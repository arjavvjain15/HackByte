# EcoSnap 🌍
### Community Environmental Hazard Reporter

> **Hackathon:** 36 hours · Team of 3 · Theme: *Patch the Reality*

---

## Problem Statement

Citizens encounter environmental hazards every day — illegal dumping, e-waste piles, oil spills, clogged drains leaking waste — and have no simple way to report them. Existing government portals are bureaucratic, slow, and rarely mobile-friendly. Hazards go unreported because the friction of reporting is too high.

**EcoSnap eliminates that friction.** Take a photo, let AI identify the hazard, and submit a formal report to the right authority in under 30 seconds. Every report is pinned on a community map so neighbors can upvote the same issue — turning isolated sightings into undeniable evidence for municipal action.

---

## Who It's For

| User | Pain Point |
|---|---|
| Concerned citizen | Sees a hazard, doesn't know who to call or how to report it |
| Municipal officer | Receives vague, unstructured complaints with no photo evidence |
| Community volunteer | Has no visibility into where problems are clustered |

---

## Value Proposition

- **For reporters:** One tap to photograph, classify, and submit a structured complaint with GPS + photo attached
- **For authorities:** Structured, categorized reports with severity scores — not freeform emails
- **For the community:** A live map showing open hazards, upvote counts, and resolution status

---

## Tech Stack

### Frontend
| Tool | Role | Why |
|---|---|---|
| React PWA | Web + mobile UI | No app store install — works on any phone browser |
| Leaflet.js | Interactive hazard map | Free, open source, no billing surprises |
| Camera API (browser) | Photo capture | Native browser, no React Native complexity |
| Web Share API | Share report / complaint letter | Native mobile share sheet, zero cost |

### Backend
| Tool | Role | Why |
|---|---|---|
| FastAPI (Python) | REST API server | Lightweight, fast to scaffold, easy file uploads |
| Supabase | Database + storage | Free tier, built-in Postgres + file bucket for photos |
| Supabase Auth | User sessions | Free, handles Google OAuth out of the box |

### AI Pipeline
| Tool | Role | Why |
|---|---|---|
| Google Cloud Vision API | Raw label extraction from photo | Free tier (1000 units/mo), high accuracy, single REST call |
| Gemini 1.5 Flash API | Hazard classification + complaint letter generation | Free tier, fast, handles semantic reasoning over Vision labels |

### AI Pipeline Flow
```
Photo upload
    │
    ▼
Google Cloud Vision API
→ returns raw labels: ["plastic bottle", "waste", "tire", "grass", 0.91 confidence]
    │
    ▼
Filter labels (confidence > 0.70)
    │
    ▼
Gemini 1.5 Flash
→ prompt: classify hazard type, severity, responsible dept, generate complaint letter
→ returns: { hazard: "illegal dumping", severity: "high", dept: "Municipal Sanitation", letter: "..." }
    │
    ▼
Save to Supabase (report + photo URL + GPS + classification)
Pin on Leaflet map
```

### DevOps
| Tool | Role |
|---|---|
| Vercel | Frontend deploy (free tier) |
| Railway | FastAPI backend deploy (free tier) |
| GitHub Actions | Auto-deploy on push to main |

---

## Core Features (MVP — must ship)

- [ ] **Photo capture** — camera opens in PWA, photo uploaded to Supabase storage
- [ ] **AI classification** — Cloud Vision → Gemini pipeline returns hazard type + severity
- [ ] **GPS tagging** — browser Geolocation API auto-attaches coordinates
- [ ] **Community map** — Leaflet map showing all reports as color-coded pins (red = high, amber = medium, green = resolved)
- [ ] **Upvote** — logged-in users can upvote existing reports; count shown on pin popup
- [ ] **Complaint letter generator** — Gemini auto-drafts a formal letter to the responsible department, pre-filled with photo link, GPS, timestamp
- [ ] **Share report** — Web Share API sends the complaint letter as an email draft or WhatsApp message

## Stretch Goals (only if MVP is done by hour 28)

- [ ] Severity heatmap overlay on the map
- [ ] Authority dashboard — filtered view by hazard type and area
- [ ] Push notification when a report you upvoted gets resolved
- [ ] Offline mode — queue reports when no internet, sync when back online

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                  React PWA                       │
│  Camera → Preview → Submit → Map → Share        │
└────────────────────┬────────────────────────────┘
                     │ REST (JSON + multipart)
                     ▼
