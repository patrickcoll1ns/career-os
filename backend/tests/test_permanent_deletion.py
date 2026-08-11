import asyncio
import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.accomplishments import get_accomplishment_service
from app.api.routes.goals import get_goal_service
from app.main import app
from app.models.accomplishment import Accomplishment
from app.models.goal import Goal
from app.repositories.accomplishments import AccomplishmentRepository
from app.repositories.goals import GoalRepository
from app.services.accomplishments import AccomplishmentService
from app.services.goals import GoalService

client = TestClient(app)


def test_delete_goal() -> None:
    goal_id = uuid.uuid4()
    service = AsyncMock(spec=GoalService)
    service.delete.return_value = True
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.delete(f"/goals/{goal_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    service.delete.assert_awaited_once_with(goal_id)


def test_delete_missing_goal_returns_not_found() -> None:
    service = AsyncMock(spec=GoalService)
    service.delete.return_value = False
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.delete(f"/goals/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Goal not found"}


def test_delete_accomplishment() -> None:
    accomplishment_id = uuid.uuid4()
    service = AsyncMock(spec=AccomplishmentService)
    service.delete.return_value = True
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.delete(f"/accomplishments/{accomplishment_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    service.delete.assert_awaited_once_with(accomplishment_id)


def test_delete_missing_accomplishment_returns_not_found() -> None:
    service = AsyncMock(spec=AccomplishmentService)
    service.delete.return_value = False
    app.dependency_overrides[get_accomplishment_service] = lambda: service

    try:
        response = client.delete(f"/accomplishments/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_goal_service_delete_removes_the_row() -> None:
    goal = Goal(id=uuid.uuid4(), title="Obsolete goal")
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = goal
    service = GoalService(repository)

    assert asyncio.run(service.delete(goal.id)) is True
    repository.delete.assert_awaited_once_with(goal)


def test_goal_service_delete_reports_a_missing_goal() -> None:
    repository = AsyncMock(spec=GoalRepository)
    repository.get.return_value = None
    service = GoalService(repository)

    assert asyncio.run(service.delete(uuid.uuid4())) is False
    repository.delete.assert_not_awaited()


def test_accomplishment_service_delete_removes_the_row() -> None:
    accomplishment = Accomplishment(id=uuid.uuid4(), title="Duplicate entry")
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.get.return_value = accomplishment
    service = AccomplishmentService(repository)

    assert asyncio.run(service.delete(accomplishment.id)) is True
    repository.delete.assert_awaited_once_with(accomplishment)


def test_accomplishment_service_delete_reports_a_missing_accomplishment() -> None:
    repository = AsyncMock(spec=AccomplishmentRepository)
    repository.get.return_value = None
    service = AccomplishmentService(repository)

    assert asyncio.run(service.delete(uuid.uuid4())) is False
    repository.delete.assert_not_awaited()
