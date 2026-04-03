"""
Memories Sorted AI — Phase 1.5 Intelligence Engine API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os, json, shutil, time, uuid, asyncio, hashlib

# --- Core Engine Imports ---
from sync import MemoriesSync
from clip_engine import ClipSearchEngine
from quality_engine import QualityScorer
from insight_engine import MemoryIntelligence
from moments_engine import MomentsEngine
import caption_engine  

# --- Configuration ---
BASE_DIR = "/root/memories-sorted"
INDEX_PATH = os.path.join(BASE_DIR, "index.json")
INPUT_DIR = os.path.join(BASE_DIR, "data/input")
CACHE_DIR = os.path.join(BASE_DIR, "data/cache")
FACES_DIR = os.path.join(BASE_DIR, "data/cache/faces")
MOMENTS_PATH = os.path.join(BASE_DIR, "moments.json")
CLIP_PATH = os.path.join(BASE_DIR, "clip_vectors.npz")
INSIGHTS_PATH = os.path.join(BASE_DIR, "insights.json")
JOBS_PATH = os.path.join(BASE_DIR, "data/jobs.json")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)

app = FastAPI(title="Memories AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# === Global State ===
syncer = MemoriesSync(base_dir=BASE_DIR)
clip_engine = ClipSearchEngine(model_name="RN50x4")
quality = QualityScorer()
insight = MemoryIntelligence()
moments_engine = MomentsEngine()

UPLOAD_JOBS = {}
PROCESS_LOCK = False

def _load_jobs():
    global UPLOAD_JOBS
    if os.path.exists(JOBS_PATH):
        try:
            with open(JOBS_PATH) as f: UPLOAD_JOBS = json.load(f)
        except: UPLOAD_JOBS = {}

def _save_jobs():
    os.makedirs(os.path.dirname(JOBS_PATH), exist_ok=True)
    with open(JOBS_PATH, 'w') as f: json.dump(UPLOAD_JOBS, f)

_load_jobs()

def _refresh_insights():
    data = insight.generate_insights()
    with open(INSIGHTS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def _refresh_moments():
    catalog = [{"file_path": i.file_path, "analyzed_at": i.analyzed_at} for i in syncer.index.image_catalog]
    moments = moments_engine.compute_moments(catalog, clip_engine._image_embeddings, min_cluster_size=2)
    with open(MOMENTS_PATH, 'w') as f:
        json.dump(moments, f, indent=2)

async def _bg_process_photo(file_path: str, job_id: str, context_type: str = None, context_id: str = None):
    global PROCESS_LOCK
    while PROCESS_LOCK: await asyncio.sleep(0.5)
    PROCESS_LOCK = True
    try:
        UPLOAD_JOBS[job_id]["status"] = "syncing"
        _save_jobs()
        syncer.sync()
        
        new_entry = next((i for i in syncer.index.image_catalog if i.file_path == file_path), None)
        if not new_entry:
            UPLOAD_JOBS[job_id]["status"] = "error"
            _save_jobs()
            return

        UPLOAD_JOBS[job_id]["status"] = "faces"
        _save_jobs()
        new_entry.quality_score = quality.score(file_path)
        
        found_names = []
        for asgn in new_entry.assignments:
            pid = asgn.get("person_id")
            if pid and pid in syncer.index.person_registry:
                name = syncer.index.person_registry[pid].get("name")
                if name and not name.startswith("PERSON_"): found_names.append(name)
        UPLOAD_JOBS[job_id]["found_people"] = list(set(found_names))

        if context_type == 'moment' and context_id and os.path.exists(MOMENTS_PATH):
            with open(MOMENTS_PATH) as f: moments = json.load(f)
            for m in moments:
                if m["id"] == context_id and file_path not in m.get("member_paths", []):
                    m.setdefault("member_paths", []).append(file_path)
                    m["count"] = len(m["member_paths"])
            with open(MOMENTS_PATH, 'w') as f: json.dump(moments, f, indent=2)

        UPLOAD_JOBS[job_id]["status"] = "vectors"
        _save_jobs()
        try:
            clip_engine.ensure_embedding(file_path)
            if clip_engine._dirty: clip_engine.save_embeddings(CLIP_PATH)
        except: pass

        UPLOAD_JOBS[job_id]["status"] = "done"
        syncer._save_index()
        _refresh_insights()
        _save_jobs()
    except Exception as e:
        print(f"[BG Error] {e}")
        UPLOAD_JOBS[job_id]["status"] = "error"
        _save_jobs()
    finally:
        PROCESS_LOCK = False

# === Request Models ===
class RenameRequest(BaseModel):
    person_id: str
    new_name: str

class MomentRenameRequest(BaseModel):
    moment_id: str
    new_label: str

class DeletePersonRequest(BaseModel):
    person_id: str

class PhotoCaptionRequest(BaseModel):
    file_path: str
    caption: str

class PhotoMoveRequest(BaseModel):
    file_path: str
    target_folder: str

class PhotoDeleteRequest(BaseModel):
    file_path: str

class MomentCreateRequest(BaseModel):
    label: str
    photo_paths: List[str]
    member_paths: Optional[List[str]] = None

class MomentAddPhotoRequest(BaseModel):
    moment_id: str
    photo_path: str

# === Routes ===

@app.get("/api/index")
async def get_index():
    if not os.path.exists(INDEX_PATH): return {}
    with open(INDEX_PATH) as f: data = json.load(f)
    for img in data.get("image_catalog", []):
        img["person_ids"] = list(set(a.get("person_id") for a in img.get("assignments", []) if a.get("person_id")))
    return data

@app.get("/api/photos")
async def get_photos():
    if not os.path.exists(INDEX_PATH): return []
    with open(INDEX_PATH) as f: data = json.load(f)
    # Add processing status to photos from UPLOAD_JOBS
    processed_photos = []
    for p in data.get("image_catalog", []):
        job_id = None
        for jid, job_info in UPLOAD_JOBS.items():
            if job_info.get("file") == os.path.basename(p.get("file_path", "")):
                job_id = jid
                break
        processed_photos.append({"file_path": p.get("file_path", ""), "caption": p.get("caption", ""), 
                                 "ai_desc": p.get("ai_desc", ""), "assignments": p.get("assignments", []),
                                 "processing_status": UPLOAD_JOBS.get(job_id, {}).get("status", "done"), # Default to 'done' if no job found
                                 "person_ids": list(set(a.get("person_id") for a in p.get("assignments", []) if a.get("person_id")))}
        )
    return processed_photos

@app.get("/api/people")
async def get_people():
    if not os.path.exists(INDEX_PATH): return []
    with open(INDEX_PATH) as f: data = json.load(f)
    registry = data.get("person_registry", {})
    photos = data.get("image_catalog", [])
    person_counts = {}
    for photo in photos:
        for asgn in photo.get("assignments", []):
            pid = asgn.get("person_id")
            if pid: person_counts[pid] = person_counts.get(pid, 0) + 1
    
    # Build a lookup: face_hash -> bbox for each photo's detected_faces
    face_bbox_lookup = {}
    for photo in photos:
        for face in photo.get("detected_faces", []):
            face_bbox_lookup[face.get("face_hash")] = face.get("bbox")
        # Also index by photo file_path for assignments
        for assignment in photo.get("assignments", []):
            fh = assignment.get("face_hash")
            if fh and fh in face_bbox_lookup:
                assignment["_bbox"] = face_bbox_lookup[fh]

    people = []
    for pid, info in registry.items():
        best_hash = info.get("best_face_hash")
        avatar = info.get("avatar")
        face_bbox = None

        # Try to find avatar + bbox from best_face_hash first
        if best_hash and best_hash in face_bbox_lookup:
            face_bbox = face_bbox_lookup[best_hash]
            # Find a photo that has this face
            for photo in photos:
                for face in photo.get("detected_faces", []):
                    if face.get("face_hash") == best_hash:
                        avatar = photo.get("file_path")
                        break
                if avatar:
                    break

        # Fallback: find any photo belonging to this person
        if not avatar:
            for photo in photos:
                for assignment in photo.get("assignments", []):
                    if assignment.get("person_id") == pid:
                        avatar = photo.get("file_path")
                        face_bbox = assignment.get("_bbox")
                        break
                if avatar:
                    break

        # Normalize bbox to CSS object-position percentages using image resolution
        normalized_bbox = None
        if face_bbox and len(face_bbox) == 4:
            x1, y1, x2, y2 = face_bbox
            # Use image resolution for proper normalization
            res = photo.get("resolution")
            if res and len(res) == 2:
                img_w, img_h = float(res[0]), float(res[1])
            else:
                # Fallback to using bbox for resolution if not present, but ensure it's not zero
                img_w, img_h = float(x2 - x1), float(y2 - y1)
                if img_w == 0 or img_h == 0: # Avoid division by zero if bbox somehow collapsed
                    img_w, img_h = 100, 100 

            w_face = x2 - x1
            h_face = y2 - y1
            if img_w > 0 and img_h > 0 and w_face > 0 and h_face > 0:
                cx = (x1 + w_face / 2) / img_w * 100
                cy = (y1 + h_face / 2) / img_h * 100
                normalized_bbox = [cx, cy, w_face, h_face, x1, y1, x2, y2]

        people.append({"id": pid, "display": info.get("name", "Person"), "name": info.get("name", "Person"), "count": person_counts.get(pid, 0), "avatar": avatar, "face_bbox": normalized_bbox})
    return people

@app.get("/api/moments")
async def get_moments():
    if os.path.exists(MOMENTS_PATH):
        with open(MOMENTS_PATH) as f: return json.load(f)
    return []

@app.post("/api/moments/rename")
async def rename_moment(req: MomentRenameRequest):
    if not os.path.exists(MOMENTS_PATH): raise HTTPException(status_code=404, detail="No moments")
    with open(MOMENTS_PATH) as f: moments = json.load(f)
    for m in moments:
        if m.get('id') == req.moment_id: m['label'] = req.new_label; break
    with open(MOMENTS_PATH, 'w') as f: json.dump(moments, f, indent=2)
    return {"status": "ok"}

@app.post("/api/moments/delete")
async def delete_moment(req: MomentRenameRequest):
    if not os.path.exists(MOMENTS_PATH): raise HTTPException(status_code=404, detail="No moments")
    with open(MOMENTS_PATH) as f: moments = json.load(f)
    moments = [m for m in moments if m.get('id') != req.moment_id]
    with open(MOMENTS_PATH, 'w') as f: json.dump(moments, f, indent=2)
    return {"status": "ok"}

@app.post("/api/moments/regenerate")
async def regenerate_moments():
    _refresh_moments()
    return {"status": "ok"}

@app.post("/api/people/delete")
async def delete_person(req: DeletePersonRequest):
    with open(INDEX_PATH) as f: idx = json.load(f)
    if req.person_id in idx.get("person_registry", {}): del idx["person_registry"][req.person_id]
    for img in idx.get("image_catalog", []):
        img["assignments"] = [a for a in img.get("assignments", []) if a.get("person_id") != req.person_id]
        img["caption"] = img.get("caption", "")
    with open(INDEX_PATH, 'w') as f: json.dump(idx, f, indent=2)
    return {"status": "ok"}

@app.post("/api/photos/caption")
async def update_caption(req: PhotoCaptionRequest):
    with open(INDEX_PATH) as f: idx = json.load(f)
    for img in idx.get("image_catalog", []):
        if img["file_path"] == req.file_path: img["caption"] = req.caption; break
    with open(INDEX_PATH, 'w') as f: json.dump(idx, f, indent=2)
    return {"status": "ok"}

@app.post("/api/photos/move")
async def move_photo(req: PhotoMoveRequest):
    dest = os.path.join(BASE_DIR, req.target_folder, os.path.basename(req.file_path))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(req.file_path): shutil.move(req.file_path, dest)
    with open(INDEX_PATH) as f: idx = json.load(f)
    for img in idx.get("image_catalog", []):
        if img["file_path"] == req.file_path: img["file_path"] = dest; break
    with open(INDEX_PATH, 'w') as f: json.dump(idx, f, indent=2)
    return {"status": "ok"}

@app.post("/api/photos/delete")
async def delete_photo(req: PhotoDeleteRequest):
    if os.path.exists(req.file_path): os.remove(req.file_path)
    with open(INDEX_PATH) as f: idx = json.load(f)
    idx["image_catalog"] = [img for img in idx["image_catalog"] if img["file_path"] != req.file_path]
    with open(INDEX_PATH, 'w') as f: json.dump(idx, f, indent=2)
    return {"status": "ok"}


@app.post("/api/moments/create")
async def create_moment(req: MomentCreateRequest):
    if os.path.exists(MOMENTS_PATH):
        with open(MOMENTS_PATH) as f: moments = json.load(f)
    else: moments = []
    moment_id = f"MOMENT_{len(moments):03d}"
    from datetime import datetime
    now = datetime.now()
    moments.append({"id": moment_id, "label": req.label, "cover_image": req.photo_paths[0] if req.photo_paths else "", "member_paths": req.photo_paths or req.member_paths or [], "count": len(req.photo_paths or req.member_paths or []), "created_at": now.isoformat(), "timestamp": int(now.timestamp())})
    with open(MOMENTS_PATH, 'w') as f: json.dump(moments, f, indent=2)
    return {"status": "ok", "moment_id": moment_id}

@app.post("/api/moments/add-photo")
async def add_photo_to_moment(req: MomentAddPhotoRequest):
    if not os.path.exists(MOMENTS_PATH): raise HTTPException(status_code=404, detail="No moments")
    with open(MOMENTS_PATH) as f: moments = json.load(f)
    for m in moments:
        if m["id"] == req.moment_id:
            if req.photo_path not in m.get("member_paths", []):
                m.setdefault("member_paths", []).append(req.photo_path)
                m["count"] = len(m["member_paths"])
                if not m.get("cover_image"): m["cover_image"] = req.photo_path
            break
    else: raise HTTPException(status_code=404, detail="Moment not found")
    with open(MOMENTS_PATH, 'w') as f: json.dump(moments, f, indent=2)
    return {"status": "ok"}

@app.get("/api/insights")
async def get_insights():
    _refresh_insights()
    if os.path.exists(INSIGHTS_PATH):
        with open(INSIGHTS_PATH) as f: return json.load(f)
    return []

@app.get("/api/face-thumb/{face_hash}")
async def get_face_thumb(face_hash: str):
    path = os.path.join(FACES_DIR, f"{face_hash}.jpg")
    if os.path.exists(path): return FileResponse(path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Not found")

# === HTML UI ===
@app.get("/")
async def root(): return FileResponse("web/app.html")

@app.get("/favicon.ico")
async def favicon(): raise HTTPException(status_code=404)

# Serve static assets
app.mount("/web", StaticFiles(directory="web"), name="web")
app.mount("/images", StaticFiles(directory=INPUT_DIR), name="images")
app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")

# === Server-side face crop endpoint ===
@app.get("/crop/{path:path}")
async def face_crop(path: str, crop: str = None):
    from PIL import Image
    full_path = os.path.join(INPUT_DIR, path)
    if not os.path.exists(full_path): raise HTTPException(status_code=404, detail="Image not found")
    if not crop: return FileResponse(full_path)
    try: cx, cy, fw, fh = [float(x) for x in crop.split(',')]
    except: return FileResponse(full_path)

    img = Image.open(full_path).convert('RGB')
    orig_w, orig_h = img.size
    cx_px = cx / 100.0 * orig_w
    cy_px = cy / 100.0 * orig_h
    fw_px = max(fw, 20.0)
    fh_px = max(fh, 20.0)
    out_size = 600
    target_face_px = out_size * 0.65
    scale_w = out_size / fw_px * target_face_px / out_size
    scale_h = out_size / fh_px * target_face_px / out_size
    scale = min(scale_w, scale_h, 5.0)

    crop_w = orig_w / scale
    crop_h = orig_h / scale
    x1 = max(0, int(cx_px - crop_w / 2))
    y1 = max(0, int(cy_px - crop_h / 2))
    x2 = min(orig_w, int(cx_px + crop_w / 2))
    y2 = min(orig_h, int(cy_px + crop_h / 2))

    if x2 - x1 >= orig_w or y2 - y1 >= orig_h: return FileResponse(full_path)

    cropped = img.crop((x1, y1, x2, y2))
    resized = cropped.resize((out_size, out_size), Image.LANCZOS)

    cache_key = hashlib.md5(f"{path}_{crop}".encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, cache_key + '.jpg')
    resized.save(cache_path, 'JPEG', quality=85)

    return FileResponse(cache_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8373)
