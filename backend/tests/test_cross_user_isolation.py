"""Every resource must be invisible to an owner who does not own it.

These tests run the real repositories against a real database so the ownership
filters are exercised as SQL, not as mocks. `document_chunks` is left out
because its pgvector column has no SQLite equivalent; that table's ownership
filter is covered by tests/test_document_index.py.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.auth import owner_context
from app.db.base import Base
from app.models.accomplishment import Accomplishment
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.goal import Goal
from app.models.interview import InterviewSession, InterviewTurn
from app.models.message import Message
from app.models.resume_review import ResumeReview
from app.repositories.accomplishments import AccomplishmentRepository
from app.repositories.chat import ConversationRepository
from app.repositories.documents import DocumentRepository
from app.repositories.goals import GoalRepository
from app.repositories.interviews import InterviewRepository
from app.repositories.resume_reviews import ResumeReviewRepository

OWNER = "google:owner"
INTRUDER = "google:intruder"

ISOLATED_TABLES = [
    Goal.__table__,
    Accomplishment.__table__,
    Conversation.__table__,
    Message.__table__,
    Document.__table__,
    ResumeReview.__table__,
    InterviewSession.__table__,
    InterviewTurn.__table__,
]


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=ISOLATED_TABLES)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as database_session:
        yield database_session
    await engine.dispose()


def make_document() -> Document:
    return Document(
        original_filename="resume.pdf",
        content_type="application/pdf",
        size_bytes=10,
        sha256="a" * 64,
        storage_key=f"{uuid.uuid4()}.pdf",
        status="ready",
        extracted_text="Backend engineer",
    )


async def test_goals_are_invisible_to_another_owner(session) -> None:
    with owner_context(OWNER):
        goal = await GoalRepository(session).add(Goal(title="Ship CareerOS"))

    with owner_context(INTRUDER):
        repository = GoalRepository(session)
        assert await repository.get(goal.id) is None
        assert await repository.list_all() == []
        assert await repository.list_archived() == []


async def test_accomplishments_are_invisible_to_another_owner(session) -> None:
    with owner_context(OWNER):
        accomplishment = await AccomplishmentRepository(session).add(
            Accomplishment(title="Led a migration")
        )

    with owner_context(INTRUDER):
        repository = AccomplishmentRepository(session)
        assert await repository.get(accomplishment.id) is None
        assert await repository.list_all() == []


async def test_conversations_and_messages_are_invisible_to_another_owner(
    session,
) -> None:
    with owner_context(OWNER):
        repository = ConversationRepository(session)
        conversation = await repository.add(Conversation(title="Career plan"))
        await repository.add_exchange(
            conversation,
            Message(conversation_id=conversation.id, role="user", content="Hi"),
            Message(conversation_id=conversation.id, role="assistant", content="Hello"),
        )

    with owner_context(INTRUDER):
        repository = ConversationRepository(session)
        assert await repository.get(conversation.id) is None
        assert await repository.list_all() == []
        # Messages are authorized through their parent conversation.
        assert await repository.list_messages(conversation.id) == []


async def test_documents_are_invisible_to_another_owner(session) -> None:
    with owner_context(OWNER):
        document = await DocumentRepository(session).add(make_document())

    with owner_context(INTRUDER):
        repository = DocumentRepository(session)
        assert await repository.get(document.id) is None
        assert await repository.list_all() == []


async def test_resume_reviews_are_invisible_to_another_owner(session) -> None:
    with owner_context(OWNER):
        document = await DocumentRepository(session).add(make_document())
        review = await ResumeReviewRepository(session).add(
            ResumeReview(document_id=document.id, status="completed")
        )

    with owner_context(INTRUDER):
        repository = ResumeReviewRepository(session)
        assert await repository.get(review.id) is None
        assert await repository.list_all() == []


async def test_interview_sessions_and_turns_are_invisible_to_another_owner(
    session,
) -> None:
    with owner_context(OWNER):
        repository = InterviewRepository(session)
        interview = await repository.add_session(
            InterviewSession(
                target_role="Staff Engineer",
                interview_type="behavioral",
                difficulty="intermediate",
                question_limit=1,
                status="active",
            )
        )
        await repository.add_turn(
            InterviewTurn(
                session_id=interview.id,
                sequence_number=1,
                question="Tell me about a hard project.",
            )
        )

    with owner_context(INTRUDER):
        repository = InterviewRepository(session)
        assert await repository.get_session(interview.id) is None
        assert await repository.list_sessions() == []
        # Turns are authorized through their parent session.
        assert await repository.list_turns(interview.id) == []


async def test_repositories_refuse_to_run_without_an_authenticated_owner(
    session,
) -> None:
    with pytest.raises(RuntimeError):
        GoalRepository(session)
