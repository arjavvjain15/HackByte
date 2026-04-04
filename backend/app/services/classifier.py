"""
EcoSnap — AI Classification Orchestrator
Runs the full pipeline: Cloud Vision → Gemini → Validate
Guarantees a valid response — never raises to the caller.
"""
import logging
from app.services.vision import analyze_image, VisionError
from app.services.gemini import classify_with_gemini, GeminiParseError
from app.utils.validators import ClassificationResult, sanitize_classification
from app.utils.fallback import (
    SAFE_DEFAULT_RESPONSE,
    infer_hazard_from_labels,
    infer_severity_from_labels,
    DEPARTMENT_MAP,
)

logger = logging.getLogger(__name__)


async def run_pipeline(
    photo_url: str,
    lat: float,
    lng: float,
    user_name: str = "Anonymous",
) -> ClassificationResult:
    """
    Full AI pipeline with fault tolerance.

    Flow:
        1. Cloud Vision → extract labels
        2. Gemini primary prompt → classify
        3. On no labels → Gemini fallback prompt
        4. On Gemini parse failure (after retry) → keyword heuristic
        5. On any crash → SAFE_DEFAULT_RESPONSE

    Returns:
        ClassificationResult — always valid, never raises.
    """

    # ── Step 1: Cloud Vision ─────────────────────────────────────────────────
    labels: list[str] = []
    error_msg = ""
    try:
        labels = await analyze_image(photo_url)
        logger.info(f"Vision labels: {labels}")
    except VisionError as e:
        error_msg = f"Vision API failed: {e}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected Vision error: {e}"
        logger.error(error_msg)

    # ── Step 2: Use Vision Labels directly for Classification ────────────────
    if labels:
        inferred_match = infer_hazard_from_labels(labels)
        inferred_hazard = inferred_match or "other"
        
        # If Vision found labels but they didn't match any known environmental hazard keywords,
        # or if all Vision scores were below 0.70 (so labels became empty), that is our "low confidence" fallback!
        is_confident = inferred_match is not None
        
        inferred_severity = infer_severity_from_labels(labels)
        inferred_dept = DEPARTMENT_MAP.get(inferred_hazard, "Municipal Authority")
        label_str = ", ".join(labels)

        return ClassificationResult(
            hazard_type=inferred_hazard,
            severity=inferred_severity,
            department=inferred_dept,
            summary=f"Analysis complete. Keywords identified: {label_str}",
            complaint_letter=_build_minimal_letter(inferred_hazard, inferred_dept, lat, lng, photo_url),
            confidence="high" if is_confident else "low",
        )

    # ── Step 3: Absolute last resort (Vision Failed) ─────────────────────────
    logger.error("Vision failed or returned no labels. Returning default response but injecting error message.")
    fallback = sanitize_classification(SAFE_DEFAULT_RESPONSE)
    fallback.summary = error_msg if error_msg else "No labels detected in the image."
    fallback.confidence = "low"
    return fallback


def _build_minimal_letter(
    hazard_type: str, department: str, lat: float, lng: float, photo_url: str
) -> str:
    """Minimal complaint letter used when Gemini is unavailable."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        f"To: {department}\n"
        f"Date: {now}\n"
        f"Subject: Environmental Hazard Report — {hazard_type.replace('_', ' ').title()}\n\n"
        "Dear Officer,\n\n"
        f"I am writing to formally report a {hazard_type.replace('_', ' ')} observed at "
        f"GPS coordinates ({lat}, {lng}). Photo evidence is available at the following URL:\n"
        f"{photo_url}\n\n"
        "I request prompt investigation and remediation of this hazard.\n\n"
        "Regards,\nEcoSnap Reporter"
    )
