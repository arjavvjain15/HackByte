from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from typing import Any

from app.core.auth import get_current_user
from app.models.schemas import ClassifyRequest
from app.services.ai import call_cloud_vision, call_gemini

router = APIRouter(prefix="/api", tags=["classify"])


@router.post("/classify")
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
        prompt = (
            "You are an environmental hazard classification AI for a civic reporting platform.\n\n"
            "I will give you a list of object labels detected in a photo by Google Cloud Vision.\n\n"
            "Your task:\n"
            "1. Classify the hazard into exactly one of: illegal_dumping, oil_spill, e_waste, "
            "water_pollution, blocked_drain, air_pollution, other\n"
            "2. Assign severity: high, medium, or low\n"
            "3. Identify the responsible department: Municipal Sanitation, EPA, Public Works, "
            "Parks Department, or Drainage Authority\n"
            "4. Write a formal 3-paragraph complaint letter addressed to that department\n\n"
            f"Labels detected: {labels}\n"
            f"Location: lat {payload.lat}, lng {payload.lng}\n"
            f"Date and time: {now_iso}\n"
            f"Reporter name: {reporter_name}\n"
            f"Photo URL: {payload.photo_url}\n\n"
            "Respond ONLY with valid JSON. No markdown, no explanation, no preamble.\n\n"
            "{\n"
            '  "hazard_type": "...",\n'
            '  "severity": "...",\n'
            '  "department": "...",\n'
            '  "summary": "One sentence describing the hazard",\n'
            '  "complaint_letter": "Full formal letter text here"\n'
            "}\n"
        )
    else:
        prompt = (
            "You are an environmental hazard classifier.\n\n"
            "Google Cloud Vision could not detect clear labels in this photo "
            "(all confidence scores below 0.70).\n\n"
            "Based only on the context - location: lat "
            f"{payload.lat}, lng {payload.lng}, submitted via an environmental reporting app - "
            "make a best-guess classification.\n\n"
            "Return the same JSON schema as above, but set \"confidence\": \"low\" in the response.\n"
        )

    result = await call_gemini(prompt)
    return {"labels": labels, "result": result}
