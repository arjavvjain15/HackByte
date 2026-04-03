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
User: `POST /api/reports/:id/upvote` upvotes a report (Feature 6).
User: `GET /api/reports/:id/upvote-status` checks if current user already voted.
User: `GET /api/reports/:id/complaint-letter` gets stored complaint letter (Feature 7 helper).
User: `GET /api/reports/:id/share-payload` gets share-ready payload/URLs (Feature 7 helper).

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

**Upvote example (curl)**
```
curl -X POST "http://localhost:8000/api/reports/<report-id>/upvote" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Upvote status example (curl)**
```
curl -X GET "http://localhost:8000/api/reports/<report-id>/upvote-status" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Admin reports with filters (curl)**
```
curl -X GET "http://localhost:8000/api/admin/reports?severity=high&status=open&area_name=Downtown&sort=most_upvoted" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Complaint letter helper (curl)**
```
curl -X GET "http://localhost:8000/api/reports/<report-id>/complaint-letter" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

**Share payload helper (curl)**
```
curl -X GET "http://localhost:8000/api/reports/<report-id>/share-payload" ^
  -H "Authorization: Bearer <SUPABASE_ACCESS_TOKEN>"
```

Query params now use strict enum validation:
`severity`: `high|medium|low`
`status`: `open|in_review|resolved|escalated`
`sort`: `newest|oldest|most_upvoted|highest_severity`

**Nearby RPC (optional)**
If you want Postgres to filter by distance, create this function once in Supabase SQL:
```
create or replace function public.nearby_reports(lat float, lng float, radius_m int)
returns table (
  id uuid,
  lat float,
  lng float,
  hazard_type text,
  severity text,
  upvotes int,
  status text,
  created_at timestamp,
  distance_m float
)
language sql
as $$
  select
    id, lat, lng, hazard_type, severity, upvotes, status, created_at,
    6371000 * acos(
      cos(radians(lat)) * cos(radians(reports.lat)) * cos(radians(reports.lng) - radians(lng)) +
      sin(radians(lat)) * sin(radians(reports.lat))
    ) as distance_m
  from reports
  where 6371000 * acos(
      cos(radians(lat)) * cos(radians(reports.lat)) * cos(radians(reports.lng) - radians(lng)) +
      sin(radians(lat)) * sin(radians(reports.lat))
    ) <= radius_m
  order by distance_m asc;
$$;
```

You can run the full SQL helper script from:
`backend/sql/feature6_feature5_helpers.sql`
