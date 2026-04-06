# Spec: Phase 0 — Restore Lost Features

## Requirements

### PH0.1 Semantic Search Bar Restored
- Search bar appears at top of homepage, above AI Insights
- On input (debounced 400ms), calls `GET /api/search?q=...`
- Results show photo grid with CLIP score badges
- Works with `escape` to clear

### PH0.2 Your People Carousel Restored
- Horizontal scroll carousel of person cards above search bar
- Shows lifted face portrait + blur background + count
- Uses existing `/crop/{path}` endpoint for face thumbnails
- Hover/focus → scale animation
- Click opens person filter on timeline

### PH0.3 Empty State Restored
- When `allPhotos.length === 0`, shows guidance: icon + "No Memories Yet" + upload CTA
- Replaces blank timeline with friendly onboarding

### PH0.4 Suggestion Threshold Lowered
- `/api/suggestions` triggers on ≥2 photos per day (was ≥3)
