# EcoSnap (HackByte4.0)

Backend scaffold for the EcoSnap hackathon project.

**Photo Upload (Feature 2)**  
Use `POST /api/upload` to upload a camera photo to Supabase Storage and receive a public URL.  
Use `POST /api/uploads/presign` to get a signed upload URL for direct-to-storage uploads.

**AI Classification (Feature 3)**  
Use `POST /api/classify` to call Cloud Vision + Gemini and get a structured hazard result.

**Report Submission (Feature 4)**  
Use `POST /api/reports` to save a full report to the database.  
Admin-only: `GET /api/admin/reports` returns all reports.  
Admin-only: `PATCH /api/admin/reports` bulk-updates report status.
Public: `GET /api/reports` returns map pins.  
User: `GET /api/reports/nearby` returns nearby hazards.  
Admin-only: `GET /api/admin/stats` returns stat card numbers.

**Required env vars**
```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
SUPABASE_STORAGE_BUCKET=hazard-photos
GOOGLE_CLOUD_VISION_API_KEY=
GEMINI_API_KEY=
```

**Run locally**
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Upload example (curl)**
```
curl -X POST "http://localhost:8000/api/upload" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" ^
  -F "file=@photo.jpg"
```

**Presign example (curl)**
```
curl -X POST "http://localhost:8000/api/uploads/presign" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"filename\":\"photo.jpg\",\"content_type\":\"image/jpeg\"}"
```

**Classify example (curl)**
```
curl -X POST "http://localhost:8000/api/classify" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"photo_url\":\"https://...\",\"lat\":12.34,\"lng\":56.78,\"reporter_name\":\"Alex\"}"
```

**Create report example (curl)**
```
curl -X POST "http://localhost:8000/api/reports" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"photo_url\":\"https://...\",\"lat\":12.34,\"lng\":56.78,\"hazard_type\":\"illegal_dumping\",\"severity\":\"high\",\"department\":\"Municipal Sanitation\",\"summary\":\"Trash pile by the curb\",\"complaint_letter\":\"...\"}"
```

**Admin list reports example (curl)**
```
curl -X GET "http://localhost:8000/api/admin/reports" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Admin bulk update example (curl)**
```
curl -X PATCH "http://localhost:8000/api/admin/reports" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"ids\":[\"report-id-1\",\"report-id-2\"],\"status\":\"resolved\"}"
```

**Public map reports (curl)**
```
curl -X GET "http://localhost:8000/api/reports"
```

**Nearby reports (curl)**
```
curl -X GET "http://localhost:8000/api/reports/nearby?lat=12.34&lng=56.78&radius=2000" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Admin stats (curl)**
```
curl -X GET "http://localhost:8000/api/admin/stats" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```
