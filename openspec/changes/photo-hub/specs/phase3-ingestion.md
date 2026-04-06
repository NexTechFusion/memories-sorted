# Spec: Phase 3 — Ingestion Pipeline

## Requirements

### PH3.1 GDrive Sync
- OAuth2 flow for Google Drive access
- Watch API for incremental changes (webhooks)
- Initial full scan + periodic delta sync
- Downloads new/modified photos to `data/input/`
- Triggers existing CLIP + InsightFace pipeline
- Stores sync state (`last_sync_token`, `last_sync_time`)

### PH3.2 Telegram Bot Upload
- Bot receives forwarded photos or direct sends
- Downloads media, saves to `data/input/`
- Triggers `sync.py` processing pipeline
- Replies with: "✅ Added 3 photos" + detected people
- Bot token configurable via env var

### PH3.3 Batch Upload Queue
- `POST /api/upload/batch` accepts multiple files
- Files saved to queue, processed asynchronously
- Status endpoint: `GET /api/upload/status/<job_id>`
- Progress: `{processed: N, total: M, status: "running"|"done"|"error"}`

### PH3.4 Deduplication
- SHA-256 hash exact duplicate detection
- Perceptual hash (pHash) for near-duplicates (resized, edited versions)
- On upload, checks against existing catalog
- Exact dupes: skip silently
- Near-dupes: flag for user review (optional merge)

### PH3.5 Background Queue
- Simple file-based queue: `queue/pending/`, `queue/processing/`, `queue/done/`
- Worker process picks up files, runs sync pipeline
- Status exposed via `GET /api/queue/status`
- No Redis/complex setup — file system is the queue
