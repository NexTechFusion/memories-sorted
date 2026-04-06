# Tasks: Photo Hub — Phases 0–3

## Phase 0 — Restore Lost Features

- [x] 0.1 Remove FastSAM (`lift_subject.py` + FastSAM references)
- [x] 0.2 Restore semantic search bar to homepage (above insights)
- [x] 0.3 Restore "Your People" carousel (InsightFace face crops, no FastSAM)
- [x] 0.4 Restore empty state ("No Memories Yet" + upload CTA)
- [x] 0.5 Lower suggestion threshold from ≥3 to ≥2 photos/day

## Phase 1 — Face Naming + German Translation

- [x] 1.1 `POST /api/person/rename` endpoint
- [x] 1.2 Face naming UI in Unidentified drawer (inline input)
- [x] 1.3 Install `deep-translator`, wire DE→EN translation in `/api/search`
- [ ] 1.4 Merge suggestion on 85% face similarity

## Phase 2 — Albums & Curation

- [x] 2.1 Multi-select UI on timeline photos
- [x] 2.2 `albums.json` schema + `/api/albums` CRUD endpoints
- [x] 2.3 Album tab in nav + album grid/browse UI
- [x] 2.4 Smart albums (save search as dynamic)
- [ ] 2.5 Album export → ZIP download

## Phase 2.1 — UX Refinement & Album Fixes (CURRENT)

- [ ] 2.1.1 Implement Longpress Selection (Remove Select/Add buttons)
- [ ] 2.1.2 Fix Album Creation & Persistence
- [ ] 2.1.3 Add Album Delete & Photo Add endpoints/UI
- [ ] 2.1.4 Fix Unidentified People View logic
- [ ] 2.1.5 Add Image Fallbacks for Albums and Empty States
- [ ] 2.1.6 Fix Rename Modal "Discard" button

## Phase 2.2 — Final UX Polish & File Ops (CURRENT)

- [ ] 2.2.1 Multi-file Upload (with optional Album target)
- [ ] 2.2.2 Lightbox Swiping & Navigation (Backdrop close, X button)
- [ ] 2.2.3 Registered Face Deletion/Removal UI
- [ ] 2.2.4 Fix Lightbox missing components

## Phase 3 — Ingestion Pipeline

- [ ] 3.1 GDrive OAuth + incremental sync
- [ ] 3.2 Telegram bot upload
- [ ] 3.3 Batch upload with progress queue
- [ ] 3.4 Deduplication (hash + perceptual similarity)
- [ ] 3.5 Background processing queue
