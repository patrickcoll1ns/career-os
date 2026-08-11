import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class GoalHorizon(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    horizon: GoalHorizon = GoalHorizon.SHORT_TERM
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Goal title cannot be blank.")
        return title


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: GoalStatus | None = None
    horizon: GoalHorizon | None = None
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        title = value.strip()
        if not title:
            raise ValueError("Goal title cannot be blank.")
        return title


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: GoalStatus
    horizon: GoalHorizon
    target_date: date | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
