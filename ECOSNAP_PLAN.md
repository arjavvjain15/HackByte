# EcoSnap 🌍 — Full Build Plan
### Community Environmental Hazard Reporter · Hackathon Build Guide

> **Duration:** 36 hours · **Team:** 3 members · **Theme:** *Patch the Reality*

---

## Two User Roles

| Role | Access | Primary Action |
|---|---|---|
| **User (Citizen)** | PWA on mobile/desktop | Report hazards, upvote, view map, share complaint letters |
| **Admin (Authority)** | Web dashboard | View all reports, filter, mark as "In Review" or "Resolved", see escalations |

> There is no separate authority login for the hackathon. Admin = special flag in the users table (`is_admin: true`). One admin account is pre-seeded before the demo.

---

## Feature-by-Feature Build Plan

Each feature below maps directly to a screen in the two provided HTML files. Follow in this exact order — each feature depends on the previous.

---

### Feature 1 — Authentication (Supabase Auth)

**What it does:** Google OAuth login via Supabase. On first login, user record is created. Admin flag is set manually in the DB.

**User Dashboard screens affected:** Login gate before the main PWA loads.  
**Admin Dashboard screens affected:** Login gate before the sidebar loads.

**Step-by-step:**
1. Create a Supabase project → enable Google OAuth provider in Auth settings.
2. Create a `profiles` table:
   ```sql
   id uuid references auth.users primary key,
   display_name text,
   avatar_url text,
   is_admin boolean default false,
   reports_submitted integer default 0,
   reports_resolved integer default 0,
   created_at timestamp default now()
   ```
3. Add a Supabase trigger: on new `auth.users` insert → auto-create `profiles` row.
4. In the React PWA, wrap all routes with a `<ProtectedRoute>` that checks the Supabase session.
5. After login, fetch the user's `profiles` row. If `is_admin = true`, redirect to `/admin`. Otherwise, load the citizen PWA.
6. Seed one admin account manually: insert `is_admin = true` for your demo account.

**Done when:** Logging in with Google creates a profile. Admin account lands on admin dashboard. Regular user lands on citizen PWA.

---

### Feature 2 — Photo Capture + Upload

**What it does:** Opens the device camera (or file picker fallback), previews the photo, uploads to Supabase Storage.

**User Dashboard screens affected:** FAB button ("Report a Hazard") → full-screen camera modal.

**Step-by-step:**
1. On FAB tap, trigger `<input type="file" accept="image/*" capture="environment">` — this opens the native camera on mobile, file picker on desktop.
2. On file select, render a preview using `URL.createObjectURL(file)`.
3. Show "Confirm / Retake" buttons below the preview.
4. On confirm, upload the file to Supabase Storage bucket `hazard-photos` using `supabase.storage.from('hazard-photos').upload(...)`.
5. Get the public URL back and store it in component state — it gets passed to the AI pipeline in Feature 3.
6. Show a loading spinner labeled "Analyzing with AI…" while upload is in progress.

**Done when:** Photo taken → preview shown → confirmed → public URL available in state.

---

### Feature 3 — AI Classification Pipeline (Cloud Vision → Gemini Flash)

**What it does:** Sends the uploaded photo to Google Cloud Vision for raw label extraction, then sends those labels to Gemini 1.5 Flash to classify the hazard, determine severity, and identify the responsible department.

**User Dashboard screens affected:** The loading state → result card showing hazard type + severity badge.

**AI Pipeline Flow:**
```
Photo URL
  ↓
POST /api/classify  (FastAPI)
  ↓
Cloud Vision API → raw labels (confidence > 0.70 filter)
  ↓
Gemini 1.5 Flash → structured JSON output
  ↓
{ hazard_type, severity, department, complaint_letter }
```

**Step-by-step:**
1. Create `POST /api/classify` in FastAPI. Accepts `{ photo_url: string, lat: float, lng: float }`.
2. Call Cloud Vision `LABEL_DETECTION` on the photo URL. Filter labels with `score > 0.70`.
3. Build the Gemini prompt (see Prompt Templates section below).
4. Call Gemini 1.5 Flash API. Parse the JSON response.
5. Return the result to the frontend.
6. On the frontend, display the result: hazard type as bold heading, severity as a color-coded badge (red = high, amber = medium, green = low), department name below.

