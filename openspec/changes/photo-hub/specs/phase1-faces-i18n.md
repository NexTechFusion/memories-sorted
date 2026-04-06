# Spec: Phase 1 — Face Naming + German Translation

## Requirements

### PH1.1 Face Naming UX
- Person card in "Unidentified" group shows "✏️ Name" button
- Tap → inline input field appears for typing name
- Submit → calls `POST /api/person/rename` with `{person_id, name}`
- Person display updates everywhere instantly (Alpine reactivity)

### PH1.2 /api/person/rename Endpoint
- Accepts `{person_id: str, name: str}`
- Updates `person_registry` in index.json
- Returns `{status: "ok", person_id, display_name}`

### PH1.3 Merge Suggestion (85% similarity)
- When a new unidentified cluster forms, compare embedding distance to existing named people
- If cosine similarity > 0.85, show "Looks like [Name]. Merge?" suggestion
- Merge moves all assignments to the target person, removes old cluster

### PH1.4 German → English Query Translation
- Install `deep-translator` (local, no API key)
- `/api/search` detects non-ASCII → auto-translates query to English before CLIP
- Original query shown in UI, translation logged for debugging
- Translation is cached (same query → same translation)