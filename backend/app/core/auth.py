import hashlib
import hmac
import time
from collections.abc import AsyncIterator
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

SIGNATURE_MAX_AGE_SECONDS = 60
MAX_OWNER_ID_LENGTH = 200
DEVELOPMENT_OWNER_ID = "development:local"

_owner_id: ContextVar[str | None] = ContextVar("owner_id", default=None)


@dataclass(frozen=True)
class CurrentUser:
    id: str


def get_current_owner_id() -> str:
    owner_id = _owner_id.get()
    if owner_id is None:
        raise RuntimeError("A repository was used outside an authenticated request.")
    return owner_id


def _signature_payload(request: Request, owner_id: str, timestamp: str) -> bytes:
    request_target = request.url.path
    if request.url.query:
        request_target = f"{request_target}?{request.url.query}"
    return f"{request.method}\n{request_target}\n{timestamp}\n{owner_id}".encode()


async def require_user(
    request: Request,
    owner_id: Annotated[str | None, Header(alias="X-CareerOS-User")] = None,
    timestamp: Annotated[str | None, Header(alias="X-CareerOS-Timestamp")] = None,
    signature: Annotated[str | None, Header(alias="X-CareerOS-Signature")] = None,
) -> AsyncIterator[CurrentUser]:
    secret = settings.internal_auth_secret
    no_identity_headers = not owner_id and not timestamp and not signature
    if settings.environment != "production" and no_identity_headers:
        token = _owner_id.set(DEVELOPMENT_OWNER_ID)
        try:
            yield CurrentUser(DEVELOPMENT_OWNER_ID)
        finally:
            _owner_id.reset(token)
        return

    if not secret or not owner_id or not timestamp or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not owner_id.strip() or len(owner_id) > MAX_OWNER_ID_LENGTH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        request_time = int(timestamp)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from error
    if abs(int(time.time()) - request_time) > SIGNATURE_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    expected = hmac.new(
        secret.get_secret_value().encode(),
        _signature_payload(request, owner_id, timestamp),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token = _owner_id.set(owner_id)
    try:
        yield CurrentUser(owner_id)
    finally:
        _owner_id.reset(token)