**Done when:** Submitting a photo of trash returns `{ hazard_type: "illegal_dumping", severity: "high", department: "Municipal Sanitation", complaint_letter: "..." }`.

---

### Feature 4 — GPS Tagging + Report Submission

**What it does:** Auto-attaches the device's GPS coordinates to the report. Submits the full report (photo + GPS + AI result) to the database.

**User Dashboard screens affected:** The "submitting" loading state → success screen → new pin on the map.

**Step-by-step:**
1. On camera open, trigger `navigator.geolocation.getCurrentPosition(...)` immediately so GPS is ready by the time the user confirms the photo.
2. Show a small "📍 Location attached" chip below the photo preview once GPS resolves.
3. Fallback: if GPS is denied, show a manual pin-drop UI on a mini map (tap to place location).
4. On submission, call `POST /api/reports` with: `{ user_id, photo_url, lat, lng, hazard_type, severity, department, complaint_letter }`.
5. Backend inserts the row into `reports` table and returns the new report's `id`.
6. Frontend shows a success toast: "Report submitted! Your complaint letter is ready."
7. Update the user's `reports_submitted` count in their profile.

**Done when:** Full report row exists in DB with photo URL, GPS coords, and AI classification.

---

### Feature 5 — Community Map

**What it does:** Shows all open reports as color-coded pins on a Leaflet map. Clicking a pin shows a popup with hazard details and upvote button.

**User Dashboard screens affected:** The mini map section + the full-screen map tab.  
**Admin Dashboard screens affected:** The large map panel (center of the dashboard).

**Step-by-step (User PWA):**
1. On map tab open, call `GET /api/reports` → returns all reports as `{ id, lat, lng, hazard_type, severity, upvotes, status }`.
2. Initialize Leaflet map with OpenStreetMap tiles (free, no billing).
3. For each report, add a `L.circleMarker` with color: `#E24B4A` for high, `#EF9F27` for medium, `#639922` for resolved.
4. Bind a popup to each marker showing: hazard type, upvote count, status badge, "Upvote" button.
5. Center the map on the user's GPS location. Show a green dot for "You are here."

**Step-by-step (Admin Dashboard):**
1. Same data fetch. Render pins on the admin's larger Leaflet map panel.
2. Add map view toggles: Pins / Heatmap / Clusters (use `Leaflet.heat` plugin for heatmap, `Leaflet.markercluster` for clusters — both free).
3. Map filters (area, severity) should re-request `GET /api/reports?severity=high&area=...` and re-render pins.
4. Add map legend overlay (bottom-left): red = high, amber = medium, green = resolved.

**Done when:** All seeded reports appear as colored pins. Clicking a pin shows correct info.

---

### Feature 6 — Upvoting

**What it does:** Logged-in users can upvote any report once. Upvote count is shown on map popups and report cards. When a report hits 5+ upvotes, it gets auto-tagged as "Escalated."

**User Dashboard screens affected:** Upvote button on nearby report cards + map popup.  
**Admin Dashboard screens affected:** Upvote count pill on each report card in the right panel.

**Step-by-step:**
1. Create `upvotes` table: `{ id, report_id, user_id, created_at }` with a unique constraint on `(report_id, user_id)`.
2. Create `POST /api/reports/:id/upvote`. Checks if user already voted (return 409 if so). Inserts into `upvotes`, increments `reports.upvotes` count.
3. Frontend upvote button: tapping it sends the request, then flips to a filled "voted" state (green border, green text — matches the `.voted` class in the user dashboard HTML).
4. After upvote, if `reports.upvotes >= 5`, set `reports.status = 'escalated'` in the backend.
5. In the admin dashboard, escalated reports show a red `alert` badge on the Escalations nav item.

**Done when:** Upvoting increments the count. A report with 5+ votes shows "Escalated" status.

---

### Feature 7 — Complaint Letter + Share

**What it does:** Shows the AI-generated formal complaint letter. User can copy it or share via the native share sheet (email/WhatsApp).

**User Dashboard screens affected:** "View Complaint Letter" button on the result screen → full-screen modal with the letter text, copy button, and share button.

