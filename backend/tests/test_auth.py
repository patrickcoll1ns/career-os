import hashlib
import hmac
import time
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.routes.goals import get_goal_service
from app.core.config import settings
from app.main import app
from app.services.goals import GoalService

client = TestClient(app)
SECRET = "test-only-internal-auth-secret"


def signed_headers(owner_id: str, timestamp: int | None = None) -> dict[str, str]:
    timestamp_text = str(timestamp or int(time.time()))
    payload = f"GET\n/goals\n{timestamp_text}\n{owner_id}".encode()
    signature = hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return {
        "X-CareerOS-User": owner_id,
        "X-CareerOS-Timestamp": timestamp_text,
        "X-CareerOS-Signature": signature,
    }


def configure_production_auth(monkeypatch) -> None:
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "internal_auth_secret", SecretStr(SECRET))


def test_protected_routes_reject_unsigned_requests(monkeypatch) -> None:
    configure_production_auth(monkeypatch)

    response = client.get("/goals")

    assert response.status_code == 401


def test_protected_routes_accept_a_valid_signed_identity(monkeypatch) -> None:
    configure_production_auth(monkeypatch)
    service = AsyncMock(spec=GoalService)
    service.list_all.return_value = []
    app.dependency_overrides[get_goal_service] = lambda: service

    try:
        response = client.get("/goals", headers=signed_headers("google:123"))
    finally:
        app.dependency_overrides.pop(get_goal_service, None)

    assert response.status_code == 200
    assert response.json() == []


def test_protected_routes_reject_replayed_signatures(monkeypatch) -> None:
    configure_production_auth(monkeypatch)

    response = client.get(
        "/goals",
        headers=signed_headers("google:123", int(time.time()) - 120),
    )

    assert response.status_code == 401


def test_protected_routes_reject_a_tampered_owner(monkeypatch) -> None:
    configure_production_auth(monkeypatch)
    headers = signed_headers("google:123")
    headers["X-CareerOS-User"] = "google:456"

    response = client.get("/goals", headers=headers)

    assert response.status_code == 401
