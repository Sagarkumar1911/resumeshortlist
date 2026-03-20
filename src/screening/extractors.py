import io
import os
from typing import BinaryIO, Optional

import pdfplumber
from docx import Document


def _read_bytes(file_obj: BinaryIO) -> bytes:
    
    if hasattr(file_obj, "getvalue"):
        return file_obj.getvalue()
    return file_obj.read()


def extract_text_from_pdf(
    file_bytes: bytes,
    *,
    max_pages: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        parts: list[str] = []
        total_chars = 0
        for i, page in enumerate(pdf.pages):
            if max_pages is not None and i >= max_pages:
                break
            txt = page.extract_text() or ""
            if not txt:
                continue
            parts.append(txt)
            total_chars += len(txt)
            if max_chars is not None and total_chars >= max_chars:
                break
        return "\n".join(parts).strip()


def extract_text_from_docx(
    file_bytes: bytes,
    *,
    max_paragraphs: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> str:
    doc = Document(io.BytesIO(file_bytes))
    parts: list[str] = []
    total_chars = 0
    for i, p in enumerate(doc.paragraphs):
        if max_paragraphs is not None and i >= max_paragraphs:
            break
        txt = (p.text or "").strip()
        if not txt:
            continue
        parts.append(txt)
        total_chars += len(txt)
        if max_chars is not None and total_chars >= max_chars:
            break
    return "\n".join(parts).strip()


def extract_text_from_upload(
    uploaded_file,
    *,
    max_pages: Optional[int] = None,
    max_paragraphs: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> str:
    """
    Extract raw text from a Streamlit UploadedFile.

    Returns an empty string if extraction fails.
    """
    file_name = getattr(uploaded_file, "name", "") or ""
    ext = os.path.splitext(file_name)[1].lower()

    try:
        file_bytes = _read_bytes(uploaded_file)
        if ext == ".pdf":
            return extract_text_from_pdf(file_bytes, max_pages=max_pages, max_chars=max_chars)
        if ext == ".docx":
            return extract_text_from_docx(
                file_bytes,
                max_paragraphs=max_paragraphs,
                max_chars=max_chars,
            )
        return ""
    except Exception:
        return ""

