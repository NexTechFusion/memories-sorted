# Tasks: Unified Timeline

## Phase 1: Backbone (Timeline + Nav)

- [x] 1.1 Create OpenSpec change directory + proposal.md
- [x] 1.2 Create specs/timeline-navigation.md  
- [x] 1.3 Create design.md
- [x] 1.4 Remove Memories tab from app.html (clean up purge)
- [x] 1.5 Replace Discover grid → chronological day grouping
- [x] 1.6 Update nav bar: 3 items (Timeline, Add, People drawer)
- [x] 1.7 Remove Moments tab

## Phase 2: Face Overlays

- [x] 2.1 Render face bubbles on each photo thumbnail
- [x] 2.2 Person color assignment (consistent palette)
- [x] 2.3 Tap bubble → filter timeline to that person
- [x] 2.4 "Clear filter" button when filtered

## Phase 3: Suggested Moments

- [x] 3.1 Add /api/suggestions endpoint (day-based clustering)
- [x] 3.2 Render suggestion cards between day groups
- [x] 3.3 "Create" confirms → adds to moments
- [x] 3.4 "Dismiss" hides suggestion (localStorage)

## Phase 4: People Drawer

- [x] 4.1 Replace People tab with slide-out drawer
- [x] 4.2 Drawer shows: named people + Unidentified group
- [x] 4.3 Tap person → filter timeline + close drawer
- [x] 4.4 Drawer dismisses on backdrop tap

---

## Testing

- [x] T1. Timeline loads correctly on fresh page load ✅
- [x] T2. Day groups sort newest-first (Apr 2 → Jun 14, 2024) ✅
- [x] T3. Face bubbles render at correct positions ✅
- [x] T4. Filter by person works and is reversible (Paul tested) ✅
- [x] T5. Suggestion cards appear for days with ≥3 photos ✅ (data threshold)
- [x] T6. All existing features (search, delete, caption, lightbox) still work ✅

---

## Status: ✅ COMPLETE — 2026-04-05
