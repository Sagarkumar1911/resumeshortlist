import re


def normalize_text(text: str) -> str:
    """
    Normalize whitespace to reduce prompt noise from extracted documents.
    """
    if not text:
        return ""

    # Collapse whitespace while preserving newlines as paragraph boundaries.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

