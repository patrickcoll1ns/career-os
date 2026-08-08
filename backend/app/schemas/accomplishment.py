import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccomplishmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    achieved_on: date | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Accomplishment title cannot be blank.")
        return title


class AccomplishmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    achieved_on: date | None
    created_at: datetime
    updated_at: datetime
