import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

import anyio
from fastapi import UploadFile

ALLOWED_DOCUMENT_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
}
READ_CHUNK_SIZE = 64 * 1024


class InvalidDocumentError(ValueError):
    """Raised when an uploaded file is not an approved career document."""


class DocumentTooLargeError(ValueError):
    """Raised when an uploaded document exceeds the configured size limit."""


@dataclass(frozen=True)
class StoredDocument:
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    storage_key: str


class LocalDocumentStorage:
    """Validate and persist document bytes under an application-owned directory."""

    def __init__(self, directory: Path, max_size_bytes: int) -> None:
        self.directory = directory
        self.max_size_bytes = max_size_bytes

    async def save(self, upload: UploadFile) -> StoredDocument:
        original_filename = Path(upload.filename or "").name
        suffix = Path(original_filename).suffix.lower()
        content_type = upload.content_type or ""

        if not original_filename or suffix not in ALLOWED_DOCUMENT_TYPES:
            raise InvalidDocumentError("Upload a PDF, DOCX, or plain-text file.")
        if content_type != ALLOWED_DOCUMENT_TYPES[suffix]:
            raise InvalidDocumentError(
                "The file type does not match its PDF, DOCX, or TXT extension."
            )

        self.directory.mkdir(parents=True, exist_ok=True)
        storage_key = f"{uuid.uuid4()}{suffix}"
        destination = self.directory / storage_key
        digest = hashlib.sha256()
        size_bytes = 0

        try:
            async with await anyio.open_file(destination, "wb") as stored_file:
                while chunk := await upload.read(READ_CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        raise DocumentTooLargeError(
                            "The document exceeds the 5 MB upload limit."
                        )
                    digest.update(chunk)
                    await stored_file.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

        return StoredDocument(
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            storage_key=storage_key,
        )

    def delete(self, storage_key: str) -> None:
        (self.directory / storage_key).unlink(missing_ok=True)
