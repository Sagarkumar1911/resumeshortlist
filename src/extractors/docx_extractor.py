from io import BytesIO
from typing import List

from docx import Document


def _paragraphs_to_text(paragraphs: List) -> str:
    lines: List[str] = []
    for p in paragraphs:
        txt = (p.text or "").strip()
        if txt:
            lines.append(txt)
    return "\n".join(lines)


def extract_docx_text(file_bytes: bytes) -> str:
    """
    Extract plain text from an uploaded DOCX.
    """
    doc = Document(BytesIO(file_bytes))
    body_text = _paragraphs_to_text(doc.paragraphs)
    return body_text

