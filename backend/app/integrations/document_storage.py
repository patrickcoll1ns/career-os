import hashlib
import uuid
import zipfile
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
MAX_FILENAME_LENGTH = 255
DOCX_REQUIRED_MEMBERS = {"[Content_Types].xml", "word/document.xml"}


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

        if (
            not original_filename
            or len(original_filename) > MAX_FILENAME_LENGTH
            or any(ord(character) < 32 for character in original_filename)
            or suffix not in ALLOWED_DOCUMENT_TYPES
        ):
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

            if size_bytes == 0:
                raise InvalidDocumentError("The uploaded document is empty.")
            await anyio.to_thread.run_sync(
                self._validate_file_signature,
                destination,
                suffix,
            )
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
        self.path_for(storage_key).unlink(missing_ok=True)

    def path_for(self, storage_key: str) -> Path:
        key_path = Path(storage_key)
        try:
            uuid.UUID(key_path.stem)
        except ValueError as error:
            raise InvalidDocumentError("Invalid document storage key.") from error
        if (
            key_path.name != storage_key
            or key_path.suffix.lower() not in ALLOWED_DOCUMENT_TYPES
        ):
            raise InvalidDocumentError("Invalid document storage key.")
        return self.directory / storage_key

    @staticmethod
    def _validate_file_signature(path: Path, suffix: str) -> None:
        with path.open("rb") as document:
            signature = document.read(8)

        if suffix == ".pdf" and not signature.startswith(b"%PDF-"):
            raise InvalidDocumentError("The uploaded file is not a valid PDF.")
        if suffix == ".docx":
            if not signature.startswith(b"PK") or not zipfile.is_zipfile(path):
                raise InvalidDocumentError("The uploaded file is not a valid DOCX.")
            with zipfile.ZipFile(path) as archive:
                if not DOCX_REQUIRED_MEMBERS.issubset(archive.namelist()):
                    raise InvalidDocumentError("The uploaded file is not a valid DOCX.")
        if suffix == ".txt" and b"\x00" in signature:
            raise InvalidDocumentError("The uploaded file is not plain text.")
