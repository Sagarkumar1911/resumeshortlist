"""
Compatibility extractors module.

The active Streamlit pipeline uses `src.screening.extractors` for
Streamlit UploadedFile support. This module re-exports a few legacy
function names so any older code paths keep working.
"""

from __future__ import annotations

import os
from typing import Union

from src.screening.extractors import (
    extract_text_from_docx,
    extract_text_from_pdf,
    extract_text_from_upload,
)


def extract_docx_text(file_bytes: bytes) -> str:
    return extract_text_from_docx(file_bytes)


def extract_pdf_text(file_bytes: bytes) -> str:
    return extract_text_from_pdf(file_bytes)


def get_text_from_file(file_name: str, file_bytes: bytes) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".docx":
        return extract_text_from_docx(file_bytes)
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    return ""


__all__ = [
    "extract_text_from_upload",
    "extract_docx_text",
    "extract_pdf_text",
    "get_text_from_file",
]