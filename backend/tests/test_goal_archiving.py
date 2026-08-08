import asyncio
import uuid
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.goals import get_goal_service
from app.main import app
from app.repositories.goals import GoalRepository
from app.services.goals import GoalService

client = TestClient(app)


def goal_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": "Finish CareerOS MVP",
        "description": "Build a portfolio project",
        "status": "active",
        "target_date": date(2026, 10, 1),
        "archived_at": None,
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_archive_goal() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.archive.return_value = goal_record(
        id=goal_id,
        archived_at=datetime(2026, 8, 8, 12, tzinfo=UTC),
    )
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.post(f"/goals/{goal_id}/archive")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["archived_at"] is not None
    service.archive.assert_awaited_once_with(goal_id)


def test_archive_missing_goal_returns_not_found() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.archive.return_value = None
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.post(f"/goals/{goal_id}/archive")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Goal not found"}


def test_list_goals_excludes_archived_by_default() -> None:
    service = AsyncMock(spec=GoalService)
    service.list_all.return_value = [goal_record()]
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.get("/goals")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    service.list_all.assert_awaited_once_with(include_archived=False)


def test_list_goals_can_include_archived() -> None:
    service = AsyncMock(spec=GoalService)
    service.list_all.return_value = []
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.get("/goals", params={"include_archived": "true"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    service.list_all.assert_awaited_once_with(include_archived=True)


def test_goal_service_archive_sets_archived_at() -> None:
    goal = goal_record()
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = goal
    repository.save.side_effect = lambda saved_goal: saved_goal
    service = GoalService(repository)

    result = asyncio.run(service.archive(goal.id))

    assert result is goal
    assert goal.archived_at is not None
    repository.save.assert_awaited_once_with(goal)


def test_goal_service_archive_returns_none_for_missing_goal() -> None:
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = None
    service = GoalService(repository)

    result = asyncio.run(service.archive(uuid.uuid4()))

    assert result is None
    repository.save.assert_not_awaited()


def test_restore_goal() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.restore.return_value = goal_record(id=goal_id, archived_at=None)
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.post(f"/goals/{goal_id}/restore")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["archived_at"] is None
    service.restore.assert_awaited_once_with(goal_id)


def test_restore_missing_goal_returns_not_found() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.restore.return_value = None
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.post(f"/goals/{goal_id}/restore")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Goal not found"}


def test_list_archived_goals() -> None:
    service = AsyncMock(spec=GoalService)
    service.list_archived.return_value = [
        goal_record(archived_at=datetime(2026, 8, 8, 12, tzinfo=UTC)),
    ]
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.get("/goals/archived")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["archived_at"] is not None
    service.list_archived.assert_awaited_once()


def test_goal_service_restore_clears_archived_at() -> None:
    goal = goal_record(archived_at=datetime(2026, 8, 8, 12, tzinfo=UTC))
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = goal
    repository.save.side_effect = lambda saved_goal: saved_goal
    service = GoalService(repository)

    result = asyncio.run(service.restore(goal.id))

    assert result is goal
    assert goal.archived_at is None
    repository.save.assert_awaited_once_with(goal)


def test_goal_service_restore_returns_none_for_missing_goal() -> None:
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = None
    service = GoalService(repository)

    result = asyncio.run(service.restore(uuid.uuid4()))

    assert result is None
    repository.save.assert_not_awaited()
