from io import BytesIO

import pdfplumber


def extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract plain text from an uploaded PDF.
    """
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        parts = []
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            parts.append(page_text)
        return "\n\n".join(parts)

