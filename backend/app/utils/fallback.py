"""
EcoSnap — Fallback Responses & Keyword Mapping Rules
Used when AI pipeline fails or returns low-confidence results.
"""
from datetime import datetime

# ── Hazard keyword → hazard_type mapping ───────────────────────────────────────
KEYWORD_HAZARD_MAP: dict[str, str] = {
    # Illegal dumping
    "trash": "illegal_dumping",
    "garbage": "illegal_dumping",
    "waste": "illegal_dumping",
    "litter": "illegal_dumping",
    "dump": "illegal_dumping",
    "refuse": "illegal_dumping",
    "rubbish": "illegal_dumping",
    "debris": "illegal_dumping",
    # Oil spill
    "oil": "oil_spill",
    "petroleum": "oil_spill",
    "fuel": "oil_spill",
    "spill": "oil_spill",
    "slick": "oil_spill",
    # E-waste
    "electronics": "e_waste",
    "electronic": "e_waste",
    "computer": "e_waste",
    "battery": "e_waste",
    "circuit": "e_waste",
    "appliance": "e_waste",
    "device": "e_waste",
    # Water pollution
    "water": "water_pollution",
    "sewage": "water_pollution",
    "effluent": "water_pollution",
    "contamination": "water_pollution",
    "algae": "water_pollution",
    "discharge": "water_pollution",
    # Blocked drain
    "drain": "blocked_drain",
    "clog": "blocked_drain",
    "flood": "blocked_drain",
    "gutter": "blocked_drain",
    "manhole": "blocked_drain",
    "sewer": "blocked_drain",
    # Air pollution
    "smoke": "air_pollution",
    "smog": "air_pollution",
    "fumes": "air_pollution",
    "exhaust": "air_pollution",
    "chimney": "air_pollution",
    "burning": "air_pollution",
    "fire": "air_pollution",
}

# ── Hazard type → department mapping ──────────────────────────────────────────
DEPARTMENT_MAP: dict[str, str] = {
    "illegal_dumping": "Municipal Sanitation Department",
    "oil_spill": "Environmental Protection Agency (EPA)",
    "e_waste": "Municipal Sanitation Department",
    "water_pollution": "Water & Sewage Authority",
    "blocked_drain": "Drainage & Flood Control Authority",
    "air_pollution": "Environmental Protection Agency (EPA)",
    "other": "Municipal Authority",
}

# ── Severity rules ─────────────────────────────────────────────────────────────
SEVERITY_KEYWORDS: dict[str, list[str]] = {
    "high": ["sewage", "oil", "toxic", "chemical", "fire", "smoke", "overflow", "contamination"],
    "low": ["litter", "minor", "small", "single", "paper"],
}


def infer_hazard_from_labels(labels: list[str]) -> str | None:
    """
    Try to map Vision API labels to a hazard type using keyword rules.
    Returns the first match found, or None if no match.
    """
    for label in labels:
        lower = label.lower()
        for keyword, hazard in KEYWORD_HAZARD_MAP.items():
            if keyword in lower:
                return hazard
    return None


def infer_severity_from_labels(labels: list[str]) -> str:
    """
    Guess severity from Vision labels using keyword heuristics.
    """
    labels_lower = " ".join(labels).lower()
    for severity, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in labels_lower for kw in keywords):
            return severity
    return "medium"


# ── Safe default response ─────────────────────────────────────────────────────
# Always returned when all AI calls fail — guarantees no crash
SAFE_DEFAULT_RESPONSE: dict = {
    "hazard_type": "other",
    "severity": "medium",
    "department": "Municipal Authority",
    "summary": "An environmental hazard has been detected. Manual review required.",
    "complaint_letter": (
        f"To: Municipal Authority\n"
        f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
        f"Subject: Environmental Hazard Report\n\n"
        "Dear Officer,\n\n"
        "I am writing to formally report an environmental hazard observed at the "
        "location indicated by the attached GPS coordinates. The AI classification "
        "system was unable to determine the exact hazard type, but the photo evidence "
        "clearly indicates an issue requiring prompt attention.\n\n"
        "I kindly request that an inspector be dispatched to assess and resolve this "
        "situation at the earliest convenience.\n\n"
        "Thank you for your attention to this matter.\n\n"
        "Regards,\nEcoSnap Reporter"
    ),
    "confidence": "low",
}
