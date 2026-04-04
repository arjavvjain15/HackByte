from datetime import datetime, timezone
from pathlib import Path
import sys
from fastapi import APIRouter, Depends
from typing import Any

from app.core.auth import get_current_user
from app.models.schemas import ClassifyRequest, ClassificationResult
from app.services.ai import call_cloud_vision, call_gemini, ensure_classification_result

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.pipeline import build_fallback_prompt, build_hazard_classification_prompt

router = APIRouter(prefix="/api", tags=["classify"])


@router.post("/classify", response_model=ClassificationResult)
async def classify_photo(
    payload: ClassifyRequest,
    _user: Any = Depends(get_current_user),
):
    labels_raw = await call_cloud_vision(payload.photo_url)
    labels = [
        label.get("description")
        for label in labels_raw
        if label.get("score", 0) >= 0.70
    ]
    labels = [label for label in labels if label]

    reporter_name = payload.reporter_name or "Citizen"
    now_iso = datetime.now(timezone.utc).isoformat()

    if labels:
        prompt = build_hazard_classification_prompt(
            labels=labels,
            lat=payload.lat,
            lng=payload.lng,
            current_datetime=now_iso,
            reporter_name=reporter_name,
            photo_url=payload.photo_url,
        )
    else:
        prompt = build_fallback_prompt(
            lat=payload.lat,
            lng=payload.lng,
        )

    result = await call_gemini(prompt)
    if not labels and "confidence" not in result:
        result["confidence"] = "low"
    return ensure_classification_result(result)
