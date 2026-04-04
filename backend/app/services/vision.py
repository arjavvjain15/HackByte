"""
EcoSnap — Google Cloud Vision API Service
Calls the Vision REST API using the API key (no service account JSON required).
Downloads the image via httpx first (handles authenticated Supabase Storage URLs),
then sends it as base64 content to Vision — so no "URL not accessible" errors.
"""
import httpx
import base64
import logging
from app.config import GOOGLE_VISION_API_KEY, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
LABEL_CONFIDENCE_THRESHOLD = 0.55   # Lowered slightly so more labels pass through
MAX_RESULTS = 20
TIMEOUT_SECONDS = 20.0


class VisionError(Exception):
    """Raised when Cloud Vision API call fails."""
    pass


async def _fetch_image_bytes(url: str) -> bytes:
    """
    Download image bytes from a URL.
    Automatically adds Supabase service-key auth if the URL is a Supabase Storage URL.
    """
    headers = {}
    if "supabase.co/storage" in url and SUPABASE_SERVICE_KEY:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        resp = await client.get(url, headers=headers, follow_redirects=True)
        resp.raise_for_status()
        return resp.content


async def analyze_image(photo_url: str) -> list[str]:
    """
    Downloads the image, then sends it to Google Cloud Vision LABEL_DETECTION as base64.
    Returns a list of label description strings with confidence >= threshold.
    Raises VisionError on any failure.
    """
    if not GOOGLE_VISION_API_KEY:
        raise VisionError("GOOGLE_VISION_API_KEY is not configured.")

    # ── Download image ────────────────────────────────────────────────────────
    try:
        image_bytes = await _fetch_image_bytes(photo_url)
    except Exception as e:
        raise VisionError(f"Failed to download image from URL: {e}")

    if not image_bytes:
        raise VisionError("Downloaded image is empty.")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    logger.info(f"Downloaded image ({len(image_bytes)} bytes), sending to Cloud Vision as base64.")

    # ── Call Vision API ───────────────────────────────────────────────────────
    payload = {
        "requests": [
            {
                "image": {"content": image_b64},          # base64 content, NOT imageUri
                "features": [
                    {"type": "LABEL_DETECTION",    "maxResults": MAX_RESULTS},
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
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
        raise VisionError("Cloud Vision API timed out.")
    except httpx.HTTPStatusError as e:
        raise VisionError(f"Cloud Vision API returned HTTP {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise VisionError(f"Unexpected error calling Cloud Vision: {str(e)}")

    data = response.json()

    # ── Parse response ────────────────────────────────────────────────────────
    responses = data.get("responses", [])
    if not responses:
        raise VisionError("Cloud Vision returned an empty responses array.")

    first = responses[0]
    if "error" in first:
        err = first["error"]
        raise VisionError(f"Cloud Vision error {err.get('code')}: {err.get('message')}")

    # Combine label annotations + object localizations for richer coverage
    annotations = first.get("labelAnnotations", [])
    objects     = first.get("localizedObjectAnnotations", [])

    labels = [
        ann["description"]
        for ann in annotations
        if ann.get("score", 0) >= LABEL_CONFIDENCE_THRESHOLD
    ]

    # Append object names (usually high-precision — include all objects)
    object_names = [obj["name"] for obj in objects if obj.get("score", 0) >= 0.5]
    for name in object_names:
        if name not in labels:
            labels.append(name)

    logger.info(
        f"Cloud Vision: {len(annotations)} label annotations, "
        f"{len(objects)} objects → {len(labels)} labels above threshold: {labels}"
    )
    return labels
