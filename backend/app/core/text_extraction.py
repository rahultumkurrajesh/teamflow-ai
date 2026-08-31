"""Text extraction from document files (PDF, TXT, etc.)."""
import io

import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file.

    Args:
        file_bytes: The PDF file contents as bytes.

    Returns:
        Extracted text as a single string.
    """
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from a TXT file.

    Args:
        file_bytes: The TXT file contents as bytes.

    Returns:
        Extracted text as a string.
    """
    return file_bytes.decode("utf-8", errors="replace")


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Extract text from a file based on its content type.

    Args:
        file_bytes: The file contents as bytes.
        content_type: The MIME type of the file (e.g. 'application/pdf').

    Returns:
        Extracted text.

    Raises:
        ValueError: If the content type is not supported.
    """
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)
    elif content_type in ("text/plain", "text/plain; charset=utf-8"):
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
