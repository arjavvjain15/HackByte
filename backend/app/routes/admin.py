"""
EcoSnap — Admin Routes
GET   /api/admin/reports   — All reports with filters + sorting
PATCH /api/admin/reports   — Bulk status update
GET   /api/admin/stats     — Dashboard stat cards
"""
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.config import supabase
from app.utils.validators import BulkStatusUpdate

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])


# ── GET /api/admin/reports ────────────────────────────────────────────────────
@router.get("/admin/reports")
async def admin_get_reports(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    hazard_type: Optional[str] = Query(None),
    sort: Optional[str] = Query(
        "newest",
        description="newest | most_upvoted | highest_severity",
    ),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Admin: Get all reports with optional filtering and sorting.
    In hackathon mode, no auth check — protect this in production.
    """
    try:
        query = supabase.table("reports").select(
            "id, user_id, photo_url, lat, lng, hazard_type, severity, "
            "department, summary, complaint, upvotes, status, created_at, resolved_at"
        )

        # Filters
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        if hazard_type:
            query = query.eq("hazard_type", hazard_type)

        # Sorting
        if sort == "most_upvoted":
            query = query.order("upvotes", desc=True)
        elif sort == "highest_severity":
            # Severity order: high > medium > low
            # Supabase doesn't support custom sort orders natively,
            # so we fetch and sort in Python
            result = query.limit(limit).execute()
            severity_order = {"high": 0, "medium": 1, "low": 2}
            data = sorted(
                result.data or [],
                key=lambda r: severity_order.get(r.get("severity", "low"), 2),
            )
            return {"reports": data, "count": len(data)}
        else:
            # Default: newest first
            query = query.order("created_at", desc=True)

        result = query.limit(limit).execute()
        return {"reports": result.data or [], "count": len(result.data or [])}

    except Exception as e:
        logger.error(f"Admin get reports failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── PATCH /api/admin/reports ──────────────────────────────────────────────────
@router.patch("/admin/reports")
async def admin_bulk_update(body: BulkStatusUpdate):
    """
    Admin: Bulk-update the status of multiple reports.
    On 'resolved': sets resolved_at timestamp and increments
    the report owner's reports_resolved counter.
    """
    if not body.ids:
        raise HTTPException(status_code=400, detail="No report IDs provided.")

    now_iso = datetime.now(timezone.utc).isoformat()

    update_data: dict = {"status": body.status}
    if body.status == "resolved":
        update_data["resolved_at"] = now_iso

    try:
        result = supabase.table("reports").update(update_data).in_(
            "id", body.ids
        ).execute()

        # If resolved, increment owner's counter (best-effort)
        if body.status == "resolved":
            _increment_resolved_counts(body.ids)

        return {
            "success": True,
            "updated_count": len(result.data or []),
            "status": body.status,
        }

    except Exception as e:
        logger.error(f"Admin bulk update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/admin/stats ──────────────────────────────────────────────────────
@router.get("/admin/stats")
async def admin_stats():
    """
    Admin: Stat card numbers for the dashboard header.
    Returns open, in_review, escalated, resolved counts,
    and average resolution time in hours.
    """
    try:
        # Fetch counts per status
        all_result = supabase.table("reports").select(
            "status, created_at, resolved_at"
        ).execute()
        rows = all_result.data or []

        counts = {"open": 0, "in_review": 0, "escalated": 0, "resolved": 0}
        resolution_times: list[float] = []

        for row in rows:
            s = row.get("status", "open")
            if s in counts:
                counts[s] += 1
            # Calculate resolution time for resolved reports
            if s == "resolved" and row.get("created_at") and row.get("resolved_at"):
                try:
                    created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                    resolved = datetime.fromisoformat(row["resolved_at"].replace("Z", "+00:00"))
                    hours = (resolved - created).total_seconds() / 3600
                    if hours >= 0:
                        resolution_times.append(hours)
                except Exception:
                    pass

        avg_resolution = (
            round(sum(resolution_times) / len(resolution_times), 1)
            if resolution_times else None
        )

        return {
            "open": counts["open"],
            "in_review": counts["in_review"],
            "escalated": counts["escalated"],
            "resolved": counts["resolved"],
            "total": len(rows),
            "avg_resolution_hours": avg_resolution,
        }

    except Exception as e:
        logger.error(f"Admin stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Helper ────────────────────────────────────────────────────────────────────
def _increment_resolved_counts(report_ids: list[str]):
    """
    For each resolved report, increment the owning user's reports_resolved.
    Best-effort — errors are logged but not raised.
    """
    try:
        reports = supabase.table("reports").select("user_id").in_(
            "id", report_ids
        ).execute()
        user_ids = [r["user_id"] for r in (reports.data or []) if r.get("user_id")]

        for uid in set(user_ids):
            try:
                supabase.rpc(
                    "increment_reports_resolved",
                    {"user_id_input": uid}
                ).execute()
            except Exception as e:
                logger.warning(f"Could not increment reports_resolved for {uid}: {e}")

    except Exception as e:
        logger.warning(f"_increment_resolved_counts error: {e}")
