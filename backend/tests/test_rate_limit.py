import pytest
from fastapi import HTTPException

from app.core.auth import owner_context
from app.core.config import settings
from app.core.rate_limit import SlidingWindowRateLimiter, limiter, rate_limit

OWNER = "google:123"
OTHER_OWNER = "google:456"


@pytest.fixture(autouse=True)
def clear_limiter():
    limiter.reset()
    yield
    limiter.reset()


def test_requests_are_allowed_up_to_the_limit() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60)

    assert [window.check("ai", OWNER, 3) for _ in range(3)] == [None, None, None]


def test_the_next_request_over_the_limit_reports_a_wait() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60)
    for _ in range(2):
        window.check("ai", OWNER, 2)

    retry_after = window.check("ai", OWNER, 2)

    assert retry_after is not None
    assert 0 < retry_after <= 60


def test_owners_are_counted_separately() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60)
    window.check("ai", OWNER, 1)

    assert window.check("ai", OTHER_OWNER, 1) is None


def test_buckets_are_counted_separately() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60)
    window.check("ai", OWNER, 1)

    assert window.check("documents", OWNER, 1) is None


def test_a_zero_limit_blocks_every_request() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60)

    assert window.check("ai", OWNER, 0) is not None


def test_tracked_keys_stay_bounded() -> None:
    window = SlidingWindowRateLimiter(window_seconds=60, max_tracked_keys=10)

    for index in range(50):
        window.check("ai", f"google:{index}", 5)

    assert len(window._hits) <= 10


async def test_the_dependency_raises_429_with_a_retry_after_header(monkeypatch) -> None:
    monkeypatch.setattr(settings, "rate_limit_ai_requests", 1)
    enforce = rate_limit("ai", "rate_limit_ai_requests")

    with owner_context(OWNER):
        await enforce()

        with pytest.raises(HTTPException) as error:
            await enforce()

    assert error.value.status_code == 429
    assert "Retry-After" in error.value.headers
