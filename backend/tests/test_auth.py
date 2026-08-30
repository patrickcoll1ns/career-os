import hashlib
import hmac
import time
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.routes.goals import get_goal_service
from app.core.auth import _is_hex_digest
from app.core.config import settings
from app.main import app
from app.services.goals import GoalService

client = TestClient(app)
SECRET = "test-only-internal-auth-secret"


EMPTY_BODY_SHA256 = hashlib.sha256(b"").hexdigest()


def signed_headers(
    owner_id: str,
    timestamp: int | None = None,
    method: str = "GET",
    target: str = "/goals",
    body: bytes = b"",
) -> dict[str, str]:
    timestamp_text = str(timestamp or int(time.time()))
    digest = hashlib.sha256(body).hexdigest()
    payload = "\n".join((method, target, timestamp_text, owner_id, digest)).encode()
    signature = hmac.new(SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return {
        "X-CareerOS-User": owner_id,
        "X-CareerOS-Timestamp": timestamp_text,
        "X-CareerOS-Signature": signature,
        "X-CareerOS-Content-SHA256": digest,
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


def test_protected_routes_reject_a_body_that_does_not_match_the_signature(
    monkeypatch,
) -> None:
    configure_production_auth(monkeypatch)
    signed_body = b'{"title": "Signed goal"}'
    headers = signed_headers(
        "google:123", method="POST", target="/goals", body=signed_body
    )
    headers["Content-Type"] = "application/json"

    response = client.post(
        "/goals", headers=headers, content=b'{"title": "Swapped goal"}'
    )

    assert response.status_code == 401


def test_protected_routes_reject_a_stripped_content_digest(monkeypatch) -> None:
    """Removing the digest header cannot downgrade a request that carries a body.

    The header is part of the signed payload, so dropping it makes the empty
    digest the verified value and the signature no longer matches.
    """
    configure_production_auth(monkeypatch)
    body = b'{"title": "Signed goal"}'
    headers = signed_headers("google:123", method="POST", target="/goals", body=body)
    del headers["X-CareerOS-Content-SHA256"]
    headers["Content-Type"] = "application/json"

    response = client.post("/goals", headers=headers, content=body)

    assert response.status_code == 401


class FakeRequest:
    """Minimal stand-in for exercising the body-digest rules directly."""

    def __init__(self, headers: dict[str, str], body: bytes = b"") -> None:
        self.headers = headers
        self._body = body

    async def body(self) -> bytes:
        return self._body


async def test_multipart_uploads_are_not_body_compared() -> None:
    from app.core.auth import _body_digest_matches

    request = FakeRequest({"content-type": "multipart/form-data; boundary=x"})

    assert await _body_digest_matches(request, "0" * 64) is True


async def test_a_chunked_body_is_refused_rather_than_buffered() -> None:
    """An undeclared length must never be read into memory to authenticate it."""
    from app.core.auth import _body_digest_matches

    request = FakeRequest(
        {"content-type": "application/json", "transfer-encoding": "chunked"}
    )

    assert await _body_digest_matches(request, EMPTY_BODY_SHA256) is False


async def test_an_oversized_declared_body_is_refused() -> None:
    from app.core.auth import MAX_VERIFIED_BODY_BYTES, _body_digest_matches

    request = FakeRequest(
        {
            "content-type": "application/json",
            "content-length": str(MAX_VERIFIED_BODY_BYTES + 1),
        }
    )

    assert await _body_digest_matches(request, EMPTY_BODY_SHA256) is False


async def test_a_request_without_a_body_matches_the_empty_digest() -> None:
    from app.core.auth import _body_digest_matches

    assert await _body_digest_matches(FakeRequest({}), EMPTY_BODY_SHA256) is True


def test_a_malformed_signature_header_is_rejected_cleanly(monkeypatch) -> None:
    """Garbage in the signature must produce 401, never a 500.

    Non-ASCII is checked against the helper directly, because HTTP clients
    refuse to send such a header even though a raw latin-1 request can carry it.
    """
    configure_production_auth(monkeypatch)
    assert not _is_hex_digest("é" * 64)

    for bad_signature in ("not-hex" * 10, "", "AB" * 32, "a" * 63):
        headers = signed_headers("google:123")
        headers["X-CareerOS-Signature"] = bad_signature

        response = client.get("/goals", headers=headers)

        assert response.status_code == 401, bad_signature
