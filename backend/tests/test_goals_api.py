import asyncio
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.goals import get_goal_service
from app.main import app
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate
from app.services.goals import GoalService

client = TestClient(app)


def goal_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": "Build a portfolio project",
        "description": "Finish CareerOS",
        "status": "active",
        "target_date": date(2026, 10, 1),
        "archived_at": None,
        "created_at": datetime(2026, 8, 7, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 7, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_goal() -> None:
    service = AsyncMock(spec=GoalService)
    service.create.return_value = goal_record()
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.post(
            "/goals",
            json={
                "title": "Build a portfolio project",
                "description": "Finish CareerOS",
                "target_date": "2026-10-01",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["title"] == "Build a portfolio project"
    assert response.json()["status"] == "active"
    service.create.assert_awaited_once()


def test_list_goals() -> None:
    service = AsyncMock(spec=GoalService)
    service.list_all.return_value = [goal_record()]
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.get("/goals")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["description"] == "Finish CareerOS"


def test_create_goal_rejects_an_empty_title() -> None:
    response = client.post("/goals", json={"title": ""})

    assert response.status_code == 422


def test_goal_service_strips_title_whitespace() -> None:
    repository = AsyncMock(spec=GoalRepository)
    repository.add.side_effect = lambda goal: goal
    service = GoalService(repository)

    asyncio.run(service.create(GoalCreate(title="  Learn FastAPI  ")))

    saved_goal = repository.add.await_args.args[0]
    assert saved_goal.title == "Learn FastAPI"
