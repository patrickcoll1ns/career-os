from app.models.conversation import Conversation
from app.models.message import Message


def test_conversation_table_has_expected_columns() -> None:
    assert set(Conversation.__table__.columns.keys()) == {
        "id",
        "title",
        "created_at",
        "updated_at",
    }


def test_message_table_has_expected_columns() -> None:
    assert set(Message.__table__.columns.keys()) == {
        "id",
        "conversation_id",
        "role",
        "content",
        "sources",
        "created_at",
    }


def test_message_role_is_constrained() -> None:
    constraint_names = {constraint.name for constraint in Message.__table__.constraints}

    assert "ck_messages_role" in constraint_names
