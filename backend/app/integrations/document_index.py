import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_owner_id
from app.core.config import settings
from app.integrations.document_chunker import DocumentChunk
from app.integrations.embeddings import VoyageEmbedder
from app.models.document_chunk import DocumentChunkRecord

logger = logging.getLogger("careeros.document_index")


@dataclass(frozen=True)
class RetrievedDocumentChunk:
    document_id: str
    filename: str
    chunk_index: int
    text: str
    distance: float


class DocumentVectorIndex:
    """Store and search document chunk embeddings inside PostgreSQL.

    Keeping vectors in the authoritative database means retrieval is covered by
    the same ownership filter, transaction, and backup as everything else, and
    removes a second stateful service from the deployment.
    """

    def __init__(
        self,
        session: AsyncSession,
        embedder: VoyageEmbedder | None = None,
        max_distance: float | None = None,
    ) -> None:
        self.session = session
        self.embedder = embedder or VoyageEmbedder()
        self.max_distance = (
            settings.retrieval_max_distance if max_distance is None else max_distance
        )
        self.owner_id = get_current_owner_id()

    async def index(
        self,
        document_id: uuid.UUID,
        filename: str,
        chunks: list[DocumentChunk],
    ) -> None:
        """Replace every stored chunk for one document."""
        await self._delete_chunks(document_id)
        if not chunks or not self.embedder.is_configured:
            if chunks:
                # A document without embeddings is still readable and reviewable;
                # only copilot retrieval is unavailable. Failing the upload here
                # would take resume review down with it.
                logger.warning(
                    "Skipping document indexing because no embedding key is set",
                    extra={"document_id": str(document_id)},
                )
            await self.session.commit()
            return

        vectors = await self.embedder.embed_documents([chunk.text for chunk in chunks])
        self.session.add_all(
            [
                DocumentChunkRecord(
                    owner_id=self.owner_id,
                    document_id=document_id,
                    chunk_index=chunk.index,
                    filename=filename,
                    text=chunk.text,
                    embedding=vector,
                )
                for chunk, vector in zip(chunks, vectors, strict=True)
            ]
        )
        await self.session.commit()

    async def delete_document(self, document_id: uuid.UUID) -> None:
        await self._delete_chunks(document_id)
        await self.session.commit()

    async def search(self, query: str, limit: int = 5) -> list[RetrievedDocumentChunk]:
        if not self.embedder.is_configured:
            return []

        query_vector = await self.embedder.embed_query(query)
        distance = DocumentChunkRecord.embedding.cosine_distance(query_vector)
        result = await self.session.execute(
            select(DocumentChunkRecord, distance.label("distance"))
            .where(
                DocumentChunkRecord.owner_id == self.owner_id,
                distance <= self.max_distance,
            )
            .order_by(distance)
            .limit(limit)
        )

        return [
            RetrievedDocumentChunk(
                document_id=str(record.document_id),
                filename=record.filename,
                chunk_index=record.chunk_index,
                text=record.text,
                distance=float(chunk_distance),
            )
            for record, chunk_distance in result.all()
        ]

    async def _delete_chunks(self, document_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(DocumentChunkRecord).where(
                DocumentChunkRecord.owner_id == self.owner_id,
                DocumentChunkRecord.document_id == document_id,
            )
        )
