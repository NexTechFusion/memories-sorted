"""
Memories Sorted AI — Phase 1.5 Intelligence Engine API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os, json, shutil, time, uuid, asyncio, hashlib, datetime, io
from PIL import Image

# --- Core Engine Imports ---
from sync import MemoriesSync
from clip_engine import ClipSearchEngine
from insight_engine import MemoryIntelligence
from moments_engine import MomentsEngine
import caption_engine  

# --- Configuration ---
BASE_DIR = "/root/memories-sorted"
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(BASE_DIR, "index.json")
INPUT_DIR = os.path.join(BASE_DIR, "data/input")
CACHE_DIR = os.path.join(BASE_DIR, "data/cache")
FACES_DIR = os.path.join(BASE_DIR, "data/cache/faces")
PREMIUM_DIR = os.path.join(CACHE_DIR, "premium_crops")
MOMENTS_PATH = os.path.join(BASE_DIR, "moments.json")
CLIP_PATH = os.path.join(BASE_DIR, "clip_vectors.npz")
INSIGHTS_PATH = os.path.join(BASE_DIR, "insights.json")
JOBS_PATH = os.path.join(BASE_DIR, "data/jobs.json")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(PREMIUM_DIR, exist_ok=True)

app = FastAPI(title="Memories AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# === Request Models ===
class RenameRequest(BaseModel):
    person_id: str
    new_name: str

class MomentRenameRequest(BaseModel):
    moment_id: str
    new_label: str

class MomentDeleteRequest(BaseModel):
    moment_id: str

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

# === Global State ===
syncer = MemoriesSync(base_dir=BASE_DIR)
clip_engine = ClipSearchEngine(model_name="RN50x4")
insight = MemoryIntelligence()
moments_engine = MomentsEngine()

UPLOAD_JOBS = {}
UPLOAD_QUEUE = asyncio.Queue()

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

async def upload_worker():
    while True:
        job_info = await UPLOAD_QUEUE.get()
        job_id = job_info['job_id']
        file_path = job_info['file_path']
        ctx_type = job_info.get('context_type')
        ctx_id = job_info.get('context_id')
        try:
            await _bg_process_photo(file_path, job_id, ctx_type, ctx_id)
        except Exception as e:
            print(f"[Worker Error] {e}")
        finally:
            UPLOAD_QUEUE.task_done()

@app.on_event("startup")
async def startup_event():
    # Load persisted CLIP embeddings
    try:
        clip_engine.load_embeddings(CLIP_PATH)
    except Exception as e:
        print(f"[CLIP] Could not load embeddings: {e}")
    asyncio.create_task(upload_worker())

@app.on_event("shutdown")
async def shutdown_event():
    # Persist CLIP embeddings before exit
    try:
        if clip_engine._dirty:
            clip_engine.save_embeddings(CLIP_PATH)
    except Exception as e:
        print(f"[CLIP] Could not save embeddings: {e}")

@app.get("/api/crop/premium/{person_id}")
async def get_premium_crop(person_id: str):
    """Generates an aesthetic, head-and-shoulders portrait crop."""
    cache_path = os.path.join(PREMIUM_DIR, f"{person_id}.jpg")
    try:
        if os.path.exists(cache_path):
            return FileResponse(cache_path)
        
        if not os.path.exists(INDEX_PATH): raise HTTPException(status_code=404)
        with open(INDEX_PATH) as f: index_data = json.load(f)
        
        person_info = index_data.get('person_registry', {}).get(person_id)
        if not person_info: # Person not found at all
            raise HTTPException(status_code=404, detail="Person not found in registry")
        
        best_hash = person_info.get('best_face_hash')
        target_photo = None
        face_bbox_pixel_coords = None

        # Attempt 1: Use best_face_hash if available
        if best_hash:
            for item in index_data.get('image_catalog', []):
                for face in item.get('detected_faces', []):
                    if face.get('face_hash') == best_hash:
                        target_photo = item['file_path']
                        face_bbox_pixel_coords = face['bbox']
                        break
                if target_photo: break

        # Attempt 2: Fallback to any photo with the person if best_face_hash fails or is missing
        if not target_photo:
            # Get a list of all images this person is assigned to
            assigned_images = [item for item in index_data.get('image_catalog', []) 
                               if any(assign.get('person_id') == person_id 
                                      for assign in item.get('assignments', []))]
            
            if assigned_images:
                # Pick the first one with detected faces
                for item in assigned_images:
                    if item.get('detected_faces'):
                        target_photo = item['file_path']
                        # Find the first face assigned to this person in this photo
                        for face in item['detected_faces']:
                            if any(a.get('person_id') == person_id for a in item.get('assignments', []) if a.get('face_hash') == face.get('face_hash')):
                                face_bbox_pixel_coords = face['bbox']
                                break
                        if target_photo and face_bbox_pixel_coords: break # Found a photo and its face

        if not target_photo or not os.path.exists(target_photo) or not face_bbox_pixel_coords:
            raise HTTPException(status_code=404, detail="No suitable photo or face found for person")
        
        img = Image.open(target_photo).convert('RGB')
        w, h = img.size
        # Bbox in pixel coordinates (already verified in index.json)
        fx1, fy1, fx2, fy2 = face_bbox_pixel_coords
        
        f_w, f_h = abs(fx2 - fx1), abs(fy2 - fy1)
        cx, cy = min(fx1, fx2) + f_w/2, min(fy1, fy2) + f_h/2
        
        # Defensive crop calculation
        target_sz = max(f_w, f_h) * 2.2
        pw, ph = target_sz * 0.8, target_sz 
        
        left = max(0, int(cx - pw/2))
        top = max(0, int(cy - ph*0.45))
        right = min(w, int(cx + pw/2))
        bottom = min(h, int(cy + ph*0.55))
        
        # Guaranteed valid coordinates for PIL
        f_left, f_right = (left, right) if left < right else (right, left)
        f_top, f_bottom = (top, bottom) if top < bottom else (bottom, top)
        
        if f_right - f_left < 10 or f_bottom - f_top < 10:
            print(f"[Premium Crop Error] Calculated crop too small for {person_id}. Falling back to full photo.")
            return FileResponse(target_photo) # Fallback to full photo if crop is too small

        img.crop((f_left, f_top, f_right, f_bottom)).save(cache_path, "JPEG", quality=90)
        return FileResponse(cache_path)
    except Exception as e:
        print(f"[Premium Crop Error] {e}")
        raise HTTPException(status_code=500, detail="Premium crop generation failed")

_INSIGHTS_CACHE = {"data": [], "timestamp": 0}

def _refresh_insights(force=False):
    import time
    now = time.time()
    if not force and _INSIGHTS_CACHE["data"] and now - _INSIGHTS_CACHE["timestamp"] < 300:
        return _INSIGHTS_CACHE["data"]
    try:
        data = insight.generate_insights()
        with open(INSIGHTS_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        _INSIGHTS_CACHE["data"] = data
        _INSIGHTS_CACHE["timestamp"] = now
        return data
    except Exception as e:
        print(f"[ERROR] Insight generation failed: {e}")
        return _INSIGHTS_CACHE.get("data", [])

def _refresh_moments():
    catalog = [{"file_path": i.file_path, "analyzed_at": i.analyzed_at} for i in syncer.index.image_catalog]
    moments = moments_engine.compute_moments(catalog, clip_engine._image_embeddings, min_cluster_size=2)
    with open(MOMENTS_PATH, 'w') as f:
        json.dump(moments, f, indent=2)

async def _bg_process_photo(file_path: str, job_id: str, context_type: str = None, context_id: str = None):
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
        UPLOAD_JOBS[job_id]["status"] = "vectors"
        _save_jobs()
        clip_engine.ensure_embedding(file_path)
        UPLOAD_JOBS[job_id]["status"] = "done"
        syncer._save_index()
        if clip_engine._dirty:
            clip_engine.save_embeddings(CLIP_PATH)
        _refresh_insights()
        _refresh_moments()
        _save_jobs()
    except Exception as e:
        print(f"[BG Error] {e}")
        UPLOAD_JOBS[job_id]["status"] = "error"
        _save_jobs()

@app.post("/api/upload")
async def upload_photo(file: UploadFile = File(...), context_type: Optional[str] = Query(None), context_id: Optional[str] = Query(None)):
    job_id = str(uuid.uuid4())
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in ('.', '-', '_'))
    if not safe_name:
        safe_name = f"upload_{uuid.uuid4().hex[:8]}.jpg"
    file_path = os.path.abspath(os.path.join(INPUT_DIR, safe_name))
    if not file_path.startswith(os.path.abspath(INPUT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid filename")
    with open(file_path, "wb") as f: shutil.copyfileobj(file.file, f)
    UPLOAD_JOBS[job_id] = {"job_id": job_id, "file": file.filename, "status": "queued", "created_at": time.time()}
    _save_jobs()
    await UPLOAD_QUEUE.put({'job_id': job_id, 'file_path': file_path, 'context_type': context_type, 'context_id': context_id})
    return {"job_id": job_id, "file": file.filename, "status": "queued"}

@app.get("/api/upload/status/{job_id}")
async def get_upload_status(job_id: str): return UPLOAD_JOBS.get(job_id, {"status": "not_found"})

@app.get("/api/index")
async def get_index():
    if not os.path.exists(INDEX_PATH): return {}
    with open(INDEX_PATH) as f: return json.load(f)

@app.get("/api/photos")
async def get_photos():
    if not os.path.exists(INDEX_PATH): return []
    try:
        with open(INDEX_PATH) as f: 
            data = json.load(f)
            image_catalog = data.get("image_catalog", [])
    except: return []
    
    processed_photos = []
    for p in image_catalog:
        file_path = p.get("file_path", "")
        filename = os.path.basename(file_path)
        status = "done"
        for jid, job in UPLOAD_JOBS.items():
            if box := job.get("file") == filename:
                status = job.get("status", "done")
                break

        processed_photos.append({
            "file_path": file_path, 
            "analyzed_at": p.get("analyzed_at", ""),
            "captured_at": p.get("captured_at"),
            "caption": p.get("caption", ""), 
            "processing_status": status,
            "person_ids": list(set(a.get("person_id") for a in p.get("assignments", []) if a.get("person_id")))
        })
    # Sort by captured_at (EXIF), fall back to analyzed_at if no EXIF
    def sort_key(p):
        cap = p.get("captured_at") or p.get("analyzed_at", "0000-00-00")
        return cap
    processed_photos.sort(key=sort_key, reverse=True)
    return processed_photos

@app.get("/api/people")
async def get_people():
    if not os.path.exists(INDEX_PATH): return []
    with open(INDEX_PATH) as f: data = json.load(f)
    registry = data.get("person_registry", {})
    catalog = data.get("image_catalog", [])
    person_counts = {}
    for photo in catalog:
        for asgn in photo.get("assignments", []):
            pid = asgn.get("person_id")
            if pid: person_counts[pid] = person_counts.get(pid, 0) + 1
    
    people = []
    for pid, info in registry.items():
        people.append({
            "id": pid, 
            "display": info.get("name", pid), 
            "count": person_counts.get(pid, 0),
            "premium_crop": f"/api/crop/premium/{pid}"
        })
    return people

@app.get("/api/upload/active-jobs")
async def get_active_jobs():
    return {jid: job for jid, job in UPLOAD_JOBS.items() if job.get("status") not in ["done", "error"]}

@app.get("/api/search")
async def search_photos(query: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=200)):
    """Semantic search using CLIP embeddings."""
    results = clip_engine.search(query, top_k=limit)
    # Build full photo objects with captured_at
    photos = []
    if not os.path.exists(INDEX_PATH):
        return {"query": query, "results": []}
    with open(INDEX_PATH) as f:
        data = json.load(f)
    catalog = {p["file_path"]: p for p in data.get("image_catalog", [])}
    for file_path, score in results:
        entry = catalog.get(file_path, {})
        person_ids = list(set(a.get("person_id") for a in entry.get("assignments", []) if a.get("person_id")))
        photos.append({
            "file_path": file_path,
            "score": round(score, 3),
            "analyzed_at": entry.get("analyzed_at", ""),
            "captured_at": entry.get("captured_at"),
            "caption": entry.get("caption", ""),
            "person_ids": person_ids
        })
    return {"query": query, "count": len(photos), "results": photos}

@app.get("/api/folders")
async def get_folders():
    """List available folders in data/input."""
    folders = []
    input_dir = INPUT_DIR
    if os.path.exists(input_dir):
        for name in sorted(os.listdir(input_dir)):
            full_path = os.path.join(input_dir, name)
            if os.path.isdir(full_path):
                folders.append({
                    "name": name,
                    "path": full_path
                })
    return {"folders": folders}

@app.post("/api/rename")
async def rename_person(req: RenameRequest):
    """Rename a person in the person_registry."""
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=404, detail="Index not found")
    with open(INDEX_PATH) as f:
        data = json.load(f)
    registry = data.get("person_registry", {})
    if req.person_id not in registry:
        raise HTTPException(status_code=404, detail=f"Person {req.person_id} not found")
    registry[req.person_id]["name"] = req.new_name
    with open(INDEX_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    # Also purge cached premium crop so it regenerates if needed
    cache_path = os.path.join(PREMIUM_DIR, f"{req.person_id}.jpg")
    if os.path.exists(cache_path):
        os.remove(cache_path)
    _refresh_insights()
    _refresh_moments()
    return {"status": "ok", "person_id": req.person_id, "new_name": req.new_name}

@app.post("/api/person/delete")
async def delete_person(req: DeletePersonRequest):
    """Remove a person from the registry and unassign their faces."""
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=404, detail="Index not found")
    with open(INDEX_PATH) as f:
        data = json.load(f)
    registry = data.get("person_registry", {})
    if req.person_id not in registry:
        raise HTTPException(status_code=404, detail=f"Person {req.person_id} not found")
    # Remove from registry
    del registry[req.person_id]
    # Remove all assignments for this person
    for photo in data.get("image_catalog", []):
        photo["assignments"] = [a for a in photo.get("assignments", []) if a.get("person_id") != req.person_id]
    with open(INDEX_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    # Clean cached crop
    cache_path = os.path.join(PREMIUM_DIR, f"{req.person_id}.jpg")
    if os.path.exists(cache_path):
        os.remove(cache_path)
    _refresh_insights()
    _refresh_moments()
    return {"status": "ok", "person_id": req.person_id}

@app.post("/api/moment/rename")
async def rename_moment(req: MomentRenameRequest):
    """Rename a moment."""
    if not os.path.exists(MOMENTS_PATH):
        raise HTTPException(status_code=404, detail="Moments not found")
    with open(MOMENTS_PATH) as f:
        moments = json.load(f)
    found = False
    for m in moments:
        if m.get("id") == req.moment_id:
            m["label"] = req.new_label
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"Moment {req.moment_id} not found")
    with open(MOMENTS_PATH, 'w') as f:
        json.dump(moments, f, indent=2)
    return {"status": "ok", "moment_id": req.moment_id, "new_label": req.new_label}

@app.post("/api/moment/delete")
async def delete_moment(req: MomentDeleteRequest):
    """Delete a moment."""
    if not os.path.exists(MOMENTS_PATH):
        raise HTTPException(status_code=404, detail="Moments not found")
    with open(MOMENTS_PATH) as f:
        moments = json.load(f)
    moments = [m for m in moments if m.get("id") != req.moment_id]
    with open(MOMENTS_PATH, 'w') as f:
        json.dump(moments, f, indent=2)
    return {"status": "ok", "moment_id": req.moment_id}

@app.post("/api/caption")
async def caption_photo(req: PhotoCaptionRequest):
    """Add/edit a caption for a photo."""
    if not os.path.exists(INDEX_PATH):
        raise HTTPException(status_code=404, detail="Index not found")
    with open(INDEX_PATH) as f:
        data = json.load(f)
    for photo in data.get("image_catalog", []):
        if photo.get("file_path") == req.file_path:
            photo["caption"] = req.caption
            with open(INDEX_PATH, 'w') as f:
                json.dump(data, f, indent=2)
            return {"status": "ok", "file_path": req.file_path}
    raise HTTPException(status_code=404, detail="Photo not found")

@app.post("/api/photo/move")
async def move_photo(req: PhotoMoveRequest):
    """Move a photo file to another folder."""
    src = req.file_path
    target_dir = os.path.abspath(os.path.join(INPUT_DIR, req.target_folder))
    if not target_dir.startswith(os.path.abspath(INPUT_DIR)):
        raise HTTPException(status_code=400, detail="Invalid target path")
    if not os.path.exists(src):
        raise HTTPException(status_code=404, detail="Source file not found")
    os.makedirs(target_dir, exist_ok=True)
    dest = os.path.join(target_dir, os.path.basename(src))
    shutil.move(src, dest)
    # Update index
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f:
            data = json.load(f)
        for photo in data.get("image_catalog", []):
            if photo.get("file_path") == src:
                photo["file_path"] = dest
                break
        with open(INDEX_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    return {"status": "ok", "new_path": dest}

@app.post("/api/photo/delete")
async def delete_photo(req: PhotoDeleteRequest):
    """Delete a photo file and remove from index."""
    if os.path.exists(req.file_path):
        os.remove(req.file_path)
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f:
            data = json.load(f)
        data["image_catalog"] = [p for p in data.get("image_catalog", []) if p.get("file_path") != req.file_path]
        with open(INDEX_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    _refresh_insights()
    _refresh_moments()
    return {"status": "ok", "file_path": req.file_path}

@app.post("/api/moment/create")
async def create_moment(req: MomentCreateRequest):
    """Create a new moment manually."""
    if os.path.exists(MOMENTS_PATH):
        with open(MOMENTS_PATH) as f:
            moments = json.load(f)
    else:
        moments = []
    moment = {
        "id": str(uuid.uuid4()),
        "label": req.label,
        "photo_paths": req.photo_paths,
        "member_paths": req.member_paths or [],
        "created_at": datetime.datetime.now().isoformat()
    }
    moments.append(moment)
    with open(MOMENTS_PATH, 'w') as f:
        json.dump(moments, f, indent=2)
    return {"status": "ok", "moment": moment}

@app.post("/api/moment/add-photo")
async def add_photo_to_moment(req: MomentAddPhotoRequest):
    """Add a photo to an existing moment."""
    if not os.path.exists(MOMENTS_PATH):
        raise HTTPException(status_code=404, detail="Moments not found")
    with open(MOMENTS_PATH) as f:
        moments = json.load(f)
    for m in moments:
        if m.get("id") == req.moment_id:
            if req.photo_path not in m.get("photo_paths", []):
                m.setdefault("photo_paths", []).append(req.photo_path)
            with open(MOMENTS_PATH, 'w') as f:
                json.dump(moments, f, indent=2)
            return {"status": "ok", "moment_id": req.moment_id}
    raise HTTPException(status_code=404, detail=f"Moment {req.moment_id} not found")

@app.get("/api/moments")
async def get_moments():
    if os.path.exists(MOMENTS_PATH):
        with open(MOMENTS_PATH) as f: return json.load(f)
    return []

@app.get("/api/insights")
async def get_insights():
    _refresh_insights()
    if os.path.exists(INSIGHTS_PATH):
        with open(INSIGHTS_PATH) as f: return json.load(f)
    return []

@app.get("/")
async def root(): return FileResponse("web/app.html")

app.mount("/web", StaticFiles(directory="web"), name="web")
app.mount("/images", StaticFiles(directory=INPUT_DIR), name="images")
app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")

@app.get("/crop/{path:path}")
async def face_crop(path: str, crop: str = None):
    full_path = os.path.join(INPUT_DIR, path)
    if not os.path.exists(full_path): raise HTTPException(status_code=404)
    if not crop: return FileResponse(full_path)
    try:
        cx, cy, fw, fh = [float(x) for x in crop.split(',')]
        img = Image.open(full_path).convert('RGB')
        w, h = img.size
        cp_x, cp_y = cx * w / 100, cy * h / 100
        sz = max(fw, fh) * 1.5
        left, top = max(0, cp_x - sz/2), max(0, cp_y - sz/2)
        right, bottom = min(w, cp_x + sz/2), min(h, cp_y + sz/2)
        buf = io.BytesIO()
        img.crop((left, top, right, bottom)).save(buf, format="JPEG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/jpeg")
    except: return FileResponse(full_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8373)
