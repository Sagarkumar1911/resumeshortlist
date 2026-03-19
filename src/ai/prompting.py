import json
from typing import Any, Dict

from src.ai.schema import SCREENING_JSON_SCHEMA


SYSTEM_CONTEXT = (
    "You are an expert HR recruiter and resume screening assistant. "
    "Given a Job Description and a candidate Resume, evaluate the fit. "
    "Return ONLY a single valid JSON object that matches the required schema. "
    "Do not include any markdown, commentary, or extra keys."
)


def build_screening_prompt(job_description: str, resume_text: str) -> str:
    schema_str = json.dumps(SCREENING_JSON_SCHEMA, ensure_ascii=False)
    return (
        "Job Description:\n"
        f"{job_description}\n\n"
        "Candidate Resume:\n"
        f"{resume_text}\n\n"
        "Return a JSON object matching this schema (exactly):\n"
        f"{schema_str}\n\n"
        "Rules:\n"
        "- overall_score must be a number from 0 to 100.\n"
        "- strengths and gaps should be arrays of short strings.\n"
        "- recommendation must be one of Hire/Consider/No.\n"
        "- evidence should contain 3-5 objects mapping JD requirements to resume evidence.\n"
    )


def coerce_types(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Coerce a few common model mistakes before schema validation.
    """
    if "overall_score" in obj:
        try:
            obj["overall_score"] = float(obj["overall_score"])
        except Exception:
            pass
    if "strengths" in obj and obj["strengths"] is None:
        obj["strengths"] = []
    if "gaps" in obj and obj["gaps"] is None:
        obj["gaps"] = []
    if "evidence" in obj and obj["evidence"] is None:
        obj["evidence"] = []
    if "candidate_name" in obj and obj["candidate_name"] is None:
        obj["candidate_name"] = ""
    if "reasoning_summary" in obj and obj["reasoning_summary"] is None:
        obj["reasoning_summary"] = ""
    return obj

