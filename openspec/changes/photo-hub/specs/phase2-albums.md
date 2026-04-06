# Spec: Phase 2 — Albums & Curation

## Requirements

### PH2.1 Multi-Select UI
- "Select" button on timeline enables selection mode
- Tap photos to toggle selection
- Selected items: blue border, count badge in header
- "Create Album" / "Cancel" / "Select All" actions

### PH2.2 Album Data Model
- `albums.json` stored in data directory
- Schema:
  - `albums[].id` (uuid)
  - `albums[].name` (string)
  - `albums[].type` ("manual" | "smart")
  - `albums[].photo_paths` (string[]) — for manual
  - `albums[].query` (string) — for smart
  - `albums[].created_at` (ISO timestamp)
  - `albums[].updated_at` (ISO timestamp)

### PH2.3 Album CRUD Endpoints
- `GET /api/albums` → list all
- `POST /api/albums` → create (name + photo_paths)
- `POST /api/albums/<id>/add` → add photos
- `POST /api/albums/<id>/remove` → remove photos
- `DELETE /api/albums/<id>` → delete album
- `GET /api/albums/<id>/photos` → get album photos

### PH2.4 Smart Albums
- Create from search: "Save as Smart Album" button on search results
- Stores the query string, refreshes photo list on each load
- Updates with new uploads automatically

### PH2.5 Album Browse
- New "📁" tab in nav (Timeline / Albums / Add / Who)
- Album grid shows name, type badge, photo count, cover thumb
- Tap album → opens album view with photo grid
- Album view has "Exit Album" back button

### PH2.6 Album Export
- Album → "Export" button
- Downloads ZIP of all photos in album
- Smart albums: export current results as snapshot