import asyncio
import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import UploadFile
from pydantic import SecretStr
from starlette.datastructures import Headers

from app.integrations.document_storage import (
    DocumentNotStoredError,
    DocumentTooLargeError,
    InvalidDocumentError,
    LocalDocumentStorage,
    S3DocumentStorage,
    build_document_storage,
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


def test_storage_rejects_an_empty_file(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload("resume.txt", "text/plain", b"")

    with pytest.raises(InvalidDocumentError, match="empty"):
        asyncio.run(storage.save(upload))

    assert list(tmp_path.iterdir()) == []


def test_storage_rejects_a_spoofed_pdf(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload("resume.pdf", "application/pdf", b"not really a PDF")

    with pytest.raises(InvalidDocumentError, match="valid PDF"):
        asyncio.run(storage.save(upload))

    assert list(tmp_path.iterdir()) == []


def test_storage_rejects_a_spoofed_docx(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    upload = make_upload(
        "resume.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        b"PK but not a zip archive",
    )

    with pytest.raises(InvalidDocumentError, match="valid DOCX"):
        asyncio.run(storage.save(upload))

    assert list(tmp_path.iterdir()) == []


def test_storage_rejects_unsafe_storage_keys(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)

    with pytest.raises(InvalidDocumentError, match="storage key"):
        storage.path_for("../outside.txt")
    with pytest.raises(InvalidDocumentError, match="storage key"):
        storage.path_for("not-a-generated-id.txt")


def test_storage_reads_back_and_deletes_a_saved_document(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)
    stored = asyncio.run(
        storage.save(make_upload("resume.txt", "text/plain", b"Backend engineer"))
    )

    assert asyncio.run(storage.read(stored.storage_key)) == b"Backend engineer"

    asyncio.run(storage.delete(stored.storage_key))

    assert list(tmp_path.iterdir()) == []
    with pytest.raises(DocumentNotStoredError):
        asyncio.run(storage.read(stored.storage_key))


def test_deleting_an_absent_document_is_not_an_error(tmp_path) -> None:
    storage = LocalDocumentStorage(tmp_path, max_size_bytes=1024)

    asyncio.run(storage.delete(f"{uuid.uuid4()}.txt"))


def test_s3_storage_prefixes_and_validates_object_keys() -> None:
    storage = S3DocumentStorage(bucket="careeros", max_size_bytes=1024)
    storage_key = f"{uuid.uuid4()}.pdf"

    assert storage.object_key(storage_key) == f"documents/{storage_key}"
    with pytest.raises(InvalidDocumentError):
        storage.object_key("../../etc/passwd")


def test_the_storage_backend_follows_configuration(tmp_path) -> None:
    local = build_document_storage(
        SimpleNamespace(
            document_storage_backend="local",
            document_upload_directory=tmp_path,
            max_document_size_bytes=1024,
        )
    )
    remote = build_document_storage(
        SimpleNamespace(
            document_storage_backend="s3",
            max_document_size_bytes=1024,
            s3_bucket="careeros",
            s3_endpoint_url="https://accountid.r2.cloudflarestorage.com",
            s3_region="auto",
            s3_access_key_id=SecretStr("key"),
            s3_secret_access_key=SecretStr("secret"),
        )
    )

    assert isinstance(local, LocalDocumentStorage)
    assert isinstance(remote, S3DocumentStorage)
    assert remote.bucket == "careeros"


def test_object_storage_requires_a_bucket() -> None:
    with pytest.raises(ValueError, match="S3_BUCKET"):
        build_document_storage(
            SimpleNamespace(
                document_storage_backend="s3",
                max_document_size_bytes=1024,
                s3_bucket=None,
            )
        )
