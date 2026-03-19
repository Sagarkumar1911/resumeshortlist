from typing import Any, Dict, List

from jsonschema import Draft7Validator


RECOMMENDATIONS: List[str] = ["Hire", "Consider", "No"]


SCREENING_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "candidate_name": {"type": "string"},
        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "gaps": {"type": "array", "items": {"type": "string"}},
        "recommendation": {"type": "string", "enum": RECOMMENDATIONS},
        "reasoning_summary": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_requirement": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                },
                "required": ["jd_requirement", "resume_evidence"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "candidate_name",
        "overall_score",
        "strengths",
        "gaps",
        "recommendation",
        "reasoning_summary",
        "evidence",
    ],
    "additionalProperties": False,
}


_validator = Draft7Validator(SCREENING_JSON_SCHEMA)


def validate_screening_json(obj: Dict[str, Any]) -> None:
    errors = sorted(_validator.iter_errors(obj), key=lambda e: e.path)
    if errors:
        # Raise the first error for a cleaner failure message.
        raise ValueError(str(errors[0].message))

