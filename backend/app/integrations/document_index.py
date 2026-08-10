import uuid

import chromadb

from app.integrations.document_chunker import DocumentChunk


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
