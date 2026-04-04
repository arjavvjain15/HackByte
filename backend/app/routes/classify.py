"""
EcoSnap — POST /api/classify
Core AI pipeline endpoint. Always returns valid JSON.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.utils.validators import ClassifyRequest, ClassificationResult
from app.services.classifier import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Classification"])


@router.post("/classify", response_model=ClassificationResult)
async def classify_image(request: ClassifyRequest) -> ClassificationResult:
    """
    Run the Cloud Vision → Gemini AI pipeline on an uploaded photo.

    - Always returns a valid ClassificationResult — never crashes.
    - If AI is unavailable, returns a safe default with confidence='low'.

    Body:
        photo_url: Publicly accessible image URL (from Supabase Storage)
        lat: GPS latitude (optional, defaults to 0.0)
        lng: GPS longitude (optional, defaults to 0.0)
        user_name: Reporter's display name for the complaint letter
    """
    logger.info(f"[classify] photo_url={request.photo_url[:80]} lat={request.lat} lng={request.lng}")

    # Validate URL is non-empty (basic check — Vision API will handle the rest)
    if not request.photo_url or not request.photo_url.startswith("http"):
        logger.warning("[classify] Invalid photo_url provided. Returning safe default.")
        from app.utils.fallback import SAFE_DEFAULT_RESPONSE
        from app.utils.validators import sanitize_classification
        return sanitize_classification(SAFE_DEFAULT_RESPONSE)

    # Run the full pipeline — never raises
    result = await run_pipeline(
        photo_url=request.photo_url,
        lat=request.lat,
        lng=request.lng,
        user_name=request.user_name or "Anonymous",
    )

    return result