**Step-by-step:**
1. The complaint letter is already stored in the `reports.complaint` field (generated in Feature 3).
2. On "View Complaint Letter" tap, open a bottom sheet / modal showing the letter in a scrollable text area.
3. "Copy" button: `navigator.clipboard.writeText(complaint_letter)` → show a "Copied!" toast.
4. "Share" button: call `navigator.share({ title: 'EcoSnap Report', text: complaint_letter })` for native share. Fallback: copy to clipboard.
5. Letter format (Gemini generates this):
   ```
   To: [Department Name]
   Date: [Auto-filled]
   Subject: [Hazard Type] at [Location]

   Dear Officer,

   I am writing to formally report a [hazard_type] at [lat, lng].
   This was observed on [date] and has been classified as [severity] severity.
   
   Photo evidence: [photo_url]
   GPS coordinates: [lat, lng]
   
   I request prompt action. Report ID: [id]
   
   Regards,
   [User Name]
   ```

**Done when:** Letter modal opens, copy works, share sheet triggers on mobile.

---

### Feature 8 — My Reports (User Dashboard)

**What it does:** Shows the citizen's own submitted reports with live status updates.

**User Dashboard screens affected:** "My Reports" section on the home screen — the report cards with progress bars and status badges.

**Step-by-step:**
1. On dashboard load, call `GET /api/reports?user_id=me` → returns only this user's reports.
2. Render report cards matching the HTML design: severity badge (top-left), hazard type (bold), location string, date, status badge (bottom-right).
3. Progress bar under each card: 33% for "open", 66% for "in_review", 100% for "resolved". Color fills match severity.
4. Impact strip at top (from the HTML): show `reports_submitted` and `reports_resolved` from the user's profile row.
5. Notifications section (bottom of dash): render latest status changes as notification items.

**Done when:** User's submitted reports appear with correct statuses and progress bars.

---

### Feature 9 — Admin Dashboard: Report Management

**What it does:** Admin can view all reports, filter them, select multiple, and update their status. This is the core of the "authority plays admin" loop.

**Admin Dashboard screens affected:** The entire right panel (stats cards, report list, action bar) + filter bar in the topbar.

**Step-by-step:**
1. On admin dashboard load, call `GET /api/admin/reports` (protected endpoint — checks `is_admin = true` in the session). Returns all reports sorted by newest.
2. Render 4 stat cards: Open Reports, Resolved, Escalated (5+ upvotes), Avg Resolution Time.
3. Render report list: each card shows severity badge, hazard type, location + time, upvote count pill, and a colored status dot (red = open, amber = in_review, green = resolved).
4. Clicking a report card selects it (green highlight — matches `.report-card.selected` in the admin HTML). Multiple cards can be selected.
5. "Mark In Review" button: calls `PATCH /api/admin/reports` with `{ ids: [...], status: 'in_review' }`. Updates DB and refreshes the list.
6. "Mark Resolved" button: same flow but sets `status = 'resolved'`. Also increments `reports_resolved` on the submitting user's profile.
7. Filter bar: Area, Date Range, Severity, Hazard Type dropdowns. Each change calls `GET /api/admin/reports?severity=high&...`.
8. Sort dropdown in the report list header: newest / most upvoted / highest severity.

**Done when:** Admin can filter, select, and resolve reports. Resolved reports disappear from "open" count.

---

### Feature 10 — Admin: Escalations View

**What it does:** Dedicated view for reports that have crossed the 5+ upvote threshold. These are the priority items.

**Admin Dashboard screens affected:** "Escalations" nav item in the sidebar → filtered list of escalated reports.

**Step-by-step:**
1. "Escalations" nav item shows a red alert badge with the count of escalated reports.
2. Clicking it filters the report list to `status = 'escalated'` only.
3. Escalated cards are visually distinguished (red left border or escalation tag).
4. "Assign Department" button in the action bar: opens a dropdown to manually route the report to a specific department.
5. Stretch: send an email/SMS to the department head when a report is escalated (use Resend free tier or just a Supabase Edge Function for hackathon purposes).

**Done when:** Escalated reports appear in the dedicated view. Demo can show: "5 citizens upvoted this — it's now escalated."

---

### Feature 11 — Badges + Gamification (User Dashboard)

**What it does:** Citizens earn badges for reporting activity. Shown on their dashboard to encourage engagement.

**User Dashboard screens affected:** The badge row in the user dashboard HTML.

