# CareerOS

CareerOS is an AI-powered career copilot for planning and documenting career growth. The portfolio MVP currently includes persistent goals and accomplishments plus Claude-powered conversations grounded in that structured career context.

Planned capabilities include resume feedback, document-grounded retrieval, mock interviews, and recommendations for what to learn next.

## Technology

- Next.js, React, TypeScript, and Tailwind CSS
- FastAPI, SQLAlchemy, Alembic, and Python
- PostgreSQL 17 in Docker Compose
- Anthropic Claude API
- Chroma vector storage for document embeddings

## How the current app works

```text
Browser -> Next.js -> FastAPI -> PostgreSQL
                         |
                         `-> Anthropic Claude
```

PostgreSQL owns the saved goals, accomplishments, conversations, and messages. FastAPI validates requests and contains the application logic. Next.js renders the interface and uses server actions to communicate with FastAPI. The Anthropic API key stays in the backend environment and is never sent to browser code.

## One-time setup

You need Node.js, Python 3.12 or newer, Docker Desktop, and `make`. On macOS, `make` is included with the Xcode command-line tools.

From the repository root:

```bash
make setup
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Replace `ANTHROPIC_API_KEY` in the ignored root `.env` file to enable live copilot replies. You can also override `ANTHROPIC_MODEL`; the local default is Claude Sonnet 5. Never commit either copied environment file.

## Run the app

Keep Docker Desktop open, then use three VS Code terminals from the repository root.

Terminal 1 starts PostgreSQL and ChromaDB, then applies database migrations:

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

Open [http://localhost:3000](http://localhost:3000) for the dashboard and [http://localhost:3000/chat](http://localhost:3000/chat) for the career copilot. FastAPI's interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

Stop either development server with `Control-C`. Stop PostgreSQL and ChromaDB without deleting saved data with:

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

Checkpoint 4 document ingestion and grounded chat are complete. Validated uploads are stored locally, their metadata and extracted text are saved in PostgreSQL, and overlapping chunks are embedded and indexed in ChromaDB. Chat searches all indexed documents, gives Claude only chunks that clear a configurable semantic-relevance threshold, and persists and displays the sources used for each grounded response.
