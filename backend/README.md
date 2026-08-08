# CareerOS API

FastAPI backend for CareerOS.

## Local setup

Create and activate a virtual environment from this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the application and development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Start PostgreSQL from the repository root:

```bash
docker compose up -d postgres
```

Apply pending database migrations from the backend directory:

```bash
alembic upgrade head
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API is available at [http://localhost:8000](http://localhost:8000), with interactive documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

Health endpoints:

- `/health` checks whether FastAPI is running.
- `/health/database` checks whether FastAPI can query PostgreSQL.

Goal endpoints:

- `POST /goals` validates and creates a career goal.
- `GET /goals` lists goals with the newest first.
- `PATCH /goals/{goal_id}` updates selected fields on an existing goal.

## Run tests

```bash
pytest
```

The automated tests mock external infrastructure. A live PostgreSQL connection is verified separately during local setup.
