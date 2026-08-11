import asyncio
import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.models.goal import Goal
from app.repositories.goals import GoalRepository
from app.schemas.goal import GoalCreate, GoalHorizon, GoalUpdate
from app.services.goals import GoalService

client = TestClient(app)


def make_service():
    repository = AsyncMock(spec=GoalRepository)
    repository.add.side_effect = lambda goal: goal
    repository.save.side_effect = lambda goal: goal
    return GoalService(repository), repository


def test_goal_horizon_is_constrained_to_known_values() -> None:
    constraint_names = {constraint.name for constraint in Goal.__table__.constraints}

    assert "ck_goals_horizon" in constraint_names


def test_create_defaults_to_short_term() -> None:
    service, repository = make_service()

    asyncio.run(service.create(GoalCreate(title="Ship the resume reviewer")))

    assert repository.add.await_args.args[0].horizon == "short_term"


def test_create_persists_the_chosen_horizon() -> None:
    service, repository = make_service()

    asyncio.run(
        service.create(
            GoalCreate(
                title="Land a new grad role",
                horizon=GoalHorizon.LONG_TERM,
            )
        )
    )

    assert repository.add.await_args.args[0].horizon == "long_term"


def test_update_stores_the_horizon_as_a_plain_string() -> None:
    """The column is a constrained string, so the enum must not leak into it."""
    service, repository = make_service()
    goal = Goal(id=uuid.uuid4(), title="Learn Rust", horizon="short_term")
    repository.get.return_value = goal

    result = asyncio.run(
        service.update(goal.id, GoalUpdate(horizon=GoalHorizon.LONG_TERM))
    )

    assert result is goal
    assert goal.horizon == "long_term"
    assert isinstance(goal.horizon, str)


def test_update_leaves_horizon_alone_when_it_is_not_supplied() -> None:
    service, repository = make_service()
    goal = Goal(id=uuid.uuid4(), title="Learn Rust", horizon="long_term")
    repository.get.return_value = goal

    asyncio.run(service.update(goal.id, GoalUpdate(title="Learn Go")))

    assert goal.horizon == "long_term"
    assert goal.title == "Learn Go"


def test_create_rejects_an_unknown_horizon() -> None:
    response = client.post(
        "/goals",
        json={"title": "Become a staff engineer", "horizon": "someday"},
    )

    assert response.status_code == 422
