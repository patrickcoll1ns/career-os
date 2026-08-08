import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    target_date: date | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: GoalStatus
    target_date: date | None
    created_at: datetime
    updated_at: datetime
