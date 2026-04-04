"""
EcoSnap — Admin Routes
GET    /api/admin/reports              — All reports with full filters + sort
PATCH  /api/admin/reports              — Bulk status update
GET    /api/admin/stats                — Dashboard stat cards
GET    /api/admin/escalations          — Reports with 5+ upvotes
GET    /api/admin/breakdown            — Hazard type + area breakdown
GET    /api/admin/reports/export       — CSV export
GET    /api/admin/dashboard            — Full dashboard bundle (stats + reports + breakdown)
"""
import logging
import io
import csv
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import supabase
from app.core.auth import get_current_user, require_admin
from app.services.badges import ensure_badges

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}
ALLOWED_STATUSES = {"open", "in_review", "resolved", "escalated"}


class BulkUpdateRequest(BaseModel):
    ids: list[str]
    status: str


def _apply_sort(data: list[dict], sort: str) -> list[dict]:
    if sort == "highest_severity":
        data.sort(key=lambda r: SEVERITY_RANK.get(r.get("severity") or "", 0), reverse=True)
    elif sort == "most_upvoted":
        data.sort(key=lambda r: int(r.get("upvotes") or 0), reverse=True)
    return data


def _fetch_reports(
    severity: str | None,
    status: str | None,
    hazard_type: str | None,
    area_name: str | None,
    date_from: str | None,
    date_to: str | None,
    sort: str,
    limit: int,
    escalated_only: bool = False,
    min_upvotes: int | None = None,
) -> list[dict]:
    try:
        query = supabase.table("reports").select("*")
        if severity:
            query = query.eq("severity", severity)
        if hazard_type:
            query = query.eq("hazard_type", hazard_type)
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)
        if escalated_only:
            query = query.eq("status", "escalated")
        elif status:
            query = query.eq("status", status)
        if min_upvotes is not None:
            query = query.gte("upvotes", min_upvotes)

        if sort == "most_upvoted":
            query = query.order("upvotes", desc=True)
        elif sort == "oldest":
            query = query.order("created_at", desc=False)
        else:
            query = query.order("created_at", desc=True)

        result = query.limit(limit).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e}")

    data = result.data or []
    if area_name:
        norm = area_name.strip().lower()
        data = [r for r in data if norm in str(r.get("summary") or "").lower()]

    return _apply_sort(data, sort)


# ── GET /api/admin/reports ────────────────────────────────────────────────────

@router.get("/reports")
def admin_list_reports(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    area_name: Optional[str] = Query(None, min_length=2, max_length=120),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: str = Query("newest", enum=["newest", "oldest", "most_upvoted", "highest_severity"]),
    limit: int = Query(500, ge=1, le=1000),
    user: dict = Depends(get_current_user),
):
    """Admin: full report list with filtering, sorting, and pagination."""
    require_admin(user)
    reports = _fetch_reports(severity, status, hazard_type, area_name, date_from, date_to, sort, limit)
    return {"reports": reports}


# ── PATCH /api/admin/reports ──────────────────────────────────────────────────

