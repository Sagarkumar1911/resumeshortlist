import os
from typing import Any

from src.extractors.docx_extractor import extract_docx_text
from src.extractors.pdf_extractor import extract_pdf_text
from src.utils.text_cleaning import normalize_text


def extract_text_from_upload(upload: Any) -> str:
    """
    Extract text from a Streamlit UploadedFile.
    """
    file_name = getattr(upload, "name", "") or ""
    _, ext = os.path.splitext(file_name.lower())
    file_bytes = upload.getvalue()

    if ext == ".pdf":
        raw = extract_pdf_text(file_bytes)
    elif ext == ".docx":
        raw = extract_docx_text(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext or '<unknown>'}")

    return normalize_text(raw)

