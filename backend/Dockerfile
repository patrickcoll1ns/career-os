# syntax=docker/dockerfile:1

# Build the dependency set in a throwaway stage so compilers and caches never
# reach the published image.
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip && pip install .


FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# curl is only for the container healthcheck.
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 careeros

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=careeros:careeros app ./app
COPY --chown=careeros:careeros migrations ./migrations
COPY --chown=careeros:careeros alembic.ini ./alembic.ini

USER careeros
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail --silent http://127.0.0.1:8000/health || exit 1

# One worker keeps the in-process rate limiter exact. Scale with more instances
# only after moving those counters into PostgreSQL or Redis.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
