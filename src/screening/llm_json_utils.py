import json


def extract_json_from_text(text: str) -> str:
    """
    Try to pull the first JSON object from an LLM response.

    If the response already is pure JSON, this returns it unchanged.
    """
    text = (text or "").strip()
    if not text:
        return ""

    # Fast path: already a JSON object.
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def parse_json_safely(text: str):
    raw = extract_json_from_text(text)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