┌─────────────────────────────────────────────────┐
│               FastAPI Backend                    │
│                                                  │
│  POST /report     → handles upload pipeline      │
│  GET  /reports    → returns all map pins         │
│  POST /upvote     → increments upvote count      │
└──────┬─────────────────────────┬────────────────┘
       │                         │
       ▼                         ▼
┌─────────────┐         ┌────────────────────────┐
│  Supabase   │         │     AI Pipeline         │
│  Postgres   │         │                         │
│  (reports)  │         │  1. Cloud Vision API    │
│             │         │     → raw labels        │
│  Storage    │         │                         │
│  (photos)   │         │  2. Gemini Flash API    │
└─────────────┘         │     → classification    │
                        │     → complaint letter  │
                        └────────────────────────┘
```

---

## Database Schema

```sql
-- reports table
id            uuid primary key
user_id       uuid references auth.users
photo_url     text
lat           float
lng           float
hazard_type   text        -- "illegal_dumping" | "oil_spill" | "e_waste" | "water_pollution"
severity      text        -- "low" | "medium" | "high"
department    text        -- "Municipal Sanitation" | "EPA" | etc.
complaint     text        -- generated letter
upvotes       integer default 0
status        text default "open"   -- "open" | "in_review" | "resolved"
created_at    timestamp default now()
```

---

## Team Roles & Responsibilities

### Person A — Backend + AI Pipeline
**Owns:** FastAPI server, Cloud Vision integration, Gemini classification prompt, Supabase schema, photo storage

**Hour-by-hour:**
- H0–3: Scaffold FastAPI, set up Supabase project, create reports table, configure storage bucket
- H3–7: Build `/report` endpoint — accepts photo + GPS, calls Cloud Vision, filters labels
- H7–12: Build Gemini classification layer — prompt engineering for hazard type, severity, dept, letter
- H12–16: Build `/reports` and `/upvote` endpoints, test full pipeline end-to-end with Postman
- H16–20: Seed database with 10 real reports from around venue, fix edge cases
- H20–28: Support frontend integration, fix any pipeline bugs surfaced during UI testing
- H28–36: Buffer, polish, help with demo prep

### Person B — Frontend + Map
**Owns:** React PWA setup, camera flow, Leaflet map, report submission UI, upvote UI

**Hour-by-hour:**
- H0–3: Scaffold React PWA with Vite, set up Tailwind, configure service worker for PWA
- H3–7: Build camera capture screen — open camera, preview photo, confirm/retake
- H7–12: Build submission flow — GPS auto-attach, loading state during AI processing, result display
- H12–18: Build Leaflet map — fetch all reports, render colored pins, popup with hazard info + upvote button
- H18–24: Build complaint letter modal — display generated letter, copy button, Web Share API integration
- H24–28: Polish UI — loading skeletons, error states, mobile responsiveness
- H28–36: Final UI fixes from testing, demo walkthrough prep

### Person C — Auth + DevOps + Pitch
**Owns:** Supabase Auth, GitHub Actions CI/CD, Vercel + Railway deploy, demo data seeding, pitch deck, demo script

**Hour-by-hour:**
- H0–3: Set up GitHub repo, Vercel project, Railway project, configure environment variables
- H3–6: Implement Supabase Auth (Google OAuth) on frontend + protect upvote/submit endpoints
- H6–10: Set up GitHub Actions — auto-deploy frontend to Vercel and backend to Railway on push to main
- H10–16: Monitor integration between Person A and Person B — flag blockers, test on a real phone
- H16–22: Seed realistic demo data — photograph 10 actual hazards near venue, submit via app
- H22–28: Build pitch deck (problem → demo → tech → impact → roadmap), write 90-second demo script
- H28–34: Full rehearsal run x3, time the demo, prepare fallback (cached responses for offline demo)
- H34–36: Final submit, submission form, screenshots

---

## 36-Hour Build Schedule

```
Hour 00–03   Kickoff
             ├── A: FastAPI scaffold + Supabase setup
             ├── B: React PWA scaffold + Tailwind
             └── C: Repo + Vercel + Railway + env vars

