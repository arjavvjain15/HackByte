"""
EcoSnap — Gemini 2.0 Flash Service (Multimodal)
Sends images DIRECTLY to Gemini for classification — no Cloud Vision dependency.
Uses the Gemini REST API via httpx (no SDK).
"""
import json
import re
import logging
import base64
import httpx
from datetime import datetime, timezone
from app.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiParseError(Exception):
    """Raised when Gemini response cannot be parsed as valid JSON."""
    pass


# ── Prompt builders ──────────────────────────────────────────────────────────

def _build_image_prompt(
    lat: float,
    lng: float,
    photo_url: str,
    user_name: str = "Anonymous",
    labels: list[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    labels_section = ""
    if labels:
        labels_str = ", ".join(labels)
        labels_section = f"\nAdditional context — Cloud Vision labels detected: {labels_str}\n"

    return f"""You are an environmental hazard classification AI for a civic reporting platform called EcoSnap.

Analyze the image provided carefully.
{labels_section}
Your task:
1. Classify the hazard into EXACTLY ONE of: illegal_dumping, oil_spill, e_waste, water_pollution, blocked_drain, air_pollution, other
2. Assign severity: high, medium, or low
   - high = dangerous, immediate health risk
   - medium = moderate environmental issue
   - low = minor nuisance
3. Identify the responsible department from: Municipal Sanitation Department, Environmental Protection Agency (EPA), Public Works, Parks Department, Drainage & Flood Control Authority, Water & Sewage Authority, or Municipal Authority
4. Write a formal 3-paragraph complaint letter addressed to that department

Location: lat {lat}, lng {lng}
Date and time: {now}
Reporter name: {user_name}
Photo URL: {photo_url}

Respond ONLY with valid JSON. No markdown, no explanation, no preamble, no code fences.

{{
  "hazard_type": "...",
  "severity": "...",
  "department": "...",
  "summary": "One sentence describing the hazard",
  "complaint_letter": "Full formal letter text here"
}}"""


# ── JSON extractor ───────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence_match:
        text = fence_match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    obj_match = re.search(r"\{[\s\S]+\}", text)
    if obj_match:
        try:
            return json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass
    raise GeminiParseError(f"Could not extract valid JSON from Gemini response: {text[:300]}")


# ── Download image and convert to base64 ─────────────────────────────────────

def _download_image_base64(photo_url: str) -> tuple[str, str]:
    """
    Downloads an image from URL and returns (base64_data, mime_type).
    Falls back to empty strings on failure.
    """
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(photo_url)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "image/jpeg")
        # Clean up content type
        mime = content_type.split(";")[0].strip()
        if mime not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            mime = "image/jpeg"

        b64 = base64.b64encode(resp.content).decode("utf-8")
        logger.info(f"Downloaded image: {len(resp.content)} bytes, {mime}")
        return b64, mime
    except Exception as e:
        logger.warning(f"Failed to download image from {photo_url}: {e}")
        return "", ""


# ── Core Gemini REST caller ──────────────────────────────────────────────────

def _call_gemini(prompt: str, image_b64: str = "", image_mime: str = "") -> str:
    """
    Calls Gemini REST API with text prompt + optional base64 image.
    Returns raw text response. Retries on 429 rate limits.
    """
    import time

    model_name = GEMINI_MODEL or "gemini-2.0-flash"
    url = f"{GEMINI_API_BASE}/models/{model_name}:generateContent"

    # Build parts — text + optional image
    parts = []
    if image_b64 and image_mime:
        parts.append({
            "inline_data": {
                "mime_type": image_mime,
                "data": image_b64,
            }
        })
    parts.append({"text": prompt})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        },
    }

    # Retry up to 3 times on 429 rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, params={"key": GEMINI_API_KEY}, json=payload)
        except httpx.TimeoutException:
            raise GeminiParseError("Gemini API timed out after 30 seconds.")
        except Exception as e:
            raise GeminiParseError(f"Gemini HTTP error: {str(e)}")

        if response.status_code == 429:
            logger.warning(f"Gemini rate limited (429) on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                # Basic sleep during tests but it will block this thread for a couple of secs.
                time.sleep(2)
                continue
            raise GeminiParseError("Gemini rate limit exceeded.")

        if response.status_code != 200:
            raise GeminiParseError(f"Gemini API returned {response.status_code}: {response.text[:300]}")

    data = response.json()

    try:
        candidates = data.get("candidates", [])
        if not candidates:
            raise GeminiParseError(f"Gemini returned no candidates: {json.dumps(data)[:300]}")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise GeminiParseError("Gemini candidate has no parts.")
        return parts[0].get("text", "")
    except (KeyError, IndexError) as e:
        raise GeminiParseError(f"Unexpected Gemini response structure: {str(e)}")


# ── Public API ───────────────────────────────────────────────────────────────

async def classify_with_gemini(
    labels: list[str],
    lat: float,
    lng: float,
    photo_url: str,
    user_name: str = "Anonymous",
    use_fallback_prompt: bool = False,
) -> dict:
    """
    Sends the image DIRECTLY to Gemini 2.0 Flash for multimodal classification.
    Downloads the image, encodes as base64, and sends inline.

    Strategy:
    1. Download image → base64
    2. Build prompt with optional Cloud Vision labels as extra context
    3. Call Gemini with image + prompt
    4. Parse JSON — retry once on failure
    """
    # Download the image for multimodal analysis
    image_b64, image_mime = _download_image_base64(photo_url)

    prompt = _build_image_prompt(
        lat=lat, lng=lng, photo_url=photo_url,
        user_name=user_name, labels=labels if labels else None,
    )

    # ── Attempt 1 ────────────────────────────────────────────────────────────
    try:
        raw_text = _call_gemini(prompt, image_b64, image_mime)
        logger.info(f"Gemini raw response (first 200 chars): {raw_text[:200]}")
        return _extract_json(raw_text)
    except GeminiParseError:
        logger.warning("Gemini JSON parse failed on attempt 1. Retrying.")
    except Exception as e:
        logger.warning(f"Gemini API call failed on attempt 1: {e}. Retrying.")

    # ── Attempt 2 (stricter) ─────────────────────────────────────────────────
    strict_suffix = (
        "\n\nCRITICAL: Your response MUST be a single valid JSON object. "
        "Start with { and end with }. No other text whatsoever."
    )
    try:
        raw_text = _call_gemini(prompt + strict_suffix, image_b64, image_mime)
        logger.info(f"Gemini retry response (first 200 chars): {raw_text[:200]}")
        return _extract_json(raw_text)
    except GeminiParseError as e:
        logger.error(f"Gemini JSON parse failed on attempt 2: {e}")
        raise
    except Exception as e:
        logger.error(f"Gemini API call failed on attempt 2: {e}")
        raise GeminiParseError(f"Gemini API unavailable: {str(e)}")
