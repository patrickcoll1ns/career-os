import asyncio
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.goals import get_goal_service
from app.main import app
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalStatus, GoalUpdate
from app.services.goals import GoalService

client = TestClient(app)


def goal_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": "Finish CareerOS MVP",
        "description": "Build a portfolio project",
        "status": "active",
        "horizon": "short_term",
        "target_date": date(2026, 10, 1),
        "archived_at": None,
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_update_goal_status() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.update.return_value = goal_record(id=goal_id, status="completed")
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.patch(
            f"/goals/{goal_id}",
            json={"status": "completed"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    service.update.assert_awaited_once()


def test_update_missing_goal_returns_not_found() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.update.return_value = None
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.patch(f"/goals/{goal_id}", json={"status": "paused"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Goal not found"}


def test_update_goal_rejects_invalid_status() -> None:
    response = client.patch(
        f"/goals/{uuid.uuid4()}",
        json={"status": "finished"},
    )

    assert response.status_code == 422


def test_update_goal_title_description_and_target_date() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.update.return_value = goal_record(
        id=goal_id,
        title="Ship the goal editing checkpoint",
        description="Let users fix typos without recreating a goal",
        target_date=date(2026, 11, 15),
    )
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.patch(
            f"/goals/{goal_id}",
            json={
                "title": "Ship the goal editing checkpoint",
                "description": "Let users fix typos without recreating a goal",
                "target_date": "2026-11-15",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Ship the goal editing checkpoint"
    assert body["description"] == "Let users fix typos without recreating a goal"
    assert body["target_date"] == "2026-11-15"
    service.update.assert_awaited_once()


def test_update_goal_can_clear_description_and_target_date() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.update.return_value = goal_record(
        id=goal_id,
        description=None,
        target_date=None,
    )
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.patch(
            f"/goals/{goal_id}",
            json={"description": None, "target_date": None},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["target_date"] is None


def test_update_goal_rejects_blank_title() -> None:
    response = client.patch(
        f"/goals/{uuid.uuid4()}",
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_goal_service_updates_only_provided_fields() -> None:
    goal = goal_record()
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = goal
    repository.save.side_effect = lambda saved_goal: saved_goal
    service = GoalService(repository)

    result = asyncio.run(
        service.update(
            goal.id,
            GoalUpdate(status=GoalStatus.COMPLETED),
        )
    )

    assert result is goal
    assert goal.status == "completed"
    assert goal.title == "Finish CareerOS MVP"
    repository.save.assert_awaited_once_with(goal)


def test_goal_service_updates_title_description_and_target_date() -> None:
    goal = goal_record()
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = goal
    repository.save.side_effect = lambda saved_goal: saved_goal
    service = GoalService(repository)

    result = asyncio.run(
        service.update(
            goal.id,
            GoalUpdate(
                title="Learn advanced FastAPI",
                description=None,
                target_date=None,
            ),
        )
    )

    assert result is goal
    assert goal.title == "Learn advanced FastAPI"
    assert goal.description is None
    assert goal.target_date is None
    assert goal.status == "active"
    repository.save.assert_awaited_once_with(goal)
