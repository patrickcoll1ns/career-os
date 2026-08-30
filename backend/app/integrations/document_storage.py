import hashlib
import os
import shutil
import tempfile
import uuid
import zipfile
from abc import ABC, abstractmethod
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


class DocumentNotStoredError(LookupError):
    """Raised when a stored document's bytes cannot be read back."""


@dataclass(frozen=True)
class StoredDocument:
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    storage_key: str


class DocumentStorage(ABC):
    """Validate uploads once, then persist them through a swappable backend.

    Validation is shared so the local development backend and the production
    object-storage backend can never drift apart on what they accept.
    """

    def __init__(self, max_size_bytes: int) -> None:
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

        storage_key = f"{uuid.uuid4()}{suffix}"
        digest = hashlib.sha256()
        size_bytes = 0
        # Stream to a private temporary file first so an oversized or malformed
        # upload never reaches the real storage backend.
        handle, temporary_name = tempfile.mkstemp(suffix=suffix)
        temporary_path = Path(temporary_name)

        try:
            os.close(handle)
            async with await anyio.open_file(temporary_path, "wb") as staged_file:
                while chunk := await upload.read(READ_CHUNK_SIZE):
                    size_bytes += len(chunk)
                    if size_bytes > self.max_size_bytes:
                        raise DocumentTooLargeError(
                            "The document exceeds the 5 MB upload limit."
                        )
                    digest.update(chunk)
                    await staged_file.write(chunk)

            if size_bytes == 0:
                raise InvalidDocumentError("The uploaded document is empty.")
            await anyio.to_thread.run_sync(
                self._validate_file_signature, temporary_path, suffix
            )
            await self._persist(temporary_path, storage_key, content_type)
        finally:
            temporary_path.unlink(missing_ok=True)
            await upload.close()

        return StoredDocument(
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=digest.hexdigest(),
            storage_key=storage_key,
        )

    @abstractmethod
    async def _persist(
        self, source: Path, storage_key: str, content_type: str
    ) -> None: ...

    @abstractmethod
    async def read(self, storage_key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, storage_key: str) -> None: ...

    @staticmethod
    def validate_storage_key(storage_key: str) -> str:
        """Reject any key this application did not generate."""
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
        return storage_key

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


class LocalDocumentStorage(DocumentStorage):
    """Keep documents on the local filesystem for development and tests."""

    def __init__(self, directory: Path, max_size_bytes: int) -> None:
        super().__init__(max_size_bytes)
        self.directory = directory

    async def _persist(self, source: Path, storage_key: str, content_type: str) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        await anyio.to_thread.run_sync(
            shutil.copyfile, source, self.directory / storage_key
        )

    async def read(self, storage_key: str) -> bytes:
        path = self.path_for(storage_key)
        try:
            return await anyio.to_thread.run_sync(path.read_bytes)
        except OSError as error:
            raise DocumentNotStoredError("The stored document is missing.") from error

    async def delete(self, storage_key: str) -> None:
        self.path_for(storage_key).unlink(missing_ok=True)

    def path_for(self, storage_key: str) -> Path:
        return self.directory / self.validate_storage_key(storage_key)


class S3DocumentStorage(DocumentStorage):
    """Keep documents in a private S3-compatible bucket such as Cloudflare R2.

    Container filesystems are ephemeral, so anything a deployed CareerOS must
    still have after a restart belongs here rather than on local disk.
    """

    def __init__(
        self,
        bucket: str,
        max_size_bytes: int,
        endpoint_url: str | None = None,
        region: str = "auto",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        key_prefix: str = "documents/",
    ) -> None:
        super().__init__(max_size_bytes)
        self.bucket = bucket
        self.key_prefix = key_prefix
        self._client_options = {
            "endpoint_url": endpoint_url,
            "region_name": region,
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
        }
        self._client = None

    @property
    def client(self):
        """Build the client on first use so imports stay free of network setup."""
        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                **{
                    key: value
                    for key, value in self._client_options.items()
                    if value is not None
                },
            )
        return self._client

    def object_key(self, storage_key: str) -> str:
        return f"{self.key_prefix}{self.validate_storage_key(storage_key)}"

    async def _persist(self, source: Path, storage_key: str, content_type: str) -> None:
        def upload() -> None:
            with source.open("rb") as body:
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=self.object_key(storage_key),
                    Body=body,
                    ContentType=content_type,
                )

        await anyio.to_thread.run_sync(upload)

    async def read(self, storage_key: str) -> bytes:
        def download() -> bytes:
            response = self.client.get_object(
                Bucket=self.bucket, Key=self.object_key(storage_key)
            )
            return response["Body"].read()

        try:
            return await anyio.to_thread.run_sync(download)
        except Exception as error:
            raise DocumentNotStoredError("The stored document is missing.") from error

    async def delete(self, storage_key: str) -> None:
        def remove() -> None:
            self.client.delete_object(
                Bucket=self.bucket, Key=self.object_key(storage_key)
            )

        await anyio.to_thread.run_sync(remove)


def _reveal(secret) -> str | None:
    return secret.get_secret_value() if secret else None


def build_document_storage(settings) -> DocumentStorage:
    """Choose the storage backend the current environment is configured for."""
    if settings.document_storage_backend == "s3":
        if not settings.s3_bucket:
            raise ValueError("S3_BUCKET is required when DOCUMENT_STORAGE_BACKEND=s3.")
        return S3DocumentStorage(
            bucket=settings.s3_bucket,
            max_size_bytes=settings.max_document_size_bytes,
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
            access_key_id=_reveal(settings.s3_access_key_id),
            secret_access_key=_reveal(settings.s3_secret_access_key),
        )
    return LocalDocumentStorage(
        settings.document_upload_directory, settings.max_document_size_bytes
    )
