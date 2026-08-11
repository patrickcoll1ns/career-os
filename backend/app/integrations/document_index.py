import uuid
from dataclasses import dataclass

import chromadb

from app.integrations.document_chunker import DocumentChunk


@dataclass(frozen=True)
class RetrievedDocumentChunk:
    document_id: str
    filename: str
    chunk_index: int
    text: str


class DocumentVectorIndex:
    """Store rebuildable document chunks in a Chroma collection."""

    def __init__(
        self,
        host: str,
        port: int,
        collection_name: str = "career_documents",
    ) -> None:
        self.client = chromadb.HttpClient(host=host, port=port)
        self.collection_name = collection_name

    def index(
        self,
        document_id: uuid.UUID,
        filename: str,
        chunks: list[DocumentChunk],
    ) -> None:
        collection = self.client.get_or_create_collection(self.collection_name)
        document_id_text = str(document_id)
        collection.delete(where={"document_id": document_id_text})

        if not chunks:
            return

        collection.add(
            ids=[f"{document_id_text}:{chunk.index}" for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "document_id": document_id_text,
                    "filename": filename,
                    "chunk_index": chunk.index,
                }
                for chunk in chunks
            ],
        )

    def search(self, query: str, limit: int = 5) -> list[RetrievedDocumentChunk]:
        collection = self.client.get_or_create_collection(self.collection_name)
        result = collection.query(query_texts=[query], n_results=limit)
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]

        return [
            RetrievedDocumentChunk(
                document_id=str(metadata["document_id"]),
                filename=str(metadata["filename"]),
                chunk_index=int(metadata["chunk_index"]),
                text=document,
            )
            for document, metadata in zip(documents, metadatas, strict=True)
        ]