@router.patch("/reports")
def admin_bulk_update(
    payload: BulkUpdateRequest,
    user: dict = Depends(get_current_user),
):
    """Admin: bulk update report status. Also updates resolved_at and profile counters."""
    require_admin(user)

    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {ALLOWED_STATUSES}")
    if not payload.ids:
        raise HTTPException(status_code=400, detail="No report IDs provided")

    try:
        reports_res = supabase.table("reports").select("id,user_id,hazard_type").in_("id", payload.ids).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e}")

    reports = reports_res.data or []
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found for provided IDs")

    update_data: dict = {"status": payload.status}
    if payload.status == "resolved":
        update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()
    else:
        update_data["resolved_at"] = None

    try:
        supabase.table("reports").update(update_data).in_("id", payload.ids).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {e}")

    # ===== Native Resolution Emails =====
    if payload.status == "resolved":
        import httpx, os
        try:
            from app.routes.notify import send_resolved_email, ResolvedPayload
            user_emails = {}
            # Get user emails from auth.users natively
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_KEY")
            if url and key:
                auth_res = httpx.get(f"{url}/auth/v1/admin/users", headers={"apikey": key, "Authorization": f"Bearer {key}"})
                if auth_res.status_code < 300:
                    user_emails = {u.get("id"): u.get("email") for u in auth_res.json().get("users", [])}
            
            for r in reports:
                u_email = user_emails.get(r.get("user_id"))
                if u_email:
                    send_resolved_email(ResolvedPayload(
                        report_id=r.get("id"),
                        user_email=u_email,
                        hazard_type=r.get("hazard_type", "unknown")
                    ))
        except Exception as e:
            logger.error(f"Failed to auto-send resolved emails: {e}")

    updated_profiles = 0
    if payload.status == "resolved":
        user_counts = Counter([r.get("user_id") for r in reports if r.get("user_id")])
        for uid, count in user_counts.items():
            try:
                pr = supabase.table("profiles").select("reports_resolved").eq("id", uid).single().execute()
                current = int((pr.data or {}).get("reports_resolved") or 0)
                supabase.table("profiles").update({"reports_resolved": current + count}).eq("id", uid).execute()
                updated_profiles += 1
                ensure_badges(uid)
            except Exception:
                continue

    return {
        "updated_reports": len(reports),
        "updated_profiles": updated_profiles,
        "status": payload.status,
    }


# ── GET /api/admin/stats ──────────────────────────────────────────────────────

