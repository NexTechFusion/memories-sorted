# Timeline Navigation

## ADDED Requirements

### REQ-1: Chronological Day Grouping
**The system shall group photos by exact date (YYYY-MM-DD) instead of year/month.**

**Given** photos exist with `captured_at` dates  
**When** the user views the timeline  
**Then** photos are grouped under date headers like "March 30, 2025"  
**And** date groups are sorted newest-first

### REQ-2: Day Group Metadata
**Each day group header shall display contextual metadata.**

**Given** a day group with photos  
**When** the group renders  
**Then** it shows: photo count, detected people names (up to 3), and location if available  
**Example:** "March 30, 2025 — 3 photos · Paul, Liam"

### REQ-3: Single Surface Navigation
**The timeline replaces the Discover tab as the primary view.**

**Given** the app loads  
**When** no tab is specified  
**Then** the timeline is shown by default  
**And** the nav bar shows: `+` (Upload) / 🔍 (Search) / 👤 (People)  
**And** the Memories and Moments tabs are removed

### REQ-4: People as Overlay Bubbles
**Face bubbles are rendered on each photo in the timeline.**

**Given** a photo has person assignments with `face_bbox` data  
**When** the photo thumbnail renders  
**Then** colored circles are overlaid at the bounding box positions  
**And** each bubble is labeled with the person's display name  
**And** tapping a bubble filters the timeline to show only that person's photos  
**And** an "Unidentified" bubble shows for unmatched faces

### REQ-5: AI-Suggested Moments
**The system suggests moments based on photo clustering.**

**Given** ≥3 photos share the same day, similar CLIP vectors, or overlapping people  
**When** the timeline renders  
**Then** a suggestion card appears between the relevant day groups  
**And** the card shows: suggested name, photo count, preview thumbnails  
**And** the user can tap "Create" to confirm or "Dismiss" to hide  
**And** dismissed suggestions are stored and not re-shown

### REQ-6: People Drawer
**The People tab becomes a drawer/side panel.**

**Given** the user taps the 👤 icon  
**When** the drawer opens  
**Then** it shows: named people sorted by photo count, then "Unidentified" group  
**And** tapping a person filters the timeline to their photos  
**And** the drawer dismisses on backdrop tap or swipe

### REQ-7: Backwards Compatibility
**All existing functionality remains operational.**

**Given** the unified timeline is active  
**When** the user performs any existing action  
**Then** search, rename, delete, caption, lightbox, and moments all work as before