**Step-by-step:**
1. Define 5 badges: First Report 🌱, 3 Reports 🔎, 5 Reports 🌿, First Resolved 🏆, 10 Upvotes ⭐.
2. Badges are evaluated server-side whenever a report is submitted or resolved. Logic: count reports for user, check thresholds.
3. Store earned badges in a `user_badges` table: `{ user_id, badge_id, earned_at }`.
4. On dashboard load, fetch badge state. Earned badges are green (`.badge.earned`), unearned are gray and dimmed (`.badge.locked`).

**Done when:** Submitting a first report shows the "First Report" badge as earned.

---

### Feature 12 — Nearby Reports (User Dashboard)

**What it does:** Shows hazards reported near the user's current location, with upvote capability.

**User Dashboard screens affected:** "Nearby Hazards" section — the nearby cards with distance, upvote button.

**Step-by-step:**
1. On dashboard load (after GPS resolves), call `GET /api/reports/nearby?lat=X&lng=Y&radius=2000` (2km radius).
2. Backend uses a simple Haversine distance formula in SQL or Python to filter reports within radius.
3. Render nearby cards: colored dot (severity), hazard type, location name, distance string (e.g. "0.3 km away"), upvote button.
4. Already-voted reports show the button in the voted state (`.upvote-btn.voted`).

**Done when:** Seeded reports near the demo venue appear in the "Nearby" section.

---

## AI Prompt Templates

### Prompt 1 — Gemini Hazard Classification

```
You are an environmental hazard classification AI for a civic reporting platform.

I will give you a list of object labels detected in a photo by Google Cloud Vision.

Your task:
1. Classify the hazard into exactly one of: illegal_dumping, oil_spill, e_waste, water_pollution, blocked_drain, air_pollution, other
2. Assign severity: high, medium, or low
3. Identify the responsible department: Municipal Sanitation, EPA, Public Works, Parks Department, or Drainage Authority
4. Write a formal 3-paragraph complaint letter addressed to that department

Labels detected: {labels}
Location: lat {lat}, lng {lng}
Date and time: {datetime}
Reporter name: {name}
Photo URL: {photo_url}

Respond ONLY with valid JSON. No markdown, no explanation, no preamble.

{
  "hazard_type": "...",
  "severity": "...",
  "department": "...",
  "summary": "One sentence describing the hazard",
  "complaint_letter": "Full formal letter text here"
}
```

### Prompt 2 — Fallback: Low-Confidence Labels

```
You are an environmental hazard classifier.

Google Cloud Vision could not detect clear labels in this photo (all confidence scores below 0.70).

Based only on the context — location: lat {lat}, lng {lng}, submitted via an environmental reporting app — make a best-guess classification.

Return the same JSON schema as above, but set "confidence": "low" in the response.
```

---

## Tech Stack (All Free Tiers)

| Layer | Tool | Free Tier |
|---|---|---|
| Frontend | React PWA (Vite + Tailwind) | Unlimited |
| Map | Leaflet.js + OpenStreetMap | Free forever |
| Camera | Browser File Input API | Native, no cost |
| Backend | FastAPI on Railway | 500 hrs/mo free |
| Database | Supabase Postgres | 500 MB free |
| File Storage | Supabase Storage | 1 GB free |
| Auth | Supabase Auth (Google OAuth) | 50,000 MAU free |
| AI: Vision | Google Cloud Vision | 1,000 units/mo free |
| AI: NLP | Gemini 1.5 Flash API | 15 requests/min free |
| Frontend Deploy | Vercel | Free hobby tier |
| CI/CD | GitHub Actions | 2,000 min/mo free |

---

## Database Schema

