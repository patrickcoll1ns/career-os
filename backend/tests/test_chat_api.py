import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.api.routes.chat import get_chat_service
from app.integrations.anthropic_client import AnthropicReplyError
from app.main import app
from app.services.chat import ChatService

client = TestClient(app)


def conversation_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "title": None,
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
        "updated_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def message_record(**overrides):
    values = {
        "id": uuid.uuid4(),
        "role": "user",
        "content": "Hello",
        "sources": [],
        "created_at": datetime(2026, 8, 8, tzinfo=UTC),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_create_conversation() -> None:
    service = AsyncMock(spec=ChatService)
    service.create_conversation.return_value = conversation_record()
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.post("/chat/conversations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    service.create_conversation.assert_awaited_once()


def test_list_conversations() -> None:
    service = AsyncMock(spec=ChatService)
    service.list_conversations.return_value = [conversation_record()]
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.get("/chat/conversations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_conversation() -> None:
    conversation_id = uuid.uuid4()
    service = AsyncMock(spec=ChatService)
    service.get_conversation_with_messages.return_value = (
        conversation_record(id=conversation_id),
        [message_record()],
    )
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.get(f"/chat/conversations/{conversation_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1


def test_get_conversation_returns_not_found() -> None:
    service = AsyncMock(spec=ChatService)
    service.get_conversation_with_messages.return_value = None
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.get(f"/chat/conversations/{uuid.uuid4()}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_send_message() -> None:
    conversation_id = uuid.uuid4()
    service = AsyncMock(spec=ChatService)
    service.send_message.return_value = (
        conversation_record(id=conversation_id),
        [
            message_record(role="user"),
            message_record(
                role="assistant",
                content="Hi there",
                sources=[
                    {
                        "document_id": str(uuid.uuid4()),
                        "filename": "resume.pdf",
                        "chunk_index": 2,
                    }
                ],
            ),
        ],
    )
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.post(
            f"/chat/conversations/{conversation_id}/messages",
            json={"content": "How should I prep for interviews?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 2
    assert response.json()["messages"][1]["sources"][0]["filename"] == "resume.pdf"
    service.send_message.assert_awaited_once_with(
        conversation_id, "How should I prep for interviews?"
    )


def test_send_message_rejects_blank_content() -> None:
    response = client.post(
        f"/chat/conversations/{uuid.uuid4()}/messages",
        json={"content": "   "},
    )

    assert response.status_code == 422


def test_send_message_returns_not_found_for_missing_conversation() -> None:
    service = AsyncMock(spec=ChatService)
    service.send_message.return_value = None
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.post(
            f"/chat/conversations/{uuid.uuid4()}/messages",
            json={"content": "Hello"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_send_message_returns_bad_gateway_when_claude_fails() -> None:
    service = AsyncMock(spec=ChatService)
    service.send_message.side_effect = AnthropicReplyError("boom")
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        response = client.post(
            f"/chat/conversations/{uuid.uuid4()}/messages",
            json={"content": "Hello"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
