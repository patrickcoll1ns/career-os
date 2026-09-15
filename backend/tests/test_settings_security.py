"""The deployment defaults must be the safe ones.

A forgotten environment variable should stop the app, never silently open it.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

STRONG_SECRET = "a" * 32


def test_defaults_are_fail_closed() -> None:
    fields = Settings.model_fields
    assert fields["environment"].default == "production"
    assert fields["expose_api_docs"].default is False
    assert fields["backend_cors_origins"].default == ""


def test_production_requires_a_strong_internal_auth_secret() -> None:
    with pytest.raises(ValidationError, match="INTERNAL_AUTH_SECRET"):
        Settings(
            environment="production",
            internal_auth_secret=None,
            backend_cors_origins="https://careeros.example.com",
        )


def test_production_rejects_a_short_internal_auth_secret() -> None:
    with pytest.raises(ValidationError, match="INTERNAL_AUTH_SECRET"):
        Settings(
            environment="production",
            internal_auth_secret="too-short",
            backend_cors_origins="https://careeros.example.com",
        )


def test_production_rejects_plaintext_cors_origins() -> None:
    with pytest.raises(ValidationError, match="https://"):
        Settings(
            environment="production",
            internal_auth_secret=STRONG_SECRET,
            backend_cors_origins="http://localhost:3000",
        )


def test_production_requires_a_bucket_for_object_storage() -> None:
    with pytest.raises(ValidationError, match="S3_BUCKET"):
        Settings(
            environment="production",
            internal_auth_secret=STRONG_SECRET,
            backend_cors_origins="https://careeros.example.com",
            document_storage_backend="s3",
            s3_bucket=None,
        )


@pytest.mark.parametrize(
    "endpoint",
    [
        "<https://accountid.r2.cloudflarestorage.com>",
        '"https://accountid.r2.cloudflarestorage.com"',
        "http://accountid.r2.cloudflarestorage.com",
    ],
)
def test_production_rejects_a_malformed_object_storage_endpoint(
    endpoint: str,
) -> None:
    with pytest.raises(ValidationError, match="S3_ENDPOINT_URL"):
        Settings(
            environment="production",
            internal_auth_secret=STRONG_SECRET,
            backend_cors_origins="https://careeros.example.com",
            document_storage_backend="s3",
            s3_bucket="careeros-documents",
            s3_endpoint_url=endpoint,
        )


def test_a_complete_production_configuration_is_accepted() -> None:
    settings = Settings(
        environment="production",
        internal_auth_secret=STRONG_SECRET,
        backend_cors_origins="https://careeros.example.com, https://www.example.com",
        document_storage_backend="s3",
        s3_bucket="careeros-documents",
    )

    assert settings.is_production
    assert not settings.allows_unsigned_requests
    assert settings.cors_origins == [
        "https://careeros.example.com",
        "https://www.example.com",
    ]


def test_development_allows_unsigned_local_requests() -> None:
    settings = Settings(environment="development", internal_auth_secret=None)

    assert settings.allows_unsigned_requests
