# 🗺️ Memories Sorted — Product Roadmap

> Based on Roundtable Audit (UX Architect × Product CEO × Basic User)
> Status: **Critical bugs fixed** ✅ | **Now stable and rendering**

---

## 🟥 Phase 1 — Critical (Blockers)

- [x] Fix `doSaveCaption()` recursive stub — now saves to all photo lists
- [x] Fix `lbZoomStart` ternary typo — breaks on non-touch devices
- [x] Fix three-dots menu — `bMenuOpen` vs `lbMenuOpen` state mismatch
- [x] Add missing `lbEditCaption()` handler — menu button had no function
- [x] Restore rename person modal — HTML stripped during rewrite
- [x] Add moment creation modal + button
- [x] Set lightbox `lbDetail:true` — details auto-show on open
- [x] Wire up Move/Delete modals with correct state (`lbMoveShow` / `lbDeleteShow`)
- [x] Add backend API endpoints (`/api/photos/move`, `/api/photos/delete`, `/api/photos/caption`, `/api/moments/create`)

---

## 🟧 Phase 2 — UX Polish (This Week)

- [x] Replace `bg-black` with `bg-zinc-950` / `#09090b` — pure black causes OLED smear, feels cheap
- [x] Increase nav bar touch targets from ~36px to 48px minimum (bottom padding, icon size)
- [x] Fix `text-[10px]` labels — too small on mobile, bump to `text-xs`
- [x] Lightbox swipe navigation — restore `lbST`/`lbSwipe` to work alongside zoom
- [ ] Pinch-to-zoom boundary constraints — image can pan completely off-screen
- [x] Double-tap crash on desktop — `e.touches[0]` is undefined for mouse dblclick (fixed via pointer-events check)
- [x] Z-index cleanup: modals (75), lightbox (70), nav (55) — modals should be above lightbox
- [x] FAB `bottom-24` overlaps nav on small viewports
- [x] Empty Discover state — show "Upload photos to get started" instead of blank
- [ ] Search results CSS columns cause vertical gaps — use masonry or grid fallback

---

## 🟩 Phase 3 — Feature Gaps (Next 2 Weeks)

- [ ] **Empty states that inspire** — first run shows "Upload your first photos to discover your memories" with illustration
- [x] **Onboarding flow** — 3-step guided tour: what does this app do? where are my photos? privacy promise (local-first)
- [x] **Face rename quality** — replace "Person 26A74A22" with "Dom" everywhere (insights, moments, galleries)
- [x] **Moment narrative quality** — AI-generated story titles instead of raw labels ("Dom's Birthday at the Lake" vs "Family")
- [ ] **Photo upload flow** — drag-and-drop or camera capture from mobile
- [x] **Bulk operations** — select multiple photos → move, delete, add to moment
- [ ] **Share moment** — export a moment as a shareable photo strip or story
- [ ] **Search by person + caption** — "show me photos of Dom at the beach"

---

## 🟦 Phase 4 — Advanced (Month 2+)

- [ ] **Face merge** — "Person A76D3805" and "Dom" are same person → merge with confidence score
- [ ] **Location clustering** — EXIF GPS data groups photos by place, enriches moments
- [ ] **Time-based trends** — "Your most active photos day was Saturday" / "You take more photos during trips"
- [ ] **Smart captions** — auto-generate captions for all 26 photos using vision model
- [ ] **CLIP natural language search** — "photos of people in snow" → returns matching images
- [ ] **Moments timeline auto-play** — swipe through a moment like a story
- [ ] **Export / backup** — JSON export of index.json + moments.json
- [ ] **Multi-device sync** — sync index across VPS and local machines
- [ ] **Dark mode rich** — add depth, subtle gradients, glassmorphism instead of flat zinc palette

---

## 🟪 Phase 5 — Stretch (Future)

- [ ] **Video support** — extract keyframes, detect faces in video
- [ ] **Audio transcription** — voice-activated photo search ("show me the birthday photos")
- [ ] **AI photo enhancement** — upscale, denoise, colorize old photos
- [ ] **Face recognition v2** — higher accuracy with multi-model ensemble (InsightFace + ArcFace + RetinaFace)
- [ ] **Collaborative mode** — share a moment collection with family (read-only link)
- [ ] **Auto-tagging** — objects, scenes, weather, emotions from image content
- [ ] **API for external apps** — expose moments/people/photos via REST API

---

## 📊 Current Metrics

| Metric | Value |
|--------|-------|
| Photos indexed | 26 |
| Faces detected | 19 |
| Moments generated | 4 (Baby Time, Bathtub Time, Family, Glasses Time) |
| Server | FastAPI uvicorn on port 8373 |
| Face engine | InsightFace on CPU |
| Search | CLIP embeddings (26 loaded) |

---

*Last updated: 2026-04-02 | Audit: 3-agent Roundtable (UX Dev, Lead Architect, Product CEO)*
