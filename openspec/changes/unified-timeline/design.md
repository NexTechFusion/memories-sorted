# Technical Design: Unified Timeline

## Architecture Overview

The change is primarily frontend-only. The existing API endpoints return all needed data:
- `/api/photos` → returns `person_ids` per photo (already available)
- `/api/people` → returns person registry with `face_bbox`
- `/api/moments` → returns existing moments
- `/api/insights` → powers the suggestion cards

**No backend API changes needed for Phase 1.**

## Data Flow

```
GET /api/photos
  ↓
Alpine app.allPhotos[] — each photo has { file_path, captured_at, person_ids, assignments }
  ↓
groupPhotosByDay() groups by YYYY-MM-DD
  ↓
Template renders day headers + photo grid with face overlay bubbles
```

## Face Rendering

Each photo's `assignments` array contains `{ person_id, face_bbox: [cx, cy, w, h] }`.
The face bounding box is normalized (0-1 coordinates relative to the image).

Rendering approach:
```html
<div class="photo-thumb relative">
  <img src="/images/filename.jpg" class="w-full h-full object-cover">
  <template x-for="a in photo.assignments" :key="a.person_id">
    <div class="face-bubble absolute rounded-full border-2"
         :style="`left:${a.face_bbox[0]*100}%;top:${a.face_bbox[1]*100}%;width:${a.face_bbox[2]*100}%;height:${a.face_bbox[3]*100}%`"
         :class="getPersonColor(a.person_id)"
         @click="filterByPerson(a.person_id)">
    </div>
  </template>
</div>
```

**Color assignment:** Each person ID gets a consistent color from a predefined palette (hsl-based, 12 colors cycling).

## Day Grouping Logic

Replace current `groupPhotosByDate()` output (Year → Month) with:

```javascript
groupPhotosByDay() {
  const days = {}
  for (const photo of this.allPhotos) {
    const cap = photo.captured_at
    if (!cap) continue
    const dayKey = cap.split('T')[0]  // "2025-03-30"
    if (!days[dayKey]) {
      const date = new Date(cap)
      days[dayKey] = { 
        key: dayKey,
        label: date.toLocaleDateString('de-DE', { day:'numeric', month:'long', year:'numeric' }),
        photos: [],
        people: new Set()
      }
    }
    days[dayKey].photos.push(photo)
    for (const pid of photo.person_ids || []) {
      days[dayKey].people.add(pid)
    }
  }
  return Object.values(days).sort((a, b) => b.key.localeCompare(a.key))
}
```

## Nav Structure

```
Before: [Discover] [Memories] [Moments] [People]
After:  [Timeline]         [Search]  [People 👤]
```

The timeline IS Discover — it just replaces the grid view. Search bar stays at top. People becomes a slide-out drawer instead of a dedicated tab.

## Suggestion Algorithm (Lightweight)

```python
def compute_suggestions(photos, moments, person_registry):
    """Group photos by day, detect clusters."""
    from collections import defaultdict
    days = defaultdict(list)
    for p in photos:
        if p.captured_at:
            day = p.captured_at.split('T')[0]
            days[day].append(p)
    
    suggestions = []
    for day_key, photos in days.items():
        if len(photos) < 3:
            continue
        # Check if these photos already belong to a moment
        day_paths = {p.file_path for p in photos}
        covered = any(day_paths.issubset(set(m.member_paths or [])) for m in moments)
        if covered:
            continue
        
        # Generate suggestion
        people = set()
        for p in photos:
            for pid in p.person_ids or []:
                people.add(pid)
        
        suggestions.append({
            'id': f'suggest-{day_key}',
            'label': f"{day_key} ({len(photos)} photos)",
            'photo_count': len(photos),
            'people_count': len(people),
            'photos': [p.file_path for p in photos[:4]]
        })
    
    return suggestions
```

This is simple day-based clustering — no CLIP similarity computation needed for Phase 1. Can be enhanced later.

## File Changes

- `web/app.html` — main rewrite (nav, template, grouping logic, face overlay)
- `api.py` — minor: add `/api/suggestions` endpoint
- `web/app.html.bak.m4` — kept as rollback reference