@router.get("/stats")
def admin_stats(user: dict = Depends(get_current_user)):
    """Admin: stat card numbers — open, in_review, resolved, escalated, avg resolution time."""
    require_admin(user)
    try:
        result = supabase.table("reports").select("status,created_at,resolved_at,upvotes").execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats fetch failed: {e}")

    reports = result.data or []
    counts = Counter([r.get("status") or "open" for r in reports])
    escalated = sum(1 for r in reports if r.get("status") == "escalated" or (r.get("upvotes") or 0) >= 5)

    resolution_times = []
    for r in reports:
        if r.get("resolved_at") and r.get("created_at"):
            try:
                created = datetime.fromisoformat(str(r["created_at"]).replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(str(r["resolved_at"]).replace("Z", "+00:00"))
                resolution_times.append((resolved - created).total_seconds())
            except Exception:
                continue

    avg_resolution_hours = (
        round(sum(resolution_times) / len(resolution_times) / 3600, 2) if resolution_times else 0.0
    )

    return {
        "open": counts.get("open", 0),
        "in_review": counts.get("in_review", 0),
        "resolved": counts.get("resolved", 0),
        "escalated": escalated,
        "total": len(reports),
        "avg_resolution_hours": avg_resolution_hours,
    }


# ── GET /api/admin/escalations ────────────────────────────────────────────────

@router.get("/escalations")
def admin_escalations(
    severity: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    area_name: Optional[str] = Query(None, min_length=2, max_length=120),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: str = Query("most_upvoted", enum=["newest", "oldest", "most_upvoted", "highest_severity"]),
    min_upvotes: int = Query(5, ge=1),
    limit: int = Query(500, ge=1, le=1000),
    user: dict = Depends(get_current_user),
):
    """Admin: reports with 5+ upvotes (escalated)."""
    require_admin(user)
    reports = _fetch_reports(
        severity, None, hazard_type, area_name, date_from, date_to, sort, limit,
        escalated_only=True, min_upvotes=min_upvotes,
    )
    return {"reports": reports, "count": len(reports)}


# ── GET /api/admin/breakdown ──────────────────────────────────────────────────

@router.get("/breakdown")
def admin_breakdown(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """Admin: breakdown counts by hazard type."""
    require_admin(user)
    try:
        query = supabase.table("reports").select("hazard_type,severity,status")
        if date_from:
            query = query.gte("created_at", date_from)
        if date_to:
            query = query.lte("created_at", date_to)
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        result = query.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Breakdown fetch failed: {e}")

    rows = result.data or []
    by_type = Counter([r.get("hazard_type") or "other" for r in rows])
    by_severity = Counter([r.get("severity") or "medium" for r in rows])
    by_status = Counter([r.get("status") or "open" for r in rows])

    return {
        "by_type": [{"label": k, "count": v} for k, v in by_type.most_common()],
        "by_severity": [{"label": k, "count": v} for k, v in by_severity.most_common()],
        "by_status": [{"label": k, "count": v} for k, v in by_status.most_common()],
    }


# ── GET /api/admin/reports/export ─────────────────────────────────────────────

@router.get("/reports/export")
def admin_export_csv(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    area_name: Optional[str] = Query(None, min_length=2, max_length=120),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: str = Query("newest"),
    limit: int = Query(2000, ge=1, le=5000),
    user: dict = Depends(get_current_user),
):
    """Admin: export filtered reports as CSV file."""
    require_admin(user)
    rows = _fetch_reports(severity, status, hazard_type, area_name, date_from, date_to, sort, limit)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "created_at", "hazard_type", "severity", "status", "upvotes", "department", "lat", "lng"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    csv_content = output.getvalue()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ecosnap_reports.csv"},
    )


# ── GET /api/admin/dashboard ──────────────────────────────────────────────────

@router.get("/dashboard")
def admin_dashboard_bundle(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    area_name: Optional[str] = Query(None, min_length=2, max_length=120),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort: str = Query("newest", enum=["newest", "oldest", "most_upvoted", "highest_severity"]),
    limit: int = Query(500, ge=1, le=1000),
    include_escalations: bool = Query(False),
    user: dict = Depends(get_current_user),
):
    """
    Admin: single endpoint that returns stats + reports + breakdown in one call.
    Use include_escalations=true to also get escalated reports list.
    """
    require_admin(user)
    try:
        stats_res = supabase.table("reports").select("status,created_at,resolved_at,upvotes").execute()
        reports_data = stats_res.data or []
        counts = Counter([r.get("status") or "open" for r in reports_data])
        escalated_count = sum(1 for r in reports_data if r.get("status") == "escalated" or (r.get("upvotes") or 0) >= 5)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats fetch failed: {e}")

    reports = _fetch_reports(severity, status, hazard_type, area_name, date_from, date_to, sort, limit)

    by_type = Counter([r.get("hazard_type") or "other" for r in reports_data])

    bundle = {
        "stats": {
            "open": counts.get("open", 0),
            "in_review": counts.get("in_review", 0),
            "resolved": counts.get("resolved", 0),
            "escalated": escalated_count,
            "total": len(reports_data),
        },
        "reports": reports,
        "breakdown": {
            "by_type": [{"label": k, "count": v} for k, v in by_type.most_common()],
        },
    }

    if include_escalations:
        escalations = _fetch_reports(
            severity, None, hazard_type, area_name, date_from, date_to,
            "most_upvoted", limit, escalated_only=True, min_upvotes=5,
        )
        bundle["escalations"] = escalations
        bundle["escalations_count"] = len(escalations)

    return bundle


# ── GET /api/admin/reports/{id}/resolution-plan ───────────────────────────────

@router.get("/reports/{report_id}/resolution-plan")
async def admin_resolution_plan(
    report_id: str,
    user: dict = Depends(get_current_user),
):
    """
    Admin: On-demand AI prediction of resolution resources based on text context.
    """
    require_admin(user)
    
    try:
        report_res = supabase.table("reports").select("id,hazard_type,severity,summary,complaint").eq("id", report_id).single().execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {e}")

    report = report_res.data
    if not isinstance(report, dict):
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Import the gemini predictor
    from app.services.gemini import predict_resolution_plan, GeminiParseError
    
    try:
        result = await predict_resolution_plan(
            hazard_type=report.get("hazard_type", "unknown"),
            severity=report.get("severity", "unknown"),
            summary=report.get("summary", ""),
            complaint=report.get("complaint", ""),
        )
        return {
            "report_id": report_id,
            "resolution_plan": result
        }
    except GeminiParseError as e:
        raise HTTPException(status_code=502, detail=f"AI Prediction Failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

