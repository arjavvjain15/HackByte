"""
EcoSnap — Classify Route
POST /api/classify — Cloud Vision → keyword mapping pipeline (requires auth)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any

from app.core.auth import get_current_user
from app.services.classifier import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI Classify"])


class ClassifyRequest(BaseModel):
    photo_url: str = Field(..., min_length=5, max_length=2048, description="Publicly accessible image URL")
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    user_name: Optional[str] = Field(None, max_length=100)


@router.post("/classify")
async def classify_photo(
    body: ClassifyRequest,
    user: Any = Depends(get_current_user),
):
    """
    AI hazard classification pipeline.
    Sends photo to Cloud Vision, maps labels to hazard type/severity/department.
    Requires a valid Supabase JWT token (Authorization: Bearer <token>).
    """
    if not body.photo_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="photo_url must be a valid HTTP/HTTPS URL")

    from app.core.auth import get_current_user_id
    user_name = body.user_name or user.get("email", "Anonymous").split("@")[0]

    result = await run_pipeline(
        photo_url=body.photo_url,
        lat=body.lat,
        lng=body.lng,
        user_name=user_name,
    )
    return result
