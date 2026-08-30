import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# Structured fields are allow-listed rather than filtered, so resumes, prompts,
# messages, and API keys can never reach the log stream by accident.
_RESERVED_RECORD_FIELDS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
)


class JsonLogFormatter(logging.Formatter):
    """Render records as one JSON object per line for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        current_request_id = request_id.get()
        if current_request_id:
            payload["request_id"] = current_request_id
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_FIELDS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())

    # uvicorn installs its own handlers; route them through the same formatter.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log one structured line per request without recording any request data."""

    def __init__(self, app, logger_name: str = "careeros.request") -> None:
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        current_id = (
            incoming_id if _is_safe_request_id(incoming_id) else uuid.uuid4().hex
        )
        token = request_id.set(current_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            self.logger.exception(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": self._elapsed_ms(started),
                },
            )
            raise
        else:
            self.logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": self._elapsed_ms(started),
                },
            )
            response.headers["X-Request-ID"] = current_id
            return response
        finally:
            request_id.reset(token)

    @staticmethod
    def _elapsed_ms(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 2)


def _is_safe_request_id(value: str | None) -> bool:
    """Accept only short, opaque upstream IDs so logs cannot be poisoned."""
    return (
        bool(value)
        and len(value) <= 64
        and all(character.isalnum() or character in "-_" for character in value)
    )
