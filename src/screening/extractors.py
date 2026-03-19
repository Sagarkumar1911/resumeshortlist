import io
import os
from typing import BinaryIO

import pdfplumber
from docx import Document


def _read_bytes(file_obj: BinaryIO) -> bytes:
    # Works for Streamlit's UploadedFile as well as standard file objects.
    if hasattr(file_obj, "getvalue"):
        return file_obj.getvalue()
    return file_obj.read()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = []
        for page in pdf.pages:
            txt = page.extract_text() or ""
            pages.append(txt)
        return "\n".join(pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras).strip()


def extract_text_from_upload(uploaded_file) -> str:
    """
    Extract raw text from a Streamlit UploadedFile.

    Returns an empty string if extraction fails.
    """
    file_name = getattr(uploaded_file, "name", "") or ""
    ext = os.path.splitext(file_name)[1].lower()

    try:
        file_bytes = _read_bytes(uploaded_file)
        if ext == ".pdf":
            return extract_text_from_pdf(file_bytes)
        if ext == ".docx":
            return extract_text_from_docx(file_bytes)
        return ""
    except Exception:
        return ""

