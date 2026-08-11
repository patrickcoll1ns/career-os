import asyncio
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.accomplishments import get_accomplishment_service
from app.main import app
from app.repositories.accomplishments import AccomplishmentRepository
from app.schemas.accomplishment import AccomplishmentCreate
from app.services.accomplishments import AccomplishmentService

client = TestClient(app)


def accomplishment_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": "Shipped the goal dashboard",
        "description": "Delivered create, edit, archive, and restore flows",
        "achieved_on": date(2026, 8, 8),
        "archived_at": None,
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_accomplishment() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.create.return_value = accomplishment_record()
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.post(
            "/accomplishments",
            json={
                "title": "Shipped the goal dashboard",
                "description": "Delivered create, edit, archive, and restore flows",
                "achieved_on": "2026-08-08",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["title"] == "Shipped the goal dashboard"
    service.create.assert_awaited_once()


def test_list_accomplishments() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.list_all.return_value = [accomplishment_record()]
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.get("/accomplishments")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["description"] == (
        "Delivered create, edit, archive, and restore flows"
    )


def test_create_accomplishment_rejects_an_empty_title() -> None:
    response = client.post("/accomplishments", json={"title": ""})

    assert response.status_code == 422


def test_accomplishment_service_strips_title_whitespace() -> None:
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.add.side_effect = lambda accomplishment: accomplishment
    service = AccomplishmentService(repository)

    asyncio.run(
        service.create(AccomplishmentCreate(title="  Passed the certification  "))
    )

    saved_accomplishment = repository.add.await_args.args[0]
    assert saved_accomplishment.title == "Passed the certification"
