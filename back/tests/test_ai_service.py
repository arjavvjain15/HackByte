from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai.pipeline import build_fallback_prompt, build_hazard_classification_prompt, load_classification_schema
from app.services.ai import ensure_classification_result


def test_classification_result_adds_default_resources():
    result = ensure_classification_result(
        {
            "hazard_type": "illegal_dumping",
            "severity": "high",
            "department": "Municipal Sanitation",
            "summary": "Trash pile detected.",
            "complaint_letter": "Formal complaint text.",
        }
    )

    assert result.resources.workers >= 1
    assert result.resources.priority == "high"
    assert result.resources.vehicles
    assert isinstance(result.resources.estimated_time, str)


def test_classification_result_keeps_model_resources():
    result = ensure_classification_result(
        {
            "hazard_type": "blocked_drain",
            "severity": "medium",
            "department": "Drainage Authority",
            "summary": "Drain blockage detected.",
            "complaint_letter": "Formal complaint text.",
            "resources": {
                "workers": 5,
                "vehicles": ["drain-cleaning truck", "pickup van"],
                "estimated_time": "6 hours",
                "priority": "medium",
            },
            "confidence": "low",
        }
    )

    assert result.resources.workers == 5
    assert result.resources.vehicles == ["drain-cleaning truck", "pickup van"]
    assert result.resources.estimated_time == "6 hours"
    assert result.confidence == "low"


def test_ai_pipeline_loads_schema_and_prompt_builders():
    schema = load_classification_schema()
    prompt = build_hazard_classification_prompt(
        labels=["waste", "plastic bottle"],
        lat=12.34,
        lng=56.78,
        current_datetime="2026-04-04T10:00:00Z",
        reporter_name="Alex",
        photo_url="https://example.com/photo.jpg",
    )
    fallback_prompt = build_fallback_prompt(lat=12.34, lng=56.78)

    assert schema["title"] == "EcoSnapClassificationResult"
    assert "resources" in schema["properties"]
    assert "plastic bottle" in prompt
    assert "Alex" in prompt
    assert "https://example.com/photo.jpg" in prompt
    assert '"confidence": "low"' in fallback_prompt
