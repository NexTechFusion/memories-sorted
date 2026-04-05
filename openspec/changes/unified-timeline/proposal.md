# Unified Timeline

## Intent
Replace the current tab-based navigation (Discover / Memories / Moments / People)
with a single chronological timeline where Upload, People, and Moments are
integrated layers — not separate destinations.

## Problem
The current UX fragments the photo experience:
- **Discover** shows a grid but hides people context
- **Memories** tab duplicates content from the dashboard
- **Moments** tab feels manual and disconnected
- **People** tab isolates faces from the photos they're in
- Upload is a separate action, not the starting point

Users must navigate 3-4 tabs to complete one thought: "What happened on this day, with whom?"

## Scope
### In
- Timeline view replacing Discover tab (chronological day grouping)
- Face overlay bubbles on photos (tap → name, click → filter)
- AI-suggested moments (cards between day groups)
- People/Moments as drawer access (not tabs)
- Nav bar: `+` (Upload) / 🔍 (Search) / 👤 (People drawer)

### Out (for this change)
- Virtual scrolling (defer — current 17 photos fine at 50px each)
- Upload preview screen (defer to follow-up)
- Telegram bot upload (defer)
- Long-press action sheets (defer to phase 2)

## Success Criteria
1. User opens app → sees chronological timeline, not a tab grid
2. Tapping a face bubble filters to that person's photos
3. AI suggestion card appears between day groups when ≥3 photos share context
4. All existing functionality (search, rename, delete, caption) still works

## Rollback Plan
- Current 4-tab system preserved in `app.html.bak.m4`
- Revert = `git revert` the unified-timeline commit

## Context
- Stack: FastAPI backend, Alpine.js frontend, CLIP RN50x4 vectors
- 17 photos, 10 people, 3 moments currently
- Port: 8373
- Monolithic `web/app.html` — ~1600 lines
