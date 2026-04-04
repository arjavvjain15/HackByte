# 🌍 EcoSnap — Full Hackathon Plan (36 Hours)

## 🚀 Overview
EcoSnap is an AI-powered civic platform where users report environmental hazards and authorities resolve them.

---

# 👥 TEAM STRUCTURE (3 MEMBERS)

## 🧠 PERSON A — BACKEND + AI

### AI PROMPTS
1. Hazard Classification Prompt
- Classify hazard
- Assign severity
- Identify department
- Generate complaint letter

2. Fallback Prompt
- Handle low-confidence cases

### FEATURES
1. Auth (Supabase)
2. AI Pipeline (/api/classify)
3. Reports API (/api/reports)
4. Nearby Reports (Haversine)
5. Upvote System
6. Admin APIs
7. Badge Logic
8. Error Handling & Fallbacks

---

## 🎨 PERSON B — FRONTEND (USER APP)

### FEATURES
1. Auth UI
2. Camera + Upload
3. AI Result Screen
4. Report Submission
5. Dashboard (My Reports)
6. Map (Leaflet)
7. Upvote UI
8. Complaint Letter Modal
9. Nearby Hazards
10. Badges UI
11. UX Polish

---

## 🛠️ PERSON C — ADMIN + DEVOPS

### ADMIN FEATURES
1. Dashboard UI
2. Report Actions
3. Filters & Sorting
4. Stats Panel
5. Escalation System
6. Admin Map

### DEVOPS
7. Deployment (Vercel + Railway)
8. Environment Setup
9. CI/CD

### DEMO
10. Seed 10 reports
11. Prepare pitch
12. Demo rehearsal

---

# 🤖 AI PIPELINE
Image → Vision API → Gemini → JSON Output

---

# 🗄️ DATABASE
profiles, reports, upvotes, user_badges

---

# 🔌 API ENDPOINTS
- /api/classify
- /api/reports
- /api/admin

---

# ⏱️ EXECUTION STRATEGY
- Backend builds AI first
- Frontend builds camera + UI
- DevOps seeds data + deploys

---

# 💡 TAGLINE
EcoSnap patches reality — one photo at a time.
