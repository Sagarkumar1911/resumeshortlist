from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from src.ai.gemini_client import analyze_resume_with_gemini
from src.screening.extractors import extract_text_from_upload


def _results_to_row(file_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    strengths = payload.get("strengths", []) or []
    gaps = payload.get("gaps", []) or []
    evidence = payload.get("evidence", []) or []

    return {
        "file_name": file_name,
        "candidate_name": payload.get("candidate_name", "") or "",
        "overall_score": float(payload.get("overall_score", 0) or 0),
        "recommendation": payload.get("recommendation", "") or "",
        "strengths": " | ".join(strengths),
        "gaps": " | ".join(gaps),
        "reasoning_summary": payload.get("reasoning_summary", "") or "",
        "evidence_count": len(evidence),
    }


def screen_batch(
    *,
    job_description: str,
    files: List[Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> pd.DataFrame:
    """
    Batch-screen a list of Streamlit UploadedFile objects.
    """
    job_description = (job_description or "").strip()
    if not job_description:
        return pd.DataFrame()

    results: List[Dict[str, Any]] = []

    for upload in files:
        file_name = getattr(upload, "name", "uploaded_resume")
        try:
            resume_text = extract_text_from_upload(upload)
            if not resume_text.strip():
                raise ValueError("No extractable text found in document.")

            payload = analyze_resume_with_gemini(
                job_description=job_description,
                resume_text=resume_text,
                api_key=api_key,
                model_name=model_name,
            )
            results.append(_results_to_row(file_name, payload))
        except Exception as e:
            results.append(
                {
                    "file_name": file_name,
                    "candidate_name": "",
                    "overall_score": 0.0,
                    "recommendation": "No",
                    "strengths": "",
                    "gaps": "",
                    "reasoning_summary": f"Error: {e}",
                    "evidence_count": 0,
                }
            )

    df = pd.DataFrame(results)
    if not df.empty and "overall_score" in df.columns:
        df = df.sort_values(by="overall_score", ascending=False).reset_index(drop=True)
    return df

