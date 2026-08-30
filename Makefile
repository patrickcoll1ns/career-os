PYTHON ?= python3
VENV := backend/.venv
VENV_BIN := $(VENV)/bin
OWNER ?=

.PHONY: setup configure database database-stop database-status migrate reindex claim-owner backend frontend backend-check frontend-check security-check check

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/python -m pip install -e "backend[dev]"
	npm --prefix frontend install
	$(PYTHON) scripts/configure.py

configure:
	$(PYTHON) scripts/configure.py

database:
	docker compose up -d --wait postgres
	cd backend && .venv/bin/alembic upgrade head

database-stop:
	docker compose down

database-status:
	docker compose ps

migrate:
	cd backend && .venv/bin/alembic upgrade head

# Rebuild document embeddings from stored extracted text.
reindex:
	cd backend && .venv/bin/python -m app.cli reindex

# Move pre-authentication records to a real account: make claim-owner OWNER=google:123
claim-owner:
	@test -n "$(OWNER)" || (echo "Set OWNER, for example: make claim-owner OWNER=google:123" && exit 1)
	cd backend && .venv/bin/python -m app.cli claim-owner --owner "$(OWNER)"

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload

frontend:
	npm --prefix frontend run dev

backend-check:
	cd backend && .venv/bin/ruff format --check .
	cd backend && .venv/bin/ruff check .
	cd backend && .venv/bin/pytest

frontend-check:
	npm --prefix frontend run lint
	npm --prefix frontend run build

security-check:
	npm --prefix frontend audit --omit=dev --audit-level=low
	# The local careeros-api package is not on PyPI, so it is skipped. --strict is
	# omitted because it would turn that expected skip into a failure; pip-audit
	# still exits non-zero when a real advisory is found.
	cd backend && .venv/bin/pip-audit --skip-editable --progress-spinner off

check: backend-check frontend-check
