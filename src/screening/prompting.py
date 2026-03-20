from __future__ import annotations

from typing import Type

from .schemas import ResumeScreeningResult


SYSTEM_CONTEXT = (
    "You are an expert HR recruiter and resume screener. "
    "Given a job description and a single candidate resume, "
    "produce an objective assessment with scores, strengths, gaps, and recommendation. "
    "Be specific and grounded in the resume content."
)


SCHEMA_HINT = (
    "Return a single JSON object with exactly these keys:\n"
    "- candidate_name: string\n"
    "- overall_score: number between 0 and 100\n"
    '- recommendation: one of "Hire", "Consider", "No"\n'
    "- strengths: array of short strings\n"
    "- gaps: array of short strings\n"
    "- reasoning_summary: string (max 2 sentences)\n"
    "- evidence: array of 3-5 objects, each with:\n"
    "  - jd_requirement: string\n"
    "  - resume_evidence: string\n"
    "No extra keys."
)


def build_resume_screening_prompt(
    *,
    job_description: str,
    resume_text: str,
    output_schema_model: Type[ResumeScreeningResult] = ResumeScreeningResult,
) -> str:
    return f"""
{SYSTEM_CONTEXT}

Return ONLY valid JSON (no markdown, no backticks, no commentary) that matches this schema hint:
{SCHEMA_HINT}

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


def build_strict_resume_chat_prompt(
    *,
    job_description: str,
    resume_text: str,
    question: str,
) -> str:
    """
    Strict prompt for the recruiter chatbot.

    The assistant must ground every factual claim in the provided `resume_text`.
    """
    return f"""
You are an expert recruiter assistant. You will be given a single candidate's resume text.

CRITICAL RULES:
1) Use ONLY the information contained in the provided RESUME TEXT.
2) Do NOT guess, infer, or use outside knowledge.
3) If the RESUME TEXT does not contain the answer, reply exactly: "Not found in resume."
4) When you do answer, include 1-3 short supporting excerpts (verbatim) from the RESUME TEXT.
5) Output plain text only. No JSON.

JOB DESCRIPTION (context only; do not invent facts from it):
{job_description}

RESUME TEXT (your only source of facts):
---
{resume_text}
---

RECRUITER QUESTION:
{question}
""".strip()

