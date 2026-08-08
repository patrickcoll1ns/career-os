from fastapi.testclient import TestClient

from app.api.routes import health as health_routes
from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "careeros-api"}


def test_database_health_check(monkeypatch) -> None:
    async def database_is_ready() -> bool:
        return True

    monkeypatch.setattr(health_routes, "database_is_ready", database_is_ready)

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "postgres"}


def test_database_health_check_when_database_is_unavailable(monkeypatch) -> None:
    async def database_is_ready() -> bool:
        return False

    monkeypatch.setattr(health_routes, "database_is_ready", database_is_ready)

    response = client.get("/health/database")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_openapi_schema_is_available() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "CareerOS API"
