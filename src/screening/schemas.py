from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Recommendation = Literal["Hire", "Consider", "No"]


class CandidateEvidence(BaseModel):
    jd_requirement: str = Field(..., description="A single requirement pulled from the job description.")
    resume_evidence: str = Field(..., description="A quote or concise paraphrase from the resume that matches the requirement.")


class ResumeScreeningResult(BaseModel):
    candidate_name: str = Field("", description="Best effort name extracted from the resume; may be empty.")
    overall_score: float = Field(..., ge=0, le=100, description="Overall fit score on a 0-100 scale.")
    recommendation: Recommendation
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    reasoning_summary: str = Field("", description="Short HR-style explanation of the score and recommendation.")
    evidence: list[CandidateEvidence] = Field(default_factory=list)

