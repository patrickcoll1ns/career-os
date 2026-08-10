PYTHON ?= python3
VENV := backend/.venv
VENV_BIN := $(VENV)/bin

.PHONY: setup database database-stop database-status migrate backend frontend backend-check frontend-check check

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/python -m pip install -e "backend[dev]"
	npm --prefix frontend install

database:
	docker compose up -d --wait postgres chroma
	cd backend && .venv/bin/alembic upgrade head

database-stop:
	docker compose down

database-status:
	docker compose ps

migrate:
	cd backend && .venv/bin/alembic upgrade head

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

check: backend-check frontend-check
