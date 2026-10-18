from pathlib import Path

import pytest

from app.services.document_parser import DocumentParseError, validate_upload


def test_rejects_unsupported_and_empty_files():
    with pytest.raises(DocumentParseError, match="Unsupported"):
        validate_upload("notes.exe", "application/octet-stream", b"data", 10_000)
    with pytest.raises(DocumentParseError, match="empty"):
        validate_upload("notes.pdf", "application/pdf", b"", 10_000)


def test_accepts_pdf_signature_and_size_limit():
    assert validate_upload("requirements.pdf", "application/pdf", b"%PDF-1.7 demo", 10_000) == ".pdf"
    with pytest.raises(DocumentParseError, match="exceeds"):
        validate_upload("requirements.pdf", "application/pdf", b"%PDF-" + b"x" * 20, 10)
