"""
EcoSnap — Google Cloud Vision API Service
Calls the Vision REST API using the API key (no service account JSON required).
"""
import httpx
import logging
from app.config import GOOGLE_VISION_API_KEY

logger = logging.getLogger(__name__)

VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
LABEL_CONFIDENCE_THRESHOLD = 0.70
MAX_RESULTS = 20
TIMEOUT_SECONDS = 10.0


class VisionError(Exception):
    """Raised when Cloud Vision API call fails."""
    pass


async def analyze_image(photo_url: str) -> list[str]:
    """
    Sends a photo URL to Google Cloud Vision LABEL_DETECTION.
    Returns a list of label description strings with confidence > 0.70.
    Raises VisionError on any failure.

    Args:
        photo_url: Publicly accessible URL of the image.

    Returns:
        List of label strings, e.g. ["trash", "garbage", "waste container"]
    """
    if not GOOGLE_VISION_API_KEY:
        raise VisionError("GOOGLE_VISION_API_KEY is not configured.")

    payload = {
        "requests": [
            {
                "image": {"source": {"imageUri": photo_url}},
                "features": [
                    {"type": "LABEL_DETECTION", "maxResults": MAX_RESULTS}
                ],
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(
                VISION_API_URL,
                params={"key": GOOGLE_VISION_API_KEY},
                json=payload,
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise VisionError("Cloud Vision API timed out after 10 seconds.")
    except httpx.HTTPStatusError as e:
        raise VisionError(f"Cloud Vision API returned HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise VisionError(f"Unexpected error calling Cloud Vision: {str(e)}")

    data = response.json()

    # Check for API-level errors
    responses = data.get("responses", [])
    if not responses:
        raise VisionError("Cloud Vision returned an empty responses array.")

    first = responses[0]
    if "error" in first:
        err = first["error"]
        raise VisionError(f"Cloud Vision error {err.get('code')}: {err.get('message')}")

    # Extract high-confidence labels
    annotations = first.get("labelAnnotations", [])
    labels = [
        ann["description"]
        for ann in annotations
        if ann.get("score", 0) >= LABEL_CONFIDENCE_THRESHOLD
    ]

    logger.info(f"Cloud Vision returned {len(annotations)} labels, {len(labels)} above threshold.")
    return labels
