# CareerOS

CareerOS is an AI-powered career copilot for planning and documenting career growth. The portfolio MVP currently includes a working dashboard where career goals are stored in PostgreSQL through a FastAPI API and displayed by a Next.js frontend.

Planned capabilities include personalized guidance, accomplishment tracking, persistent Claude conversations, resume feedback, mock interviews, and retrieval-augmented responses grounded in uploaded career documents.

## Technology

- Next.js, React, TypeScript, and Tailwind CSS
- FastAPI, SQLAlchemy, Alembic, and Python
- PostgreSQL 17 in Docker Compose
- Anthropic Claude API (planned)
- Chroma vector storage for RAG (planned)

## How the current app works

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
```

PostgreSQL owns the saved goal data. FastAPI validates requests and contains the application logic. Next.js renders the interface and sends goal actions to FastAPI.

## One-time setup

You need Node.js, Python 3.12 or newer, Docker Desktop, and `make`. On macOS, `make` is included with the Xcode command-line tools.

From the repository root:

```bash
make setup
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

The sample environment values are safe local-development defaults. Add a real Anthropic key only when the Claude integration is implemented. Never commit either copied environment file.

## Run the app

Keep Docker Desktop open, then use three VS Code terminals from the repository root.

Terminal 1 starts PostgreSQL and applies database migrations:

```bash
make database
```

Terminal 2 starts FastAPI:

```bash
make backend
```

Terminal 3 starts Next.js:

```bash
make frontend
```

Open [http://localhost:3000](http://localhost:3000) for the app. FastAPI's interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Stop either development server with `Control-C`. Stop PostgreSQL without deleting saved data with:

```bash
make database-stop
```

## Quality checks

Run all backend and frontend checks from the repository root:

```bash
make check
```

This checks Python formatting and lint rules, runs backend tests, lints the frontend, and creates a production frontend build.

## Repository layout

```text
career-os-app/
├── backend/         # FastAPI application, migrations, and tests
├── docs/            # Architecture decisions and roadmap
├── frontend/        # Next.js application
├── compose.yaml     # Local PostgreSQL service
├── Makefile         # Short, repeatable development commands
└── README.md
```

See [the architecture](docs/ARCHITECTURE.md) for system boundaries and [the roadmap](docs/ROADMAP.md) for the incremental build plan.

## Current milestone

The goal model, migration, create/list/update/archive/restore API, and goal dashboard are working. Goals are soft-deleted (an `archived_at` timestamp) so history is never lost; the dashboard shows archived goals separately with a restore action. The next useful increment is completing the goal-management experience (editable title/description/target date) before introducing Claude conversations and RAG.
