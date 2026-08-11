import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_database_session
from app.integrations.anthropic_client import AnthropicClient, AnthropicReplyError
from app.integrations.document_index import DocumentVectorIndex
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.accomplishments import AccomplishmentRepository
from app.repositories.chat import ConversationRepository
from app.repositories.goals import GoalRepository
from app.schemas.chat import (
    ConversationRead,
    ConversationWithMessages,
    MessageRead,
    SendMessageRequest,
)
from app.services.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]


def get_chat_service(session: DatabaseSession) -> ChatService:
    return ChatService(
        ConversationRepository(session),
        GoalRepository(session),
        AccomplishmentRepository(session),
        AnthropicClient(),
        DocumentVectorIndex(
            settings.chroma_host,
            settings.chroma_port,
            settings.chroma_collection,
        ),
    )


ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


def _to_conversation_with_messages(
    conversation: Conversation, messages: list[Message]
) -> ConversationWithMessages:
    return ConversationWithMessages(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[MessageRead.model_validate(message) for message in messages],
    )


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(service: ChatServiceDependency) -> ConversationRead:
    conversation = await service.create_conversation()
    return ConversationRead.model_validate(conversation)


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    service: ChatServiceDependency,
) -> list[ConversationRead]:
    conversations = await service.list_conversations()
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: uuid.UUID,
    service: ChatServiceDependency,
) -> ConversationWithMessages:
    result = await service.get_conversation_with_messages(conversation_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return _to_conversation_with_messages(*result)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationWithMessages,
)
async def send_message(
    conversation_id: uuid.UUID,
    message_data: SendMessageRequest,
    service: ChatServiceDependency,
) -> ConversationWithMessages:
    try:
        result = await service.send_message(conversation_id, message_data.content)
    except AnthropicReplyError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The career copilot is unavailable right now.",
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return _to_conversation_with_messages(*result)
