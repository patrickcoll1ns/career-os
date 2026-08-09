import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.integrations.document_storage import (
    DocumentTooLargeError,
    InvalidDocumentError,
    LocalDocumentStorage,
)


def make_upload(filename: str, content_type: str, content: bytes) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def test_storage_saves_an_approved_document(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload("resume.txt", "text/plain", b"Backend engineer")

    stored = asyncio.run(storage.save(upload))

    assert stored.original_filename == "resume.txt"
    assert stored.size_bytes == 16
    assert len(stored.sha256) == 64
    assert (tmp_path / stored.storage_key).read_bytes() == b"Backend engineer"


def test_storage_rejects_an_unsupported_file_type(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload("resume.exe", "application/octet-stream", b"not allowed")

    with pytest.raises(InvalidDocumentError):
        asyncio.run(storage.save(upload))


def test_storage_rejects_a_mismatched_content_type(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload("resume.pdf", "text/plain", b"not a pdf")

    with pytest.raises(InvalidDocumentError):
        asyncio.run(storage.save(upload))


def test_storage_removes_a_file_that_exceeds_the_limit(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=4)
    upload = make_upload("resume.txt", "text/plain", b"too large")

    with pytest.raises(DocumentTooLargeError):
        asyncio.run(storage.save(upload))

    assert list(tmp_path.iterdir()) == []