```sql
-- profiles (extends Supabase auth.users)
CREATE TABLE profiles (
  id           uuid references auth.users primary key,
  display_name text,
  avatar_url   text,
  is_admin     boolean default false,
  reports_submitted integer default 0,
  reports_resolved  integer default 0,
  created_at   timestamp default now()
);

-- reports
CREATE TABLE reports (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid references profiles(id),
  photo_url    text not null,
  lat          float not null,
  lng          float not null,
  hazard_type  text,   -- illegal_dumping | oil_spill | e_waste | water_pollution | blocked_drain | air_pollution | other
  severity     text,   -- high | medium | low
  department   text,
  summary      text,
  complaint    text,
  upvotes      integer default 0,
  status       text default 'open',  -- open | in_review | escalated | resolved
  created_at   timestamp default now(),
  resolved_at  timestamp
);

-- upvotes (prevents double-voting)
CREATE TABLE upvotes (
  id        uuid primary key default gen_random_uuid(),
  report_id uuid references reports(id) on delete cascade,
  user_id   uuid references profiles(id),
  created_at timestamp default now(),
  unique(report_id, user_id)
);

-- user_badges
CREATE TABLE user_badges (
  id        uuid primary key default gen_random_uuid(),
  user_id   uuid references profiles(id),
  badge_id  text,  -- first_report | three_reports | five_reports | first_resolved | ten_upvotes
  earned_at timestamp default now()
);
```

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/classify` | User | Cloud Vision → Gemini pipeline |
| POST | `/api/reports` | User | Submit a new report |
| GET | `/api/reports` | Public | All reports for the map |
| GET | `/api/reports/nearby` | User | Reports within 2km radius |
| GET | `/api/reports/mine` | User | Current user's reports |
| POST | `/api/reports/:id/upvote` | User | Upvote a report |
| GET | `/api/admin/reports` | Admin | All reports with filters |
| PATCH | `/api/admin/reports` | Admin | Bulk status update |
| GET | `/api/admin/stats` | Admin | Stat card numbers |

---

## 3-Member Team Roles

### Person A — Backend + AI Pipeline
**Stack:** Python, FastAPI, Supabase, Cloud Vision API, Gemini API

| Hours | Task |
|---|---|
| H0–3 | FastAPI scaffold, Supabase project, `reports` + `profiles` tables, storage bucket |
| H3–7 | `/api/classify` endpoint — Cloud Vision call, label filtering |
| H7–12 | Gemini Flash integration — prompt engineering, JSON parsing, complaint letter generation |
| H12–16 | `/api/reports`, `/api/reports/nearby`, `/api/upvote` endpoints |
| H16–20 | `/api/admin/reports` (filtered + sorted), bulk PATCH endpoint, stats endpoint |
| H20–26 | Full pipeline test with real photos, edge case handling (low confidence, GPS fail) |
| H26–36 | Frontend integration support, bug fixes, demo prep |

**Key deliverable:** The `/api/classify` endpoint must be solid before Hour 12 — everything blocks on it.

---

### Person B — Frontend (User PWA)
**Stack:** React, Vite, Tailwind, Leaflet.js, Supabase client

| Hours | Task |
|---|---|
| H0–3 | Vite PWA scaffold, Tailwind config, Supabase client setup, routing |
| H3–7 | Auth flow (Google OAuth), login screen, redirect to user/admin based on profile |
| H7–12 | Camera capture screen — file input, preview, confirm/retake |
| H12–18 | Submission flow — GPS attach, API call, loading state, result card with severity badge |
| H18–22 | User dashboard — impact strip, my reports cards, progress bars |
| H22–26 | Leaflet map — pin rendering, popups, upvote button on popup |
| H26–30 | Complaint letter modal — text display, copy button, Web Share API |
| H30–36 | Nearby hazards section, badges row, mobile polish, loading skeletons |

**Key deliverable:** Camera → submission → result card must be working by Hour 18 for the demo flow.

---

### Person C — Admin Dashboard + DevOps + Pitch
**Stack:** React (admin views), GitHub Actions, Vercel, Railway, demo seeding

| Hours | Task |
|---|---|
| H0–3 | GitHub repo, Vercel project, Railway project, env vars across all three |
| H3–6 | Admin dashboard scaffold — sidebar nav, topbar filter bar (from admin HTML) |
| H6–10 | Report cards in right panel — fetch, render, select behavior |
| H10–14 | Stats cards (open/resolved/escalated/avg time), sort dropdown |
| H14–18 | "Mark In Review" + "Mark Resolved" action buttons — bulk PATCH integration |
| H18–22 | Escalations view — filtered list, alert badge on nav, escalation tag on cards |
| H22–26 | Admin map panel — Leaflet integration matching the admin HTML design |
| H26–30 | Seed 10 real reports near venue. Pre-take photos, submit them through the live app |
| H30–34 | Pitch deck (problem → live demo → tech → impact → roadmap) + 90-sec demo script |
| H34–36 | Full rehearsal ×3, timed run, fallback offline screenshots ready |

**Key deliverable:** 10 seeded reports before the demo — the map must not be empty during the pitch.

---

## 36-Hour Schedule (All Members)

```
H00–03  Kickoff
        A: FastAPI scaffold + Supabase setup
        B: React PWA scaffold + Auth
        C: Repo + Vercel + Railway + Admin scaffold

