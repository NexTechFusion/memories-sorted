# Design: Photo Hub

## Architecture

```
┌──────────────────────────────────────────┐
│  Frontend: Alpine.js (single app.html)   │
│                                          │
│  Homepage:                               │
│  ┌────────────────────────────────────┐  │
│  │ 🔍 Semantic Search (DE→EN→CLIP)    │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 👥 People Carousel (InsightFace)   │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ 📁 Albums / 📅 Timeline / 💡 Ideas │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  FastAPI Backend (api.py)                │
│                                          │
│  AI Stack:                               │
│  ├── CLIP RN50x4  → semantic embeddings  │
│  └── InsightFace  → face detection/match │
│                                          │
│  Data:                                   │
│  ├── index.json  → photo catalog         │
│  ├── albums.json → album definitions     │
│  └── insights.json → cached insights     │
│                                          │
│  Ingestion:                              │
│  ├── /api/sync     → filesystem scan     │
│  ├── Telegram bot → photo forward/ingest │
│  └── GDrive OAuth → incremental sync     │
└──────────────────────────────────────────┘
```

## Key Decisions

1. **Single monolithic app.html** — Alpine.js, no build step, no React/Vue overhead
2. **Face naming** — user-driven, no auto-merge without confirmation
3. **German translation** — `deep-translator` (local, offline-capable, no API key)
4. **Albums stored as JSON** — matches existing pattern, easy to migrate to DB later
5. **FastSAM removed** — InsightFace provides sufficient face data, FastSAM adds complexity without core value
6. **Timeline as filtered view** — homepage leads with search + clusters, timeline loads on selection

## Data Model Changes

### albums.json (new)
```json
{
  "albums": [
    {
      "id": "alb_uuid",
      "name": "Bunu 1. Geburtstag",
      "type": "manual",
      "photo_paths": ["/path/to/photo1.jpg"],
      "cover_path": "/path/to/photo1.jpg",
      "created_at": "2026-04-06T08:00:00",
      "updated_at": "2026-04-06T08:00:00"
    },
    {
      "id": "alb_uuid2",
      "name": "Baby",
      "type": "smart",
      "query": "baby",
      "created_at": "2026-04-06T08:00:00",
      "updated_at": "2026-04-06T08:00:00"
    }
  ]
}
```

### index.json additions
- `person_registry[].display` — user-assigned name (was hardcoded "Person XXX")
- `person_registry[].is_named` — boolean flag

## Migration

- Remove `lift_subject.py` from deployment
- Remove FastSAM model download from setup
- Keep `/crop/{path}` endpoint (uses Pillow, not FastSAM)