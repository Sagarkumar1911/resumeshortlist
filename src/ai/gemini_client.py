import os
from typing import Any, Dict, Optional

import google.generativeai as genai

from src.ai.prompting import SYSTEM_CONTEXT, build_screening_prompt, coerce_types
from src.ai.schema import validate_screening_json
from src.utils.json_utils import extract_json_object


def _generate_with_json_mime(model: Any, prompt: str, *, model_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Ask Gemini for JSON; return raw text.
    """
    # Newer Gemini SDKs support generation_config.response_mime_type.
    gen_cfg = {"response_mime_type": "application/json"}
    if model_config:
        gen_cfg.update(model_config)

    try:
        resp = model.generate_content(prompt, generation_config=gen_cfg)
        return getattr(resp, "text", None) or str(resp)
    except TypeError:
        # Fallback for SDK variations.
        resp = model.generate_content(prompt)
        return getattr(resp, "text", None) or str(resp)


def analyze_resume_with_gemini(
    *,
    job_description: str,
    resume_text: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY.")

    model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    user_prompt = build_screening_prompt(job_description=job_description, resume_text=resume_text)
    full_prompt = f"{SYSTEM_CONTEXT}\n\n{user_prompt}"

    raw = _generate_with_json_mime(model, full_prompt)
    obj = extract_json_object(raw)
    obj = coerce_types(obj)
    validate_screening_json(obj)
    return obj

