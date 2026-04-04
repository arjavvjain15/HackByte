"""
EcoSnap — Upvote Route
POST /api/reports/:id/upvote
Prevents duplicate votes. Auto-escalates at 5+ upvotes.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import supabase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upvotes"])

ESCALATION_THRESHOLD = 5


class UpvoteRequest(BaseModel):
    user_id: str


@router.post("/reports/{report_id}/upvote")
async def upvote_report(report_id: str, body: UpvoteRequest):
    """
    Upvote a report. Each user can only upvote once per report.

    - Returns 409 if user has already voted.
    - Auto-sets status='escalated' when upvotes >= 5.
    """
    user_id = body.user_id

    # ── Check for duplicate vote ─────────────────────────────────────────────
    try:
        existing = supabase.table("upvotes").select("id").eq(
            "report_id", report_id
        ).eq("user_id", user_id).execute()

        if existing.data:
            raise HTTPException(
                status_code=409,
                detail="You have already upvoted this report."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking duplicate upvote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # ── Insert upvote ────────────────────────────────────────────────────────
    try:
        supabase.table("upvotes").insert({
            "report_id": report_id,
            "user_id": user_id,
        }).execute()
    except Exception as e:
        logger.error(f"Error inserting upvote: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save upvote: {str(e)}")

    # ── Increment upvote count on report ─────────────────────────────────────
    try:
        # Fetch current upvote count
        report_result = supabase.table("reports").select(
            "upvotes, status"
        ).eq("id", report_id).single().execute()

        if not report_result.data:
            raise HTTPException(status_code=404, detail="Report not found")

        current_upvotes = (report_result.data.get("upvotes") or 0) + 1
        current_status = report_result.data.get("status", "open")

        # Determine new status
        update_data: dict = {"upvotes": current_upvotes}
        if current_upvotes >= ESCALATION_THRESHOLD and current_status == "open":
            update_data["status"] = "escalated"
            logger.info(f"Report {report_id} escalated with {current_upvotes} upvotes.")

        supabase.table("reports").update(update_data).eq("id", report_id).execute()

        return {
            "success": True,
            "upvotes": current_upvotes,
            "escalated": update_data.get("status") == "escalated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating upvotes on report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
