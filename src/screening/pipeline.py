from __future__ import annotations

import json
from typing import Iterable, Optional

import pandas as pd
from pydantic import ValidationError

from .extractors import extract_text_from_upload
from .gemini_client import generate_gemini_text
from .llm_json_utils import parse_json_safely
from .prompting import build_resume_screening_prompt
from .schemas import Recommendation, ResumeScreeningResult


def _join_list(items: list[str], sep: str = "; ") -> str:
    return sep.join([x.strip() for x in items if x and x.strip()])


def _result_to_row(*, file_name: str, result: ResumeScreeningResult) -> dict:
    evidence_flat = []
    for ev in result.evidence:
        evidence_flat.append(f"{ev.jd_requirement}: {ev.resume_evidence}")

    return {
        "FileName": file_name,
        "CandidateName": result.candidate_name,
        "OverallScore": float(result.overall_score),
        "Recommendation": result.recommendation,
        "Strengths": _join_list(result.strengths),
        "Gaps": _join_list(result.gaps),
        "ReasoningSummary": result.reasoning_summary,
        "Evidence": _join_list(evidence_flat),
    }


def _fallback_result(*, candidate_name: str, recommendation: Recommendation = "No") -> ResumeScreeningResult:
    return ResumeScreeningResult(
        candidate_name=candidate_name,
        overall_score=0,
        recommendation=recommendation,
        strengths=[],
        gaps=[],
        reasoning_summary="Could not extract or screen this resume.",
        evidence=[],
    )


def screen_resumes_batch(
    *,
    api_key: str,
    model_name: str,
    job_description: str,
    files: Iterable,
    temperature: float = 0.0,
) -> pd.DataFrame:
    """
    Extract text from each uploaded resume file, ask Gemini to screen it,
    parse the JSON response into a strict schema, and return a ranked DataFrame.
    """
    rows: list[dict] = []

    for uploaded_file in files:
        file_name = getattr(uploaded_file, "name", "") or "resume"
        resume_text = extract_text_from_upload(uploaded_file)

        if not resume_text or len(resume_text) < 30:
            rows.append(_result_to_row(file_name=file_name, result=_fallback_result(candidate_name="")))
            continue

        prompt = build_resume_screening_prompt(
            job_description=job_description,
            resume_text=resume_text,
        )

        raw_text = generate_gemini_text(
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
        )

        parsed = parse_json_safely(raw_text)
        if parsed is None:
            # Last attempt: sometimes the SDK returns already structured content; try a direct load as JSON.
            try:
                parsed = json.loads(raw_text)
            except Exception:
                parsed = None

        if parsed is None:
            rows.append(_result_to_row(file_name=file_name, result=_fallback_result(candidate_name="")))
            continue

        try:
            validated = ResumeScreeningResult.model_validate(parsed)
        except ValidationError:
            rows.append(_result_to_row(file_name=file_name, result=_fallback_result(candidate_name="")))
            continue

        rows.append(_result_to_row(file_name=file_name, result=validated))

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="OverallScore", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", df.index + 1)
    return df

