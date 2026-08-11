import asyncio
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.accomplishments import get_accomplishment_service
from app.main import app
from app.models.accomplishment import Accomplishment
from app.repositories.accomplishments import AccomplishmentRepository
from app.services.accomplishments import AccomplishmentService

client = TestClient(app)


def accomplishment_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": "Shipped the goal dashboard",
        "description": None,
        "achieved_on": date(2026, 8, 8),
        "archived_at": None,
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_accomplishment_can_be_soft_deleted() -> None:
    assert "archived_at" in Accomplishment.__table__.columns.keys()


def test_archive_accomplishment() -> None:
    accomplishment_id = uuid.uuid4()
    service = AsyncMock(spec=AccomplishmentService)
    service.archive.return_value = accomplishment_record(
        id=accomplishment_id,
        archived_at=datetime(2026, 8, 9, tzinfo=UTC),
    )
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.post(f"/accomplishments/{accomplishment_id}/archive")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["archived_at"] is not None
    service.archive.assert_awaited_once_with(accomplishment_id)


def test_restore_accomplishment() -> None:
    accomplishment_id = uuid.uuid4()
    service = AsyncMock(spec=AccomplishmentService)
    service.restore.return_value = accomplishment_record(id=accomplishment_id)
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.post(f"/accomplishments/{accomplishment_id}/restore")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["archived_at"] is None
    service.restore.assert_awaited_once_with(accomplishment_id)


def test_archive_and_restore_map_missing_accomplishments_to_not_found() -> None:
    for action in ("archive", "restore"):
        service = AsyncMock(spec=AccomplishmentService)
        getattr(service, action).return_value = None
        app.dependency_overrides[get_accomplishment_service] = lambda s=service: s

        try:
            response = client.post(f"/accomplishments/{uuid.uuid4()}/{action}")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json() == {"detail": "Accomplishment not found"}


def test_list_excludes_archived_by_default() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.list_all.return_value = []
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.get("/accomplishments")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    service.list_all.assert_awaited_once_with(include_archived=False)


def test_list_can_include_archived() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.list_all.return_value = []
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.get("/accomplishments", params={"include_archived": "true"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    service.list_all.assert_awaited_once_with(include_archived=True)


def test_list_archived_accomplishments() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.list_archived.return_value = [
        accomplishment_record(archived_at=datetime(2026, 8, 9, tzinfo=UTC))
    ]
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.get("/accomplishments/archived")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1
    service.list_archived.assert_awaited_once()


def test_service_archive_sets_archived_at() -> None:
    accomplishment = accomplishment_record()
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.get.return_value = accomplishment
    repository.save.side_effect = lambda saved: saved
    service = AccomplishmentService(repository)

    result = asyncio.run(service.archive(accomplishment.id))

    assert result is accomplishment
    assert accomplishment.archived_at is not None


def test_service_restore_clears_archived_at() -> None:
    accomplishment = accomplishment_record(archived_at=datetime(2026, 8, 9, tzinfo=UTC))
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.get.return_value = accomplishment
    repository.save.side_effect = lambda saved: saved
    service = AccomplishmentService(repository)

    result = asyncio.run(service.restore(accomplishment.id))

    assert result is accomplishment
    assert accomplishment.archived_at is None


def test_service_archive_returns_none_for_a_missing_accomplishment() -> None:
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.get.return_value = None
    service = AccomplishmentService(repository)

    assert asyncio.run(service.archive(uuid.uuid4())) is None
    repository.save.assert_not_awaited()
