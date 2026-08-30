import asyncio
import logging

import httpx

from app.core.config import reveal, settings

logger = logging.getLogger("careeros.embeddings")

VOYAGE_EMBEDDINGS_URL = "https://api.voyageai.com/v1/embeddings"

# Voyage accepts up to 1000 inputs per request, but the per-request token
# ceiling binds first. Chunks are capped at 1200 characters, so 64 of them stay
# far inside the limit while keeping the number of round trips small.
MAX_TEXTS_PER_REQUEST = 64
REQUEST_TIMEOUT_SECONDS = 60.0
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.5
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class EmbeddingError(RuntimeError):
    """Raised when text could not be turned into vectors."""


class VoyageEmbedder:
    """Turn text into vectors with Voyage AI's embeddings API.

    The REST endpoint is called directly so the backend image stays small and
    the wire format is pinned by this file rather than by an SDK release.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.api_key = api_key or reveal(settings.voyage_api_key)
        self.model = model or settings.voyage_model
        self.dimensions = dimensions or settings.embedding_dimensions

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, "document")

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self._embed([text], "query")
        return vectors[0]

    async def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        if not self.is_configured:
            raise EmbeddingError(
                "VOYAGE_API_KEY is not configured, so documents cannot be indexed."
            )

        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            for start in range(0, len(texts), MAX_TEXTS_PER_REQUEST):
                batch = texts[start : start + MAX_TEXTS_PER_REQUEST]
                vectors.extend(await self._embed_batch(client, batch, input_type))

        if len(vectors) != len(texts):
            raise EmbeddingError("Voyage returned an unexpected number of vectors.")
        return vectors

    async def _embed_batch(
        self, client: httpx.AsyncClient, batch: list[str], input_type: str
    ) -> list[list[float]]:
        payload = {
            "input": batch,
            "model": self.model,
            "input_type": input_type,
            "output_dimension": self.dimensions,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_error: Exception | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = await client.post(
                    VOYAGE_EMBEDDINGS_URL, json=payload, headers=headers
                )
                if response.status_code in RETRYABLE_STATUS_CODES:
                    raise EmbeddingError(
                        f"Voyage returned status {response.status_code}."
                    )
                response.raise_for_status()
                return self._parse(response.json(), len(batch))
            except (httpx.HTTPError, EmbeddingError) as error:
                last_error = error
                if attempt == MAX_ATTEMPTS:
                    break
                logger.warning(
                    "Retrying Voyage embedding request",
                    extra={"attempt": attempt, "batch_size": len(batch)},
                )
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise EmbeddingError(
            "CareerOS could not reach the embedding service."
        ) from last_error

    def _parse(self, body: dict, expected_count: int) -> list[list[float]]:
        data = body.get("data")
        if not isinstance(data, list) or len(data) != expected_count:
            raise EmbeddingError("Voyage returned a malformed embedding response.")

        # Voyage documents the results as ordered, but the index is authoritative.
        ordered = sorted(data, key=lambda item: item.get("index", 0))
        vectors: list[list[float]] = []
        for item in ordered:
            embedding = item.get("embedding")
            if not isinstance(embedding, list) or len(embedding) != self.dimensions:
                raise EmbeddingError(
                    "Voyage returned an embedding with unexpected dimensions."
                )
            vectors.append([float(value) for value in embedding])
        return vectors