Hour 03–07   Core pipeline
             ├── A: /report endpoint + Cloud Vision call
             ├── B: Camera capture UI
             └── C: Supabase Auth setup

Hour 07–12   AI layer + submission flow
             ├── A: Gemini classification + letter prompt
             ├── B: Submission UI + GPS attach
             └── C: CI/CD pipeline live

Hour 12–16   Map + endpoints
             ├── A: /reports + /upvote endpoints
             ├── B: Leaflet map + pin rendering
             └── C: First full phone test + bug log

Hour 16–20   Integration
             ├── All: Connect frontend to backend, test full flow on mobile
             └── C: Seed 10 real reports near venue

Hour 20–24   Polish sprint
             ├── A: Edge cases (quota errors, low-confidence labels)
             ├── B: Mobile responsiveness + loading states
             └── C: Pitch deck draft

Hour 24–28   Complaint letter + share
             ├── A: Letter generation tuning
             ├── B: Letter modal + Web Share API
             └── C: Demo script written

Hour 28–32   Freeze + demo prep
             ├── All: No new features — fix only
             └── C: 3x rehearsal, time the demo

Hour 32–36   Submit
             ├── All: Final testing on a real phone
             └── C: Submission form + screenshots + README
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cloud Vision quota hit during demo | Low | High | Set billing cap at $5, cache 5 photo-result pairs as fallback |
| Gemini misclassifies hazard type | Medium | Medium | Show raw Vision labels alongside classification so demo still makes sense |
| GPS unavailable in venue | Medium | Medium | Allow manual location pin drop on map as fallback |
| Empty map during pitch | High | High | Seed 10 real reports before presentation — non-negotiable |
| Railway cold start delays API | Medium | Medium | Ping backend every 5 min with a cron to keep it warm |
| Camera API blocked on some browsers | Low | High | Test on Chrome Android and Safari iOS before demo — PWA works on both |

---

## API Keys Needed (get these in Hour 0)

- [ ] Google Cloud Vision API key — [console.cloud.google.com](https://console.cloud.google.com)
- [ ] Gemini API key — [aistudio.google.com](https://aistudio.google.com) (free tier)
- [ ] Supabase project URL + anon key — [supabase.com](https://supabase.com)

> Store all keys in `.env` — never commit to GitHub. Use Vercel and Railway environment variable settings for production.

---

## Demo Script (90 seconds)

1. **(0:00)** Open EcoSnap on phone. Show the live map — pins already visible from pre-seeded reports.
2. **(0:15)** Walk to a hazard (or show a pre-taken photo). Tap "Report a Hazard." Camera opens.
3. **(0:25)** Take photo. Loading indicator appears — "Analyzing with AI…"
4. **(0:35)** Result: "Illegal dumping · High severity · Responsible: Municipal Sanitation Dept."
5. **(0:45)** Tap "View Complaint Letter" — pre-filled formal letter appears with GPS, timestamp, photo link.
6. **(0:55)** Tap Share → sends as email draft ready to forward to the authority.
7. **(1:05)** Back on map — new pin appears. Show a second pin with 7 upvotes. "When 5+ citizens upvote the same issue, the authority gets an automatic escalation alert."
8. **(1:20)** Close: "EcoSnap patches reality — one photo at a time."

---

## Judging Criteria Alignment

| Criterion | How EcoSnap addresses it |
|---|---|
| Innovation | AI pipeline combining Cloud Vision + Gemini for structured hazard triage — not just a reporting form |
| Impact | Directly addresses environmental negligence; scalable to any city globally |
| Technical complexity | Two-API AI pipeline, real-time map, PWA camera, complaint generation |
| Completeness | Fully functional end-to-end: photo → AI → map → letter → share |
| Theme fit | "Patch the Reality" — literally patching broken environmental reality |

---

## Post-Hackathon Roadmap

- **Week 1–2:** Open source the repo, post on Product Hunt
- **Month 1:** Partner with one local NGO or municipal body to pilot real report routing
- **Month 2:** Add authority dashboard — filtered inbox of reports by area and severity
- **Month 3:** WhatsApp Bot version — report a hazard without opening a browser
- **Month 6:** Explore civic tech grants (Google.org, UN Environment Programme)

---

*Built in 36 hours. Powered by Google Cloud Vision, Gemini, Supabase, and a genuine frustration with ignored potholes.*
