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


def main() -> None:
    ensure_file(BACKEND_ENV, ROOT / ".env.example")
    ensure_file(FRONTEND_ENV, ROOT / "frontend" / ".env.example")

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
