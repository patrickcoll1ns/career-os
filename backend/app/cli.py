"""Maintenance commands for a deployed CareerOS backend.

Run with `python -m app.cli <command>` inside the backend environment, or
through the `make reindex` / `make claim-owner` targets.
"""

import argparse
import asyncio
import sys

from sqlalchemy import func, select, update

from app.core.auth import DEVELOPMENT_OWNER_ID, owner_context
from app.db.session import async_session_factory, engine
from app.integrations.document_chunker import DocumentChunker
from app.integrations.document_index import DocumentVectorIndex
from app.models.accomplishment import Accomplishment
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.goal import Goal
from app.models.interview import InterviewSession
from app.models.resume_review import ResumeReview

OWNED_MODELS = (
    Goal,
    Accomplishment,
    Conversation,
    Document,
    ResumeReview,
    InterviewSession,
)


async def reindex_documents() -> int:
    """Rebuild every document's embeddings from its stored extracted text."""
    chunker = DocumentChunker()
    reindexed = 0

    async with async_session_factory() as session:
        documents = (
            await session.scalars(
                select(Document).where(Document.extracted_text.is_not(None))
            )
        ).all()

        for document in documents:
            with owner_context(document.owner_id):
                index = DocumentVectorIndex(session)
                chunks = chunker.split(document.extracted_text or "")
                await index.index(document.id, document.original_filename, chunks)
                print(f"Reindexed {document.original_filename} ({len(chunks)} chunks)")
            reindexed += 1

    return reindexed


async def list_owners() -> list[tuple[str, int]]:
    """Report which owner IDs hold records, so one can be named for a claim.

    Owner IDs are deliberately absent from the request logs, so this is how a
    freshly signed-in account finds the ID to migrate records to.
    """
    totals: dict[str, int] = {}
    async with async_session_factory() as session:
        for model in OWNED_MODELS:
            result = await session.execute(
                select(model.owner_id, func.count()).group_by(model.owner_id)
            )
            for owner_id, count in result.all():
                totals[owner_id] = totals.get(owner_id, 0) + count
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


async def claim_owner(new_owner_id: str, previous_owner_id: str) -> int:
    """Reassign pre-authentication records to a real signed-in account."""
    moved = 0
    async with async_session_factory() as session:
        for model in OWNED_MODELS:
            result = await session.execute(
                update(model)
                .where(model.owner_id == previous_owner_id)
                .values(owner_id=new_owner_id)
            )
            moved += result.rowcount or 0
        await session.commit()
    return moved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="app.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("reindex", help="Rebuild document embeddings.")
    commands.add_parser(
        "owners", help="List owner IDs and how many records each holds."
    )

    claim = commands.add_parser(
        "claim-owner", help="Move records to an authenticated owner ID."
    )
    claim.add_argument(
        "--owner",
        required=True,
        help="Target owner ID, for example google:1234567890.",
    )
    claim.add_argument(
        "--from",
        dest="previous_owner",
        default=DEVELOPMENT_OWNER_ID,
        help=f"Owner ID to move records from (default: {DEVELOPMENT_OWNER_ID}).",
    )
    return parser


async def _run(arguments: argparse.Namespace) -> int:
    try:
        try:
            async with engine.connect():
                pass
        except Exception as error:
            # These commands are run by a person during a deployment; a stack
            # trace for an unreachable database helps nobody.
            print(
                "Could not reach the database. Check DATABASE_URL, and that it "
                f"uses the postgresql+asyncpg:// driver.\n  {type(error).__name__}",
                file=sys.stderr,
            )
            return 1

        if arguments.command == "reindex":
            count = await reindex_documents()
            print(f"Reindexed {count} document(s).")
            return 0

        if arguments.command == "owners":
            owners = await list_owners()
            if not owners:
                print("No records yet. Sign in and save something first.")
            for owner_id, count in owners:
                print(f"{owner_id}\t{count} record(s)")
            return 0

        moved = await claim_owner(arguments.owner, arguments.previous_owner)
        print(f"Moved {moved} record(s) to {arguments.owner}.")
        return 0
    finally:
        await engine.dispose()


def main() -> int:
    arguments = build_parser().parse_args()
    return asyncio.run(_run(arguments))


if __name__ == "__main__":
    sys.exit(main())
