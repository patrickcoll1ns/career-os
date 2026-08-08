from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.session import database_is_ready

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report that the FastAPI process is running."""
    return HealthResponse(status="ok", service="careeros-api")


@router.get("/health/database", response_model=HealthResponse)
async def database_health_check() -> HealthResponse:
    """Report whether FastAPI can execute a query against PostgreSQL."""
    if not await database_is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    return HealthResponse(status="ok", service="postgres")
