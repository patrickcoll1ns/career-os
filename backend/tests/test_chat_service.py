import asyncio
import uuid
from unittest.mock import AsyncMock

from app.integrations.anthropic_client import AnthropicClient, AnthropicReplyError
from app.models.accomplishment import Accomplishment
from app.models.conversation import Conversation
from app.models.goal import Goal
from app.models.message import Message
from app.repositories.accomplishments import AccomplishmentRepository
from app.repositories.chat import ConversationRepository
from app.repositories.goals import GoalRepository
from app.services.chat import ChatService


def make_service(goals=None, accomplishments=None, reply_text="Great question!"):
    conversation_repository = AsyncMock(spec=ConversationRepository)
    goal_repository = AsyncMock(spec=GoalRepository)
    goal_repository.list_all.return_value = goals or []
    accomplishment_repository = AsyncMock(spec=AccomplishmentRepository)
    accomplishment_repository.list_all.return_value = accomplishments or []
    anthropic_client = AsyncMock(spec=AnthropicClient)
    anthropic_client.generate_reply.return_value = reply_text

    service = ChatService(
        conversation_repository,
        goal_repository,
        accomplishment_repository,
        anthropic_client,
    )
    return service, conversation_repository, anthropic_client


def test_send_message_persists_user_and_assistant_messages() -> None:
    conversation_id = uuid.uuid4()
    service, conversation_repository, anthropic_client = make_service()
    conversation_repository.get.return_value = Conversation(id=conversation_id)
    conversation_repository.list_messages.return_value = [
        Message(conversation_id=conversation_id, role="user", content="Hi")
    ]

    result = asyncio.run(service.send_message(conversation_id, "Hi"))

    assert result is not None
    assert conversation_repository.add_message.await_count == 2
    added_roles = [
        call.args[0].role
        for call in conversation_repository.add_message.await_args_list
    ]
    assert added_roles == ["user", "assistant"]
    anthropic_client.generate_reply.assert_awaited_once()


def test_send_message_returns_none_for_missing_conversation() -> None:
    service, conversation_repository, anthropic_client = make_service()
    conversation_repository.get.return_value = None

    result = asyncio.run(service.send_message(uuid.uuid4(), "Hi"))

    assert result is None
    anthropic_client.generate_reply.assert_not_awaited()
    conversation_repository.add_message.assert_not_awaited()


def test_send_message_propagates_anthropic_errors() -> None:
    conversation_id = uuid.uuid4()
    service, conversation_repository, anthropic_client = make_service()
    conversation_repository.get.return_value = Conversation(id=conversation_id)
    conversation_repository.list_messages.return_value = []
    anthropic_client.generate_reply.side_effect = AnthropicReplyError("boom")

    try:
        asyncio.run(service.send_message(conversation_id, "Hi"))
        raised = False
    except AnthropicReplyError:
        raised = True

    assert raised
    # The user's message is still saved even though the reply failed.
    assert conversation_repository.add_message.await_count == 1


def test_system_prompt_includes_goals_and_accomplishments() -> None:
    goal = Goal(title="Land a backend role", status="active")
    accomplishment = Accomplishment(title="Shipped goal archiving")
    service, conversation_repository, anthropic_client = make_service(
        goals=[goal], accomplishments=[accomplishment]
    )
    conversation_id = uuid.uuid4()
    conversation_repository.get.return_value = Conversation(id=conversation_id)
    conversation_repository.list_messages.return_value = []

    asyncio.run(service.send_message(conversation_id, "Hi"))

    system_prompt = anthropic_client.generate_reply.await_args.kwargs["system_prompt"]
    assert "Land a backend role" in system_prompt
    assert "Shipped goal archiving" in system_prompt


def test_system_prompt_is_generic_when_profile_is_empty() -> None:
    service, conversation_repository, anthropic_client = make_service()
    conversation_id = uuid.uuid4()
    conversation_repository.get.return_value = Conversation(id=conversation_id)
    conversation_repository.list_messages.return_value = []

    asyncio.run(service.send_message(conversation_id, "Hi"))

    system_prompt = anthropic_client.generate_reply.await_args.kwargs["system_prompt"]
    assert "Current goals" not in system_prompt
    assert "Recent accomplishments" not in system_prompt
