import asyncio
import json
from pathlib import Path
import sys
from typing import Optional
from fastapi import HTTPException
import httpx

from app.core.config import get_env_alias

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.pipeline import normalize_classification_result


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


async def _request_with_retry(
    method: str,
    url: str,
    *,
    json_body: dict,
    max_attempts: int = 3,
    timeout: int = 30,
) -> httpx.Response:
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, json=json_body)
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt < max_attempts:
                    await asyncio.sleep(0.5 * attempt)
                    continue
            return response
        except Exception as exc:
            last_exc = exc
            if attempt < max_attempts:
                await asyncio.sleep(0.5 * attempt)
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Request failed after retries")


async def call_cloud_vision(photo_url: str) -> list[dict]:
    api_key = get_env_alias(["GOOGLE_CLOUD_VISION_API_KEY", "CLOUD_VISION_API_KEY", "Cloud_Vision"])
    endpoint = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    payload = {
        "requests": [
            {
                "image": {"source": {"imageUri": photo_url}},
                "features": [{"type": "LABEL_DETECTION", "maxResults": 10}],
            }
        ]
    }

    response = await _request_with_retry("POST", endpoint, json_body=payload, timeout=30)
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Vision API error: {response.status_code} {response.text}",
        )
    data = response.json()

    responses = data.get("responses", [])
    if not responses:
        return []
    return responses[0].get("labelAnnotations", []) or []


async def call_gemini(prompt: str) -> dict:
    api_key = get_env_alias(["GEMINI_API_KEY", "Gemini"])
    endpoint = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    response = await _request_with_retry("POST", endpoint, json_body=payload, timeout=45)
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API error: {response.status_code} {response.text}",
        )
    data = response.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise HTTPException(status_code=502, detail="Gemini API returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise HTTPException(status_code=502, detail="Gemini API returned no content")

    text = parts[0].get("text", "")
    if not text:
        raise HTTPException(status_code=502, detail="Gemini API returned empty text")
    try:
        return _extract_json(text)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini output was not valid JSON: {exc}",
        ) from exc

def ensure_classification_result(payload: dict):
    try:
        return normalize_classification_result(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Classification schema validation failed: {exc}") from exc
