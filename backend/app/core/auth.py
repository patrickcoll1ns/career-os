import hashlib
import hmac
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

SIGNATURE_MAX_AGE_SECONDS = 60
MAX_OWNER_ID_LENGTH = 200
DEVELOPMENT_OWNER_ID = "development:local"

# Bodies at or below this size are re-hashed and compared against the signed
# digest. Larger bodies arrive only through streamed multipart uploads, which
# must not be buffered into memory just to authenticate them.
MAX_VERIFIED_BODY_BYTES = 1024 * 1024
MULTIPART_CONTENT_TYPE = "multipart/form-data"
EMPTY_BODY_SHA256 = hashlib.sha256(b"").hexdigest()

_owner_id: ContextVar[str | None] = ContextVar("owner_id", default=None)


@dataclass(frozen=True)
class CurrentUser:
    id: str


def get_current_owner_id() -> str:
    owner_id = _owner_id.get()
    if owner_id is None:
        raise RuntimeError("A repository was used outside an authenticated request.")
    return owner_id


@contextmanager
def owner_context(owner_id: str) -> Iterator[str]:
    """Bind an owner outside an HTTP request, for maintenance commands."""
    token = _owner_id.set(owner_id)
    try:
        yield owner_id
    finally:
        _owner_id.reset(token)


def signature_payload(
    method: str,
    request_target: str,
    timestamp: str,
    owner_id: str,
    body_sha256: str,
) -> bytes:
    """Build the exact byte string both services sign.

    The body digest is part of the payload so a signature captured inside the
    replay window cannot be reused to send different content to the same route.
    """
    return "\n".join(
        (method, request_target, timestamp, owner_id, body_sha256)
    ).encode()


def _request_target(request: Request) -> str:
    if request.url.query:
        return f"{request.url.path}?{request.url.query}"
    return request.url.path


def _unauthorized() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _is_hex_digest(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


async def _body_digest_matches(request: Request, expected_digest: str) -> bool:
    """Confirm the received body hashes to the digest the caller signed."""
    content_type = request.headers.get("content-type", "")
    if content_type.startswith(MULTIPART_CONTENT_TYPE):
        # Streamed uploads are bounded and validated by the storage layer; the
        # signature still binds the method, path, owner, and timestamp.
        return True

    declared_length = request.headers.get("content-length")
    if declared_length is None:
        # Without a declared length the body could be arbitrarily long. Refuse a
        # chunked request rather than reading it into memory; anything else has
        # no body to compare.
        transfer_encoding = request.headers.get("transfer-encoding", "").lower()
        if "chunked" in transfer_encoding:
            return False
        return hmac.compare_digest(expected_digest, EMPTY_BODY_SHA256)

    try:
        if int(declared_length) > MAX_VERIFIED_BODY_BYTES:
            return False
    except ValueError:
        return False

    body = await request.body()
    if len(body) > MAX_VERIFIED_BODY_BYTES:
        return False
    return hmac.compare_digest(hashlib.sha256(body).hexdigest(), expected_digest)


async def require_user(
    request: Request,
    owner_id: Annotated[str | None, Header(alias="X-CareerOS-User")] = None,
    timestamp: Annotated[str | None, Header(alias="X-CareerOS-Timestamp")] = None,
    signature: Annotated[str | None, Header(alias="X-CareerOS-Signature")] = None,
    content_digest: Annotated[
        str | None, Header(alias="X-CareerOS-Content-SHA256")
    ] = None,
) -> AsyncIterator[CurrentUser]:
    secret = settings.internal_auth_secret
    no_identity_headers = not owner_id and not timestamp and not signature
    if settings.allows_unsigned_requests and no_identity_headers:
        token = _owner_id.set(DEVELOPMENT_OWNER_ID)
        try:
            yield CurrentUser(DEVELOPMENT_OWNER_ID)
        finally:
            _owner_id.reset(token)
        return

    if not secret or not owner_id or not timestamp or not signature:
        raise _unauthorized()
    if not owner_id.strip() or len(owner_id) > MAX_OWNER_ID_LENGTH:
        raise _unauthorized()

    # hmac.compare_digest raises TypeError on non-ASCII strings, so shape is
    # checked before either value reaches it.
    digest = content_digest or EMPTY_BODY_SHA256
    if not _is_hex_digest(digest) or not _is_hex_digest(signature):
        raise _unauthorized()

    try:
        request_time = int(timestamp)
    except ValueError as error:
        raise _unauthorized() from error
    if abs(int(time.time()) - request_time) > SIGNATURE_MAX_AGE_SECONDS:
        raise _unauthorized()

    expected = hmac.new(
        secret.get_secret_value().encode(),
        signature_payload(
            request.method,
            _request_target(request),
            timestamp,
            owner_id,
            digest,
        ),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise _unauthorized()
    if not await _body_digest_matches(request, digest):
        raise _unauthorized()

    token = _owner_id.set(owner_id)
    try:
        yield CurrentUser(owner_id)
    finally:
        _owner_id.reset(token)
