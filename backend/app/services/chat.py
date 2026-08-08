import uuid

from app.integrations.anthropic_client import AnthropicClient
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.accomplishments import AccomplishmentRepository
from app.repositories.chat import ConversationRepository
from app.repositories.goals import GoalRepository

BASE_SYSTEM_PROMPT = (
    "You are the CareerOS career copilot. Give concise, practical career "
    "coaching grounded in the person's actual goals and accomplishments "
    "below. Reference specific goals or accomplishments by name when it "
    "helps. If the profile is empty, coach generally and encourage them to "
    "add goals and accomplishments to CareerOS so future advice can be "
    "more specific."
)


class ChatService:
    """Coordinate persisted career-coaching conversations with Claude."""

    def __init__(
        self,
        conversation_repository: ConversationRepository,
        goal_repository: GoalRepository,
        accomplishment_repository: AccomplishmentRepository,
        anthropic_client: AnthropicClient,
    ) -> None:
        self.conversation_repository = conversation_repository
        self.goal_repository = goal_repository
        self.accomplishment_repository = accomplishment_repository
        self.anthropic_client = anthropic_client

    async def create_conversation(self) -> Conversation:
        return await self.conversation_repository.add(Conversation())

    async def list_conversations(self) -> list[Conversation]:
        return await self.conversation_repository.list_all()

    async def get_conversation_with_messages(
        self, conversation_id: uuid.UUID
    ) -> tuple[Conversation, list[Message]] | None:
        conversation = await self.conversation_repository.get(conversation_id)
        if conversation is None:
            return None

        messages = await self.conversation_repository.list_messages(conversation_id)
        return conversation, messages

    async def send_message(
        self, conversation_id: uuid.UUID, content: str
    ) -> tuple[Conversation, list[Message]] | None:
        conversation = await self.conversation_repository.get(conversation_id)
        if conversation is None:
            return None

        await self.conversation_repository.add_message(
            Message(conversation_id=conversation_id, role="user", content=content)
        )

        system_prompt = await self._build_system_prompt()
        history = await self.conversation_repository.list_messages(conversation_id)
        reply_text = await self.anthropic_client.generate_reply(
            system_prompt=system_prompt,
            messages=[
                {"role": message.role, "content": message.content}
                for message in history
            ],
        )

        await self.conversation_repository.add_message(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=reply_text,
            )
        )

        return await self.get_conversation_with_messages(conversation_id)

    async def _build_system_prompt(self) -> str:
        goals = await self.goal_repository.list_all()
        accomplishments = await self.accomplishment_repository.list_all()

        sections = [BASE_SYSTEM_PROMPT]

        if goals:
            goal_lines = "\n".join(f"- {goal.title} ({goal.status})" for goal in goals)
            sections.append(f"Current goals:\n{goal_lines}")

        if accomplishments:
            accomplishment_lines = "\n".join(
                f"- {accomplishment.title}" for accomplishment in accomplishments
            )
            sections.append(f"Recent accomplishments:\n{accomplishment_lines}")

        return "\n\n".join(sections)
