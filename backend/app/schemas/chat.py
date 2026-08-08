import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationWithMessages(ConversationRead):
    messages: list[MessageRead] = []


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("Message content cannot be blank.")
        return content
