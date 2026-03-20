import json
import threading
from typing import Any, Dict, Optional
import google.generativeai as genai

_config_lock = threading.Lock()
_configured_api_key: Optional[str] = None

try:
    # Some SDK versions expose a typed GenerationConfig class.
    from google.generativeai.types import GenerationConfig as _GenerationConfig  # type: ignore
except Exception:  # pragma: no cover
    _GenerationConfig = None


def _ensure_configured(api_key: str) -> None:
    global _configured_api_key
    if _configured_api_key == api_key:
        return
    with _config_lock:
        if _configured_api_key != api_key:
            genai.configure(api_key=api_key)
            _configured_api_key = api_key


def generate_gemini_text(
    *,
    api_key: str,
    model_name: str,
    prompt: str,
    temperature: float = 0.0,
    timeout_seconds: Optional[int] = 60,
    response_mime_type: Optional[str] = "application/json",
) -> str:
    """Generate content using Gemini and return raw text."""
    _ensure_configured(api_key)
    model = genai.GenerativeModel(model_name)

    if _GenerationConfig is not None:
        if response_mime_type:
            generation_config = _GenerationConfig(
                temperature=temperature,
                response_mime_type=response_mime_type,
            )
        else:
            generation_config = _GenerationConfig(temperature=temperature)
    else:
        generation_config = {"temperature": temperature}
        if response_mime_type:
            generation_config["response_mime_type"] = response_mime_type

    kwargs: Dict[str, Any] = {"generation_config": generation_config}
    if timeout_seconds:
        kwargs["request_options"] = {"timeout": timeout_seconds}

    try:
        response = model.generate_content(prompt, **kwargs)
    except TypeError:
        # Fallback for SDK variations that don't accept certain config types.
        response = model.generate_content(prompt, generation_config=generation_config)
    return (response.text or "").strip()

def analyze_resume_with_gemini(
    *,
    job_description: str,
    resume_text: str,
    api_key: str,
    model_name: str = "gemini-1.5-flash", # or gemini-2.5-flash
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Constructs the prompt, calls Gemini, and parses the JSON result 
    specifically for the Resume Screening Task.
    """
    
    prompt = f"""
    You are an expert HR Recruitment Specialist. 
    Compare the following Resume against the Job Description provided.
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME TEXT:
    {resume_text}
    
    Output the result STRICTLY as a JSON object with these exact keys:
    - candidate_name: (string)
    - overall_score: (integer 0-100)
    - recommendation: (Strong Fit, Moderate Fit, or Not Fit)
    - strengths: (list of 2-3 strings)
    - gaps: (list of 2-3 strings)
    - reasoning_summary: (string, max 2 sentences)
    - evidence: (list of specific skills or projects found in resume)
    """

    try:
        raw_json = generate_gemini_text(
            api_key=api_key,
            model_name=model_name,
            prompt=prompt,
            temperature=temperature
        )
        
        return json.loads(raw_json)
    except Exception as e:
      
        return {
            "candidate_name": "Error Processing",
            "overall_score": 0,
            "recommendation": "N/A",
            "reasoning_summary": f"System Error: {str(e)}"
        }

