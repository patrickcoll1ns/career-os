from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    app_name: str = "CareerOS API"
    backend_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://careeros:careeros@localhost:5432/careeros"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "career_documents"
    chroma_max_distance: float = 1.6
    document_upload_directory: Path = REPOSITORY_ROOT / "data" / "uploads"
    max_document_size_bytes: int = 5 * 1024 * 1024
    expose_api_docs: bool = True
    environment: Literal["development", "production", "test"] = "development"
    internal_auth_secret: SecretStr | None = None

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

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment == "production" and (
            self.internal_auth_secret is None
            or len(self.internal_auth_secret.get_secret_value()) < 32
        ):
            raise ValueError(
                "INTERNAL_AUTH_SECRET must contain at least 32 characters "
                "in production."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
