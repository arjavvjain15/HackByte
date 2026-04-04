`back/` is the primary backend.

`ai/` is the shared AI module for EcoSnap. It owns the prompt contract, schema contract, and AI-side normalization helpers used by the live backend classify pipeline.

Contents:
- `ai/prompts/hazard_classification_prompt.txt`
- `ai/prompts/fallback_prompt.txt`
- `ai/schemas/classification_result.schema.json`
- `ai/contracts.py`
- `ai/pipeline.py`

Responsibilities:
- prompt definitions for hazard classification and low-confidence fallback
- classification schema contract for AI output
- prompt builders used by `/api/classify`
- normalization of Gemini output into the required schema, including default `resources`

Source of truth:
- backend/API/runtime transport, auth, persistence: `back/`
- AI prompt + schema + normalization logic: `ai/`
