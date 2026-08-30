import time
from collections import OrderedDict, deque
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import HTTPException, status

from app.core.auth import get_current_owner_id
from app.core.config import settings

# Bounds the limiter's own memory. Owners are only created by verified
# signatures, so this ceiling is a safety net rather than a hot path.
MAX_TRACKED_KEYS = 10_000
# How many admitted requests pass between full sweeps for expired owners.
PRUNE_INTERVAL_CALLS = 256


class SlidingWindowRateLimiter:
    """Count recent requests per owner inside a fixed-length window.

    State lives in the process, which is exact for the single-instance
    deployment CareerOS targets. Running several API instances would divide the
    effective limit between them; move the counters into PostgreSQL or Redis
    before scaling out.
    """

    def __init__(self, window_seconds: int, max_tracked_keys: int = MAX_TRACKED_KEYS):
        if window_seconds < 1:
            raise ValueError("window_seconds must be positive.")
        self.window_seconds = window_seconds
        self.max_tracked_keys = max_tracked_keys
        self._hits: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()
        self._calls_since_prune = 0

    def check(self, bucket: str, owner_id: str, limit: int) -> float | None:
        """Record a request. Return seconds to wait when the limit is spent."""
        if limit < 1:
            return float(self.window_seconds)

        now = time.monotonic()
        key = (bucket, owner_id)
        hits = self._hits.get(key)
        if hits is None:
            hits = deque()
            self._hits[key] = hits
        self._hits.move_to_end(key)

        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= limit:
            return max(0.0, hits[0] + self.window_seconds - now)

        hits.append(now)
        self._prune()
        return None

    def reset(self) -> None:
        self._hits.clear()
        self._calls_since_prune = 0

    def _prune(self) -> None:
        """Drop expired owners occasionally rather than on every request.

        A full sweep is O(tracked owners); doing it inline on each call would
        put that cost on the hot path for no benefit.
        """
        # Least-recently-used eviction is cheap and bounds memory immediately.
        while len(self._hits) > self.max_tracked_keys:
            self._hits.popitem(last=False)

        self._calls_since_prune += 1
        if self._calls_since_prune < PRUNE_INTERVAL_CALLS:
            return
        self._calls_since_prune = 0

        cutoff = time.monotonic() - self.window_seconds
        stale = [
            key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff
        ]
        for key in stale:
            del self._hits[key]


limiter = SlidingWindowRateLimiter(settings.rate_limit_window_seconds)


def rate_limit(bucket: str, limit_name: str) -> Callable[[], Coroutine[Any, Any, None]]:
    """Build a dependency that limits one owner's use of a group of routes.

    The limit is read per request so tests and deployments can adjust it without
    rebuilding the routing table.
    """

    async def enforce() -> None:
        limit = getattr(settings, limit_name)
        retry_after = limiter.check(bucket, get_current_owner_id(), limit)
        if retry_after is None:
            return
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "You have reached the CareerOS request limit. "
                "Try again in a few minutes."
            ),
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    return enforce
