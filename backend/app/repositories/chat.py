import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationRepository:
    """Store and retrieve conversations and their messages."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, conversation: Conversation) -> Conversation:
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def list_all(self) -> list[Conversation]:
        result = await self.session.scalars(
            select(Conversation).order_by(Conversation.updated_at.desc())
        )
        return list(result.all())

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)

    async def add_exchange(
        self,
        conversation: Conversation,
        user_message: Message,
        assistant_message: Message,
    ) -> None:
        """Persist a complete user/assistant exchange in one transaction."""
        conversation.updated_at = datetime.now(UTC)
        self.session.add_all([user_message, assistant_message])
        await self.session.commit()
        await self.session.refresh(conversation)

    async def list_messages(self, conversation_id: uuid.UUID) -> list[Message]:
        result = await self.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(result.all())
