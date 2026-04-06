# Proposal: Photo Hub — Phases 0–3

## Why

The current Unified Timeline works but sacrificed key features during redesign. For a photo aggregation hub (10K photos, single user → multi-tenant later), the entry point must be **search + clustering**, not a scrollable day list.

**Three critical gaps:**
1. 15 photos stuck in "Unidentified" with no way to name them
2. Semantic search (the demo killer) is completely missing from the UI
3. No albums, no smart albums, no export — users can't curate

## What Changes

Transform Memories Sorted from a passive viewer into an active photo aggregation hub:

- **Phase 0 (Fix)**: Restore search bar, People carousel, empty state
- **Phase 1 (Faces + i18n)**: Name faces, German→English translation on search
- **Phase 2 (Albums)**: Manual + smart albums, export
- **Phase 3 (Ingest)**: GDrive sync, Telegram bot upload, dedup, queue

## Decisions Retired

- FastSAM removed — InsightFace only for face detection
- Timeline is secondary view, not homepage
- CLIP + InsightFace remain the core AI stack