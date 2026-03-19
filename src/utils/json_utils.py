import json
import re
from typing import Any, Dict


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Parse a JSON object from model output.

    Models sometimes wrap JSON in prose. This tries to recover the first {...} block.
    """
    if not text:
        raise ValueError("Empty model output; no JSON found.")

    text = text.strip()

    # Fast path: direct JSON.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Recovery: extract from the first `{` to the last `}`.
    # This tends to work better than a naive regex on nested objects.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object detected in model output.")

    candidate = text[start : end + 1]
    obj = json.loads(candidate)
    if not isinstance(obj, dict):
        raise ValueError("Parsed JSON was not an object.")
    return obj

