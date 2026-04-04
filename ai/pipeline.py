import json
from pathlib import Path

from .contracts import ClassificationResult


ROOT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT_DIR / "prompts"
SCHEMAS_DIR = ROOT_DIR / "schemas"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def load_classification_schema() -> dict:
    path = SCHEMAS_DIR / "classification_result.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Classification schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_hazard_classification_prompt(
    *,
    labels: list[str],
    lat: float,
    lng: float,
    current_datetime: str,
    reporter_name: str,
    photo_url: str,
) -> str:
    return load_prompt("hazard_classification_prompt.txt").format(
        labels=labels,
        lat=lat,
        lng=lng,
        datetime=current_datetime,
        name=reporter_name,
        photo_url=photo_url,
    )


def build_fallback_prompt(*, lat: float, lng: float) -> str:
    return load_prompt("fallback_prompt.txt").format(
        lat=lat,
        lng=lng,
    )


def _default_resources(hazard_type: str, severity: str) -> dict:
    severity_defaults = {
        "high": {"workers": 4, "estimated_time": "4-8 hours", "priority": "high"},
        "medium": {"workers": 3, "estimated_time": "2-4 hours", "priority": "medium"},
        "low": {"workers": 2, "estimated_time": "1-2 hours", "priority": "low"},
    }
    vehicles_map = {
        "illegal_dumping": ["garbage truck", "pickup van"],
        "oil_spill": ["containment van", "cleanup truck"],
        "e_waste": ["collection truck"],
        "water_pollution": ["inspection vehicle", "water tanker"],
        "blocked_drain": ["drain-cleaning truck"],
        "air_pollution": ["inspection vehicle"],
        "other": ["utility vehicle"],
    }
    base = severity_defaults.get(severity or "medium", severity_defaults["medium"]).copy()
    base["vehicles"] = vehicles_map.get(hazard_type or "other", ["utility vehicle"])
    return base


def normalize_classification_result(payload: dict) -> ClassificationResult:
    hazard_type = payload.get("hazard_type") or "other"
    severity = payload.get("severity") or "medium"
    resources = payload.get("resources") or {}
    default_resources = _default_resources(hazard_type, severity)

    normalized = {
        "hazard_type": hazard_type,
        "severity": severity,
        "department": payload.get("department") or "Public Works",
        "summary": payload.get("summary") or "Hazard identified from uploaded photo.",
        "complaint_letter": payload.get("complaint_letter") or "Complaint letter could not be generated.",
        "confidence": payload.get("confidence"),
        "resources": {
            "workers": resources.get("workers") or default_resources["workers"],
            "vehicles": resources.get("vehicles") or default_resources["vehicles"],
            "estimated_time": resources.get("estimated_time") or default_resources["estimated_time"],
            "priority": resources.get("priority") or default_resources["priority"],
        },
    }
    return ClassificationResult.model_validate(normalized)
