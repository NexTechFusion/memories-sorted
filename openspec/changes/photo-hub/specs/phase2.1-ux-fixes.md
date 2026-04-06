# Spec: Phase 2.1 — UX Refinement & Album Fixes

## Requirements

### PH2.1.1 Longpress Selection
- Remove "Select" toggle from header.
- On photo `pointerdown`: start a timer (500ms).
- If pointer remains down: enter `selectMode` and select the photo. Trigger haptic/visual feedback.
- While in `selectMode`: single tap on any photo toggles selection (no lightbox).
- Header should change to selection UI (count + actions).

### PH2.1.2 Album Lifecycle Fixes
- Fix `POST /api/albums`: ensure it correctly saves to `albums.json`.
- Add `DELETE /api/albums/{id}` endpoint and UI button on album cards.
- Add "Add to existing Album" dropdown in selection bar.

### PH2.1.3 People View Fixes
- Ensure `UNIDENTIFIED` group is always returned by `/api/people` if unnamed persons exist.
- "Discard" in Rename Modal should close the modal and reset local state.

### PH2.1.4 Image Fallbacks
- Use standard placeholder: `https://placehold.co/400x400/18181b/ffffff?text=🖼️`.
- Fix crop paths to use verified `/cache/premium_crops/` with `.jpg` suffix.
