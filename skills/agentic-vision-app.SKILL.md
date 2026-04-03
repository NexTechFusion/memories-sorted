---
name: agentic-vision-app
category: software-development
description: Build a CPU-native, VPS-hosted agentic photo sorting and categorization web app using InsightFace, CLIP, and FastAPI.
---

# Agentic Vision App on VPS (2026 Stack)

## When to use
Use this skill when building local/VPS-hosted image analysis apps that require face recognition, semantic search, and auto-categorization without relying on cloud GPUs. Optimized for 4 vCPU / 8GB RAM limits.

## Core Stack
- **Backend:** FastAPI (monolithic: serves JSON API + HTML frontend).
- **Face Detection:** InsightFace (RetinaFace + ArcFace) running via `CPUExecutionProvider` in ONNX Runtime.
- **Semantic Search:** OpenCLIP (`RN50x4` model) for <100ms CPU text-to-image search.
- **Clustering:** HDBSCAN for "Moments" (auto-grouping photos by time + semantic similarity).
- **Storage:** `index.json` (Pydantic schema v4.0.0) + `numpy` compressed `.npz` for CLIP vectors.

## Architecture Pattern (Contract-First)

### 1. The Data Schema (Pydantic)
```python
# schemas.py
class FaceDetection(BaseModel):
    bbox: List[float]  # [x1, y1, x2, y2] for privacy blur
    face_hash: str     # Unique ID for tracking specific detections
    embedding: List[float] # 512-d ArcFace vector

class PersonID(BaseModel):
    id: str
    name: str | None
    embedding: List[float] # Running average of all matched faces
    best_face_hash: str | None
    face_count: int
```

### 2. The Sync Engine (`sync.py`)
Do not compute CLIP at query time.
- **Ingest:** Image uploaded -> Face Embedding (InsightFace) -> CLIP Embedding -> Save to DB.
- **Lookup:** New face -> Cosine Similarity vs `PersonID` embeddings -> >0.55 match? -> Add to Person.
- **Persistence:** Atomic saves (write `.tmp`, `os.replace`) to prevent index corruption.

### 3. The CLIP Engine (`clip_engine.py`)
- Uses `RN50x4` (best CPU speed/accuracy tradeoff).
- Pre-computes image vectors into `clip_vectors.npz`.
- Text encoding happens at query time (<50ms on CPU).
- Search is a simple Matrix Dot Product: `image_matrix @ text_vector`.

### 4. The Privacy Engine (`privacy_engine.py`)
- Uses the stored `bbox` from `FaceDetection` to apply `cv2.GaussianBlur` on demand.
- Returns blurred image via `FileResponse`; never modifies original files.

## Critical Pitfalls & Fixes
- **Syntax Error Dividers:** When using `write_file`, triple-backticks or dividers (`====`) at the end of the file cause silent `SyntaxError`. Always ensure the file ends with valid Python code.
- **Cold Start Timeout:** CLIP model takes 10-15s to load on CPU. **Must** initialize and warm up the engine *before* `uvicorn.run()`, or the first API call will timeout (HTTP 503).
- **FastAPI Thumbnails:** When serving face thumbnails, use `FileResponse(path, media_type="image/jpeg")`. Returning them as `JSONResponse` or plain binary causes 404s/cors errors in the browser.
- **VPS Memory:** FAISS is overkill for <10k images. Store vectors in `numpy` or `sqlite` to save RAM.

## UI/UX Standards
- **Single HTML File:** Use Tailwind via CDN for rapid iteration without Node/npm build steps.
- **Mobile-First:** Horizontal scroll carousels for faces, 2-column grid for photos, bottom-sheet modals for "Rename/Merge".
- **Glassmorphism:** `backdrop-blur` and `bg-white/80` for a clean, 2026 Apple-esque look.

## Deployment Commands
```bash
# Ensure system packages: libgl1-mesa-glx libglib2.0-0
pip install fastapi uvicorn insightface onnxruntime open-clip-torch scikit-learn pillow

# Start API (serves frontend on /)
venv/bin/python api.py
```