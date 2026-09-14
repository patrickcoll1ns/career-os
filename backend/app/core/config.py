from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_DIRECTORY.parent
MINIMUM_SECRET_LENGTH = 32


class Settings(BaseSettings):
    app_name: str = "CareerOS API"

    # Every security-relevant default is the safe one. A deployment that forgets
    # to set a variable fails closed instead of silently serving every user's
    # data to anonymous callers.
    environment: Literal["development", "production", "test"] = "production"
    expose_api_docs: bool = False
    internal_auth_secret: SecretStr | None = None

    backend_cors_origins: str = ""
    database_url: str = "postgresql+asyncpg://careeros:careeros@localhost:5432/careeros"
    database_pool_size: int = 5
    database_max_overflow: int = 5
    # asyncpg caches prepared statements, which breaks behind a transaction-mode
    # pooler such as PgBouncer or a Neon/Supabase pooled endpoint. Set to 0 there.
    database_statement_cache_size: int = 100
    log_level: str = "INFO"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-sonnet-5"

    voyage_api_key: SecretStr | None = None
    voyage_model: str = "voyage-3.5"
    embedding_dimensions: int = 1024
    retrieval_max_distance: float = 0.6

    document_storage_backend: Literal["local", "s3"] = "local"
    document_upload_directory: Path = REPOSITORY_ROOT / "data" / "uploads"
    max_document_size_bytes: int = 5 * 1024 * 1024
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None

    rate_limit_window_seconds: int = 3600
    rate_limit_ai_requests: int = 60
    rate_limit_upload_requests: int = 20

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIRECTORY / ".env", REPOSITORY_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def allows_unsigned_requests(self) -> bool:
        """Whether anonymous local callers may act as the development owner."""
        return not self.is_production

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if not self.is_production:
            return self

        secret = self.internal_auth_secret
        if secret is None or len(secret.get_secret_value()) < MINIMUM_SECRET_LENGTH:
            raise ValueError(
                "INTERNAL_AUTH_SECRET must contain at least "
                f"{MINIMUM_SECRET_LENGTH} characters in production. Set it to the "
                "same value in the backend and frontend environments, or set "
                "ENVIRONMENT=development for local work."
            )
        if self.document_storage_backend == "s3" and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when DOCUMENT_STORAGE_BACKEND=s3.")
        if self.document_storage_backend == "s3" and self.s3_endpoint_url:
            endpoint = self.s3_endpoint_url
            parsed_endpoint = urlsplit(endpoint)
            has_forbidden_characters = any(
                character in endpoint for character in ('<', '>', '"', "'", " ")
            )
            if (
                has_forbidden_characters
                or parsed_endpoint.scheme != "https"
                or not parsed_endpoint.hostname
                or parsed_endpoint.username is not None
                or parsed_endpoint.password is not None
                or parsed_endpoint.query
                or parsed_endpoint.fragment
            ):
                raise ValueError(
                    "S3_ENDPOINT_URL must be a valid HTTPS URL without placeholder "
                    "brackets, quotes, credentials, query parameters, or fragments."
                )
        insecure_origins = [
            origin for origin in self.cors_origins if not origin.startswith("https://")
        ]
        if insecure_origins:
            raise ValueError(
                "BACKEND_CORS_ORIGINS must list only https:// origins in "
                f"production. Remove: {', '.join(insecure_origins)}"
            )
        return self


def reveal(secret: SecretStr | None) -> str | None:
    """Unwrap a secret at the point of use.

    Every credential is a `SecretStr` so that a settings repr — which pydantic
    includes in startup validation errors — cannot print it.
    """
    return secret.get_secret_value() if secret else None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
