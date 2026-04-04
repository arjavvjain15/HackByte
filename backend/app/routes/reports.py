"""
EcoSnap — Reports Routes
POST   /api/reports                          — Submit a new report
GET    /api/reports                          — All reports (map view)
GET    /api/reports/nearby                   — Reports within radius
GET    /api/reports/mine                     — Current user's reports
GET    /api/reports/{id}                     — Single report
POST   /api/reports/{id}/upvote              — Upvote a report
GET    /api/reports/{id}/upvote-status       — Check if user already voted
GET    /api/reports/{id}/complaint-letter    — Get complaint letter (owner or admin)
GET    /api/reports/{id}/share-payload       — Shareable payload (email/WhatsApp/copy/native)
"""
import logging
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.config import supabase
from app.core.auth import get_current_user, get_current_user_id
from app.services.badges import ensure_badges
from app.utils.haversine import haversine_km

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Reports"])

SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    photo_url: str = Field(..., min_length=5, max_length=2048)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    hazard_type: Optional[str] = None
    severity: Optional[str] = None
    department: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=500)
    complaint: Optional[str] = Field(None, max_length=8000)

    @field_validator("hazard_type")
    @classmethod
    def validate_hazard_type(cls, v):
        valid = {"illegal_dumping", "oil_spill", "e_waste", "water_pollution", "blocked_drain", "air_pollution", "other"}
        if v and v not in valid:
            raise ValueError(f"hazard_type must be one of: {valid}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v and v not in {"high", "medium", "low"}:
            raise ValueError("severity must be: high, medium, or low")
        return v


def _is_admin_user(user_id: str) -> bool:
    try:
        result = supabase.table("profiles").select("is_admin").eq("id", user_id).single().execute()
        if isinstance(result.data, dict):
            return bool(result.data.get("is_admin"))
    except Exception:
        pass
    return False


def _build_share_payload(report: dict) -> dict:
    report_id = report.get("id", "")
    department = report.get("department") or "Concerned Department"
    hazard_type = report.get("hazard_type") or "environmental_hazard"
    lat = report.get("lat", "")
    lng = report.get("lng", "")
    photo_url = report.get("photo_url") or ""
    complaint = report.get("complaint") or ""
    created_at = report.get("created_at") or datetime.now(timezone.utc).isoformat()

    subject = f"EcoSnap Report - {hazard_type.replace('_', ' ').title()}"
    text = (
        f"To: {department}\n"
        f"Date: {created_at}\n"
        f"Subject: {subject}\n\n"
        f"{complaint}\n\n"
        f"Photo evidence: {photo_url}\n"
        f"GPS coordinates: {lat}, {lng}\n"
        f"Report ID: {report_id}"
    )
    mailto_url = f"mailto:?subject={quote(subject, safe='')}&body={quote(text, safe='')}"
    whatsapp_url = f"https://wa.me/?text={quote(text, safe='')}"

    return {
        "title": "EcoSnap Report",
        "text": text,
        "copy_text": text,
        "mailto_url": mailto_url,
        "whatsapp_url": whatsapp_url,
    }


# ── POST /api/reports ─────────────────────────────────────────────────────────

@router.post("/reports", status_code=201)
async def create_report(
    body: ReportCreate,
    user: dict = Depends(get_current_user),
):
    """Submit a new hazard report. Increments reporter's count and checks badges."""
    user_id = get_current_user_id(user)

    report_data = {
        "user_id": user_id,
        "photo_url": body.photo_url,
        "lat": body.lat,
        "lng": body.lng,
        "hazard_type": body.hazard_type,
        "severity": body.severity,
        "department": body.department,
        "summary": body.summary,
        "complaint": body.complaint,
        "upvotes": 0,
        "status": "open",
    }

    try:
        result = supabase.table("reports").insert(report_data).execute()
        inserted = result.data[0] if result.data else {}
    except Exception as e:
        logger.error(f"Failed to insert report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")

    # Increment reports_submitted counter (best-effort)
    try:
        profile_res = supabase.table("profiles").select("reports_submitted").eq("id", user_id).single().execute()
        current = int((profile_res.data or {}).get("reports_submitted") or 0)
        supabase.table("profiles").update({"reports_submitted": current + 1}).eq("id", user_id).execute()
    except Exception as e:
        logger.warning(f"Could not update reports_submitted: {e}")

    # Award badges (best-effort)
    try:
        ensure_badges(user_id)
    except Exception as e:
        logger.warning(f"Badge check failed: {e}")

    return {"success": True, "report": inserted}


# ── GET /api/reports ──────────────────────────────────────────────────────────

@router.get("/reports")
async def get_reports(
    user_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    area_name: Optional[str] = Query(None, min_length=2, max_length=120),
    limit: int = Query(500, ge=1, le=1000),
):
    """Public endpoint — returns reports for the map. Supports multiple filters."""
    try:
        query = supabase.table("reports").select(
            "id,user_id,photo_url,lat,lng,hazard_type,severity,"
            "department,summary,upvotes,status,created_at,resolved_at"
        )
        if user_id:
            query = query.eq("user_id", user_id)
        if status:
            query = query.eq("status", status)
        if severity:
            query = query.eq("severity", severity)
        if hazard_type:
            query = query.eq("hazard_type", hazard_type)

        result = query.order("created_at", desc=True).limit(limit).execute()
        data = result.data or []

        if area_name:
            norm = area_name.strip().lower()
            data = [r for r in data if norm in str(r.get("summary") or "").lower()]

        return {"reports": data}
    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/reports/nearby ───────────────────────────────────────────────────

@router.get("/reports/nearby")
async def get_nearby_reports(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(2000.0, ge=100, le=50000, description="Radius in metres"),
    user: Optional[dict] = Depends(get_current_user),
):
    """Returns reports within the given radius using Haversine distance."""
    user_id = get_current_user_id(user) if user else None
    radius_km = radius / 1000.0

    # Try server-side RPC first (fast SQL haversine)
    try:
        rpc_res = supabase.rpc("nearby_reports", {"lat": lat, "lng": lng, "radius_m": int(radius)}).execute()
        if rpc_res.data is not None:
            rows = rpc_res.data or []
            if user_id:
                try:
                    uv = supabase.table("upvotes").select("report_id").eq("user_id", user_id).execute()
                    voted_ids = {r.get("report_id") for r in (uv.data or [])}
                    for row in rows:
                        row["voted"] = row.get("id") in voted_ids
                except Exception:
                    pass
            return {"reports": rows, "count": len(rows), "radius_km": radius_km}
    except Exception:
        pass  # Fall through to Python-side filtering

    # Python-side Haversine fallback
    try:
        result = supabase.table("reports").select(
            "id,lat,lng,hazard_type,severity,department,summary,upvotes,status,created_at"
        ).in_("status", ["open", "in_review", "escalated"]).execute()
        all_reports = result.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Get user's voted report IDs
    voted_ids: set = set()
    if user_id:
        try:
            uv = supabase.table("upvotes").select("report_id").eq("user_id", user_id).execute()
            voted_ids = {r.get("report_id") for r in (uv.data or [])}
        except Exception:
            pass

    nearby = []
    for report in all_reports:
        try:
            dist = haversine_km(lat, lng, float(report["lat"]), float(report["lng"]))
            if dist <= radius_km:
                report["distance_km"] = round(dist, 3)
                report["distance_m"] = round(dist * 1000, 1)
                report["voted"] = report.get("id") in voted_ids
                nearby.append(report)
        except Exception:
            continue

    nearby.sort(key=lambda r: r.get("distance_km", 9999))
    return {"reports": nearby, "count": len(nearby), "radius_km": radius_km}


# ── GET /api/reports/mine ─────────────────────────────────────────────────────

@router.get("/reports/mine")
async def get_my_reports(user: dict = Depends(get_current_user)):
    """Returns reports submitted by the authenticated user with progress info."""
    user_id = get_current_user_id(user)
    try:
        result = (
            supabase.table("reports")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = result.data or []
        for row in rows:
            status = row.get("status") or "open"
            row["progress_percent"] = {"resolved": 100, "in_review": 66, "escalated": 80}.get(status, 33)
            row["status_label"] = {"resolved": "Resolved", "in_review": "In review", "escalated": "Escalated"}.get(status, "Open")
        return {"reports": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/reports/{id} ─────────────────────────────────────────────────────

@router.get("/reports/{report_id}")
async def get_report(report_id: str, _user: dict = Depends(get_current_user)):
    """Get a single report by ID."""
    try:
        result = supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /api/reports/{id}/upvote ─────────────────────────────────────────────

@router.post("/reports/{report_id}/upvote")
async def upvote_report(report_id: str, user: dict = Depends(get_current_user)):
    """Upvote a report. Auto-escalates when upvotes reach 5. One vote per user."""
    user_id = get_current_user_id(user)

    try:
        report_res = supabase.table("reports").select("id,user_id,upvotes,status").eq("id", report_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Report not found: {e}")

    if not isinstance(report_res.data, dict):
        raise HTTPException(status_code=404, detail="Report not found")

    # ── Check for duplicate vote manually first ──
    try:
        existing = supabase.table("upvotes").select("id").eq("report_id", report_id).eq("user_id", user_id).execute()
        if existing.data:
            raise HTTPException(status_code=409, detail="You have already upvoted this report")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {e}")

    try:
        supabase.table("upvotes").insert({"report_id": report_id, "user_id": user_id}).execute()
    except Exception as e:
        msg = str(e).lower()
        if "duplicate" in msg or "23505" in msg or "unique" in msg:
            raise HTTPException(status_code=409, detail="You have already upvoted this report")
        raise HTTPException(status_code=500, detail=f"Upvote failed: {e}")

    current_upvotes = int(report_res.data.get("upvotes") or 0)
    current_status = report_res.data.get("status") or "open"
    report_owner = report_res.data.get("user_id")

    new_upvotes = current_upvotes + 1
    new_status = "escalated" if new_upvotes >= 5 and current_status != "escalated" else current_status

    try:
        supabase.table("reports").update({"upvotes": new_upvotes, "status": new_status}).eq("id", report_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report update failed: {e}")

    if report_owner:
        try:
            ensure_badges(report_owner)
        except Exception:
            pass

    return {"report_id": report_id, "upvotes": new_upvotes, "status": new_status}


# ── GET /api/reports/{id}/upvote-status ───────────────────────────────────────

@router.get("/reports/{report_id}/upvote-status")
async def get_upvote_status(report_id: str, user: dict = Depends(get_current_user)):
    """Check if the current user has already upvoted a report."""
    user_id = get_current_user_id(user)
    try:
        uv_res = (
            supabase.table("upvotes")
            .select("id")
            .eq("report_id", report_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        report_res = supabase.table("reports").select("upvotes,status").eq("id", report_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    voted = bool(uv_res.data)
    upvotes = 0
    status = "open"
    if isinstance(report_res.data, dict):
        upvotes = int(report_res.data.get("upvotes") or 0)
        status = report_res.data.get("status") or "open"

    return {"report_id": report_id, "voted": voted, "upvotes": upvotes, "status": status}


# ── GET /api/reports/{id}/complaint-letter ────────────────────────────────────

@router.get("/reports/{report_id}/complaint-letter")
async def get_complaint_letter(report_id: str, user: dict = Depends(get_current_user)):
    """
    Returns the complaint letter for a report.
    Only accessible by the report owner or an admin.
    """
    user_id = get_current_user_id(user)
    try:
        report_res = (
            supabase.table("reports")
            .select("id,user_id,hazard_type,department,complaint,created_at,lat,lng,photo_url")
            .eq("id", report_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Report not found: {e}")

    report = report_res.data
    if not isinstance(report, dict):
        raise HTTPException(status_code=404, detail="Report not found")

    is_owner = report.get("user_id") == user_id
    if not is_owner and not _is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Access denied — only the report owner or an admin can view this letter")

    if not report.get("complaint"):
        raise HTTPException(status_code=404, detail="Complaint letter is not available for this report")

    return {
        "report_id": report.get("id"),
        "complaint_letter": report.get("complaint"),
        "department": report.get("department"),
        "hazard_type": report.get("hazard_type"),
    }


# ── GET /api/reports/{id}/share-payload ──────────────────────────────────────

@router.get("/reports/{report_id}/share-payload")
async def get_share_payload(
    report_id: str,
    channel: str = Query(default="native", enum=["native", "email", "whatsapp", "copy"]),
    user: dict = Depends(get_current_user),
):
    """
    Returns shareable links for the complaint letter.
    channel: native | email | whatsapp | copy
    """
    user_id = get_current_user_id(user)
    try:
        report_res = (
            supabase.table("reports")
            .select("id,user_id,hazard_type,department,complaint,created_at,lat,lng,photo_url")
            .eq("id", report_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Report not found: {e}")

    report = report_res.data
    if not isinstance(report, dict):
        raise HTTPException(status_code=404, detail="Report not found")

    is_owner = report.get("user_id") == user_id
    if not is_owner and not _is_admin_user(user_id):
        raise HTTPException(status_code=403, detail="Access denied")

    payload = _build_share_payload(report)

    channel_payload: dict
    if channel == "email":
        channel_payload = {"channel": channel, "title": payload["title"], "text": payload["text"], "target_url": payload["mailto_url"]}
    elif channel == "whatsapp":
        channel_payload = {"channel": channel, "title": payload["title"], "text": payload["text"], "target_url": payload["whatsapp_url"]}
    elif channel == "copy":
        channel_payload = {"channel": channel, "title": payload["title"], "text": payload["copy_text"], "target_url": None}
    else:
        channel_payload = {"channel": "native", "title": payload["title"], "text": payload["text"], "target_url": None}

    return {**payload, "channel": channel, "channel_payload": channel_payload}
