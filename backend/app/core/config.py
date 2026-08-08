from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    app_name: str = "CareerOS API"
    backend_cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://careeros:careeros@localhost:5432/careeros"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
