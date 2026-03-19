from __future__ import annotations

import json
from typing import Type

from .schemas import ResumeScreeningResult


SYSTEM_CONTEXT = (
    "You are an expert HR recruiter and resume screener. "
    "Given a job description and a single candidate resume, "
    "produce an objective assessment with scores, strengths, gaps, and recommendation. "
    "Be specific and grounded in the resume content."
)


def build_resume_screening_prompt(
    *,
    job_description: str,
    resume_text: str,
    output_schema_model: Type[ResumeScreeningResult] = ResumeScreeningResult,
) -> str:
    schema = output_schema_model.model_json_schema()
    schema_str = json.dumps(schema, ensure_ascii=False)

    return f"""
{SYSTEM_CONTEXT}

Return ONLY valid JSON (no markdown, no backticks, no commentary) that matches this JSON schema:
{schema_str}

Rules:
- overall_score must be a number from 0 to 100.
- recommendation must be one of: "Hire", "Consider", "No".
- strengths and gaps must be arrays of short strings.
- evidence must be an array where each item connects a job requirement to resume evidence.
- candidate_name is best-effort; if unknown, return empty string.

Job Description:
{job_description}

Candidate Resume:
{resume_text}
""".strip()

