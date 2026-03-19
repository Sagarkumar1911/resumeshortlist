from __future__ import annotations

from typing import Optional

import google.generativeai as genai


def generate_gemini_text(
    *,
    api_key: str,
    model_name: str,
    prompt: str,
    temperature: float = 0.0,
    timeout_seconds: Optional[int] = 60,
) -> str:
    """
    Generate content using Gemini and return raw text.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    generation_config = {"temperature": temperature}
    # Newer SDKs support response_mime_type; use it if available.
    try:
        from google.generativeai.types import GenerationConfig  # type: ignore

        generation_config = GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )
    except Exception:
        pass

    response = model.generate_content(
        prompt,
        generation_config=generation_config,
        request_options={"timeout": timeout_seconds} if timeout_seconds else None,
    )
    return (response.text or "").strip()

