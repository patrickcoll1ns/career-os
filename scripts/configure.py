"""Create safe local environment files without printing or replacing secrets."""

import secrets
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ENV = ROOT / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env.local"


def ensure_file(destination: Path, template: Path) -> None:
    if not destination.exists():
        shutil.copyfile(template, destination)
        print(f"Created {destination.relative_to(ROOT)}")
    destination.chmod(0o600)


def read_value(path: Path, key: str) -> str:
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return ""


def set_blank_value(path: Path, key: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = f"{key}="
    updated = False
    for index, line in enumerate(lines):
        if line == prefix:
            lines[index] = f"{prefix}{value}"
            updated = True
            break
    if not updated and not any(line.startswith(prefix) for line in lines):
        lines.append(f"{prefix}{value}")
        updated = True
    if updated:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_values(path: Path, keys: set[str]) -> None:
    prefixes = tuple(f"{key}=" for key in keys)
    lines = path.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in lines if not line.startswith(prefixes)]
    if filtered != lines:
        path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


# Settings that must exist locally for the fail-closed production defaults not
# to block development. Missing keys are appended; existing values are kept.
LOCAL_BACKEND_DEFAULTS = {
    "ENVIRONMENT": "development",
    "EXPOSE_API_DOCS": "true",
    "DOCUMENT_STORAGE_BACKEND": "local",
    "BACKEND_CORS_ORIGINS": "http://localhost:3000",
    "VOYAGE_MODEL": "voyage-3.5",
}
OBSOLETE_BACKEND_KEYS = {
    "CHROMA_HOST",
    "CHROMA_PORT",
    "CHROMA_COLLECTION",
    "CHROMA_MAX_DISTANCE",
}


def main() -> None:
    ensure_file(BACKEND_ENV, ROOT / ".env.example")
    ensure_file(FRONTEND_ENV, ROOT / "frontend" / ".env.example")

    remove_values(BACKEND_ENV, OBSOLETE_BACKEND_KEYS)
    for key, value in LOCAL_BACKEND_DEFAULTS.items():
        set_blank_value(BACKEND_ENV, key, value)

    backend_internal = read_value(BACKEND_ENV, "INTERNAL_AUTH_SECRET")
    frontend_internal = read_value(FRONTEND_ENV, "INTERNAL_AUTH_SECRET")
    if backend_internal and frontend_internal and backend_internal != frontend_internal:
        raise SystemExit(
            "INTERNAL_AUTH_SECRET differs between .env and frontend/.env.local. "
            "Make the values match before starting CareerOS."
        )

    internal_secret = backend_internal or frontend_internal or secrets.token_urlsafe(48)
    set_blank_value(BACKEND_ENV, "INTERNAL_AUTH_SECRET", internal_secret)
    set_blank_value(FRONTEND_ENV, "INTERNAL_AUTH_SECRET", internal_secret)
    set_blank_value(FRONTEND_ENV, "AUTH_SECRET", secrets.token_urlsafe(48))
    set_blank_value(FRONTEND_ENV, "AUTH_GOOGLE_ID", "")
    set_blank_value(FRONTEND_ENV, "AUTH_GOOGLE_SECRET", "")
    set_blank_value(FRONTEND_ENV, "AUTH_ALLOWED_EMAILS", "")
    remove_values(FRONTEND_ENV, {"AUTH_GITHUB_ID", "AUTH_GITHUB_SECRET"})

    missing = [
        key
        for key in ("AUTH_GOOGLE_ID", "AUTH_GOOGLE_SECRET")
        if not read_value(FRONTEND_ENV, key)
    ]
    print("Local secrets are configured and were not printed.")
    if missing:
        print(
            "Next: add AUTH_GOOGLE_ID and AUTH_GOOGLE_SECRET to "
            "frontend/.env.local."
        )
        print(
            "Google redirect URI: "
            "http://localhost:3000/api/auth/callback/google"
        )


if __name__ == "__main__":
    main()
