from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from typing import Dict, Iterable, Optional

import pandas as pd
from pydantic import ValidationError

from .extractors import extract_text_from_upload
from .gemini_client import generate_gemini_text
from .llm_json_utils import parse_json_safely
from .prompting import build_resume_screening_prompt
from .schemas import Recommendation, ResumeScreeningResult
from src.utils.text_cleaning import normalize_text


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
    resume_texts: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """
    Extract text from each uploaded resume file, ask Gemini to screen it,
    parse the JSON response into a strict schema, and return a ranked DataFrame.
    """
    uploaded_files = list(files)
    if not uploaded_files:
        return pd.DataFrame()

    
    max_job_desc_chars = int(os.getenv("RESUME_SCREENING_MAX_JOB_DESC_CHARS", "4000"))
    max_resume_chars = int(os.getenv("RESUME_SCREENING_MAX_RESUME_CHARS", "25000"))
    max_pdf_pages = int(os.getenv("RESUME_SCREENING_MAX_PDF_PAGES", "8"))
    max_docx_paragraphs = int(os.getenv("RESUME_SCREENING_MAX_DOCX_PARAGRAPHS", "80"))
    max_workers = int(os.getenv("RESUME_SCREENING_MAX_WORKERS", "4"))
    max_workers = max(1, min(max_workers, len(uploaded_files)))

    job_description = normalize_text(job_description)[:max_job_desc_chars]

    
    rows: list[dict | None] = [None] * len(uploaded_files)
    pending: list[tuple[int, str, str]] = []  # (index, file_name, resume_text)

    for idx, uploaded_file in enumerate(uploaded_files):
        file_name = getattr(uploaded_file, "name", "") or "resume"
        if resume_texts is not None and file_name in resume_texts:
            resume_text = resume_texts.get(file_name, "")
        else:
            resume_text = extract_text_from_upload(
                uploaded_file,
                max_pages=max_pdf_pages,
                max_paragraphs=max_docx_paragraphs,
                max_chars=max_resume_chars,
            )
        resume_text = normalize_text(resume_text)

        if not resume_text or len(resume_text) < 30:
            rows[idx] = _result_to_row(
                file_name=file_name,
                result=_fallback_result(candidate_name=""),
            )
            continue

        
        if len(resume_text) > max_resume_chars:
            resume_text = resume_text[:max_resume_chars]

        pending.append((idx, file_name, resume_text))

    def _screen_one(*, file_name: str, resume_text: str) -> dict:
        prompt = build_resume_screening_prompt(
            job_description=job_description,
            resume_text=resume_text,
        )
        raw_text = generate_gemini_text(
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "60")),
        )

        parsed = parse_json_safely(raw_text)
        if parsed is None:
            
            try:
                parsed = json.loads(raw_text)
            except Exception:
                parsed = None

        if parsed is None:
            return _result_to_row(
                file_name=file_name,
                result=_fallback_result(candidate_name=""),
            )

        try:
            validated = ResumeScreeningResult.model_validate(parsed)
        except ValidationError:
            return _result_to_row(
                file_name=file_name,
                result=_fallback_result(candidate_name=""),
            )

        return _result_to_row(file_name=file_name, result=validated)

    # Gemini calls are the dominant latency; run them concurrently.
    if pending:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(_screen_one, file_name=file_name, resume_text=resume_text): idx
                for idx, file_name, resume_text in pending
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    rows[idx] = future.result()
                except Exception:
                    # If the worker crashed, keep the table shape stable.
                    file_name = getattr(uploaded_files[idx], "name", "") or "resume"
                    rows[idx] = _result_to_row(
                        file_name=file_name,
                        result=_fallback_result(candidate_name=""),
                    )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="OverallScore", ascending=False).reset_index(drop=True)
        df.insert(0, "Rank", df.index + 1)
    return df

