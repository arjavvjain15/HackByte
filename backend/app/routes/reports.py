"""
EcoSnap — Reports Routes
POST /api/reports           — Submit a new report
GET  /api/reports           — All reports (map view)
GET  /api/reports/nearby    — Reports within radius (Haversine)
GET  /api/reports/mine      — Current user's reports
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.config import supabase
from app.utils.validators import ReportCreate, ReportResponse
from app.utils.haversine import haversine_km

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports"])


# ── POST /api/reports ─────────────────────────────────────────────────────────
@router.post("/reports", status_code=201)
async def create_report(body: ReportCreate):
    """
    Submit a new hazard report to the database.
    Also increments the user's reports_submitted counter.
    """
    report_data = {
        "user_id": body.user_id,
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

        # Increment user's reports_submitted counter (best-effort)
        if body.user_id:
            try:
                supabase.rpc(
                    "increment_reports_submitted",
                    {"user_id_input": body.user_id}
                ).execute()
            except Exception as e:
                logger.warning(f"Could not increment reports_submitted: {e}")

        # Award 'first_report' badge if applicable (best-effort)
        if body.user_id:
            _maybe_award_badge(body.user_id)

        return {"success": True, "report": inserted}

    except Exception as e:
        logger.error(f"Failed to insert report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")


# ── GET /api/reports ──────────────────────────────────────────────────────────
@router.get("/reports")
async def get_reports(
    user_id: Optional[str] = Query(None, description="Filter by user_id"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hazard_type: Optional[str] = Query(None, description="Filter by hazard_type"),
    limit: int = Query(200, ge=1, le=500),
):
    """
    Returns reports for the map. Supports optional filters.
    Public endpoint — no auth required.
    """
    try:
        query = supabase.table("reports").select(
            "id, user_id, photo_url, lat, lng, hazard_type, severity, "
            "department, summary, upvotes, status, created_at, resolved_at"
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
        return {"reports": result.data or []}

    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/reports/nearby ───────────────────────────────────────────────────
@router.get("/reports/nearby")
async def get_nearby_reports(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    radius: float = Query(2000.0, description="Radius in metres"),
):
    """
    Returns reports within the given radius (metres) using Haversine formula.
    Fetches all open/escalated reports and filters in Python.
    """
    radius_km = radius / 1000.0

    try:
        result = supabase.table("reports").select(
            "id, user_id, photo_url, lat, lng, hazard_type, severity, "
            "department, summary, upvotes, status, created_at"
        ).in_("status", ["open", "in_review", "escalated"]).execute()

        all_reports = result.data or []
    except Exception as e:
        logger.error(f"Failed to fetch reports for nearby: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    nearby = []
    for report in all_reports:
        try:
            dist = haversine_km(lat, lng, float(report["lat"]), float(report["lng"]))
            if dist <= radius_km:
                report["distance_km"] = round(dist, 3)
                nearby.append(report)
        except Exception:
            continue

    # Sort by distance ascending
    nearby.sort(key=lambda r: r.get("distance_km", 9999))

    return {"reports": nearby, "count": len(nearby), "radius_km": radius_km}


# ── GET /api/reports/mine ─────────────────────────────────────────────────────
@router.get("/reports/mine")
async def get_my_reports(
    user_id: str = Query(..., description="The user's UUID"),
):
    """
    Returns all reports submitted by a specific user, newest first.
    """
    try:
        result = supabase.table("reports").select("*").eq(
            "user_id", user_id
        ).order("created_at", desc=True).execute()
        return {"reports": result.data or []}
    except Exception as e:
        logger.error(f"Failed to fetch reports for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/reports/:id ──────────────────────────────────────────────────────
@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """
    Get a single report by ID.
    """
    try:
        result = supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Helper: Badge logic (best-effort, doesn't block response) ─────────────────
def _maybe_award_badge(user_id: str):
    """
    Check and award gamification badges. Called after report submission.
    Silently ignores any errors.
    """
    try:
        count_result = supabase.table("reports").select(
            "id", count="exact"
        ).eq("user_id", user_id).execute()
        count = count_result.count or 0

        badge_map = {
            1: "first_report",
            3: "three_reports",
            5: "five_reports",
        }

        badge_id = badge_map.get(count)
        if badge_id:
            # Check if not already awarded
            existing = supabase.table("user_badges").select("id").eq(
                "user_id", user_id
            ).eq("badge_id", badge_id).execute()
            if not existing.data:
                supabase.table("user_badges").insert({
                    "user_id": user_id,
                    "badge_id": badge_id,
                }).execute()
    except Exception as e:
        logger.warning(f"Badge logic error (non-critical): {e}")
