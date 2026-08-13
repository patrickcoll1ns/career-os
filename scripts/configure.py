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

    missing = [
        key
        for key in ("AUTH_GITHUB_ID", "AUTH_GITHUB_SECRET")
        if not read_value(FRONTEND_ENV, key)
    ]
    print("Local secrets are configured and were not printed.")
    if missing:
        print(
            "Next: add AUTH_GITHUB_ID and AUTH_GITHUB_SECRET to "
            "frontend/.env.local."
        )
        print(
            "GitHub callback URL: "
            "http://localhost:3000/api/auth/callback/github"
        )


if __name__ == "__main__":
    main()