H03–07  Core pipeline begins
        A: /classify endpoint + Cloud Vision call
        B: Camera capture UI
        C: Admin sidebar + filter bar

H07–12  AI layer
        A: Gemini integration + prompt tuning
        B: GPS attach + submission flow
        C: Admin report cards + right panel

H12–16  Data layer
        A: /reports, /upvote, /admin endpoints
        B: User dashboard (impact strip, my reports)
        C: Stats cards + action bar

H16–20  Integration sprint
        ALL: Connect frontend to backend, test on a real phone
        C: Seed 5 test reports

H20–24  Features 7–8
        A: Edge case handling, nearby endpoint
        B: Leaflet map + complaint letter modal
        C: Admin map panel + escalation view

H24–28  Polish sprint
        A: Pipeline tuning, test with real photos
        B: Nearby hazards, badges, mobile responsiveness
        C: Remaining 5 seeded reports + pitch deck draft

H28–32  Freeze + demo prep
        ALL: No new features — bugfixes only
        C: 3× full demo rehearsal, timed

H32–36  Submit
        ALL: Final phone test, screenshot set
        C: Submission form, GitHub README, live URL
```

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Cloud Vision quota hit during demo | Pre-cache 5 photo → result pairs as static JSON fallback in the API |
| Gemini returns malformed JSON | Wrap parse in try/catch, retry once with stricter prompt, fallback to a hardcoded demo result |
| GPS denied on venue WiFi | Manual pin-drop fallback on mini map |
| Empty map during pitch | Non-negotiable: 10 seeded reports before presentation. Person C owns this |
| Railway cold start delay | Ping `/health` endpoint every 5 min via a cron (UptimeRobot free tier) |
| Admin dashboard not ready in time | Person A seeds the DB directly via Supabase UI as fallback for the demo |

---

## Demo Script (90 seconds)

| Time | Action |
|---|---|
| 0:00 | Open EcoSnap on phone. Show the live map — 10 pre-seeded pins visible. "Every pin is a real hazard, reported by citizens." |
| 0:12 | Tap "Report a Hazard" FAB. Camera opens. |
| 0:18 | Take photo of a pre-set trash pile (or show a pre-taken photo). GPS chip appears. |
| 0:25 | Tap "Submit." Loading: "Analyzing with AI…" |
| 0:35 | Result appears: "Illegal Dumping · High Severity · Municipal Sanitation." |
| 0:45 | Tap "View Complaint Letter." Formal letter pre-filled with GPS and photo link. |
| 0:55 | Tap Share → native share sheet. "One tap to send this to the authority." |
| 1:05 | Switch to the admin dashboard on laptop. Show the new report in the list. Select it. Tap "Mark Resolved." |
| 1:15 | Back on phone — the report card now shows green "Resolved" status. "The loop is closed." |
| 1:22 | Point to a pin with 7 upvotes marked "Escalated." "When 5+ citizens agree, it's automatically escalated." |
| 1:30 | Closing: "EcoSnap patches reality — one photo at a time." |

---

## Environment Variables

```
# Frontend (.env)
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_URL=https://your-app.railway.app

# Backend (.env)
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
GOOGLE_CLOUD_VISION_API_KEY=
GEMINI_API_KEY=
```

> Never commit `.env` to GitHub. Set all variables in Vercel and Railway dashboards.

---

## API Keys Needed at Hour 0

- [ ] Google Cloud Vision API key — console.cloud.google.com
- [ ] Gemini 1.5 Flash API key — aistudio.google.com (free, no billing required)
- [ ] Supabase project URL + anon key — supabase.com
- [ ] Google OAuth client ID — console.cloud.google.com → APIs & Services → Credentials

---

*Built in 36 hours. Powered by Google Cloud Vision, Gemini Flash, Supabase, and a genuine frustration with unresolved civic complaints.*
