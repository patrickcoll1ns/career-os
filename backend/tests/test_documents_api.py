import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.documents import get_document_service
from app.main import app
from app.services.documents import DocumentService

client = TestClient(app)


def document_record():
    timestamp = datetime(2026, 8, 9, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        original_filename="resume.pdf",
        content_type="application/pdf",
        size_bytes=2048,
        sha256="a" * 64,
        status="pending",
        error_message=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_upload_document() -> None:
    service = AsyncMock(spec=DocumentService)
    service.upload.return_value = document_record()
    app.dependency_overrides[get_document_service] = lambda: service

    try:
        response = client.post(
            "/documents",
            files={"file": ("resume.pdf", b"pdf bytes", "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["original_filename"] == "resume.pdf"
    assert response.json()["status"] == "pending"
    service.upload.assert_awaited_once()


def test_list_documents() -> None:
    service = AsyncMock(spec=DocumentService)
    service.list_all.return_value = [document_record()]
    app.dependency_overrides[get_document_service] = lambda: service

    try:
        response = client.get("/documents")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_delete_document() -> None:
    service = AsyncMock(spec=DocumentService)
    service.delete.return_value = True
    app.dependency_overrides[get_document_service] = lambda: service
    document_id = uuid.uuid4()

    try:
        response = client.delete(f"/documents/{document_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    service.delete.assert_awaited_once_with(document_id)


def test_delete_document_that_is_not_the_callers() -> None:
    service = AsyncMock(spec=DocumentService)
    service.delete.return_value = False
    app.dependency_overrides[get_document_service] = lambda: service

    try:
        response = client.delete(f"/documents/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
