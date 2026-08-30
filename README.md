# CareerOS

CareerOS is an AI-powered career copilot for planning and documenting career growth. The portfolio MVP currently includes persistent goals and accomplishments, Claude-powered conversations grounded in that structured career context, resume review, and mock interviews.

Authentication, per-user isolation, and a safe-by-default deployment path are in
place. See [the deployment runbook](docs/DEPLOYMENT.md) to put it online.

## Technology

- Next.js, React, TypeScript, and Tailwind CSS
- FastAPI, SQLAlchemy, Alembic, and Python
- PostgreSQL 17 with `pgvector`, in Docker Compose locally
- Anthropic Claude API for coaching, resume review, and interviews
- Voyage AI embeddings for document search
- S3-compatible object storage for uploaded documents in deployments

## How the current app works

```text
Browser -> Next.js -> FastAPI -> PostgreSQL (records + pgvector embeddings)
                         |
                         |-> Object storage (uploaded documents)
                         |-> Anthropic Claude
                         `-> Voyage AI
```

PostgreSQL owns the saved goals, accomplishments, conversations, messages, and
document embeddings. FastAPI validates requests and contains the application
logic. Next.js renders the interface and uses server actions to communicate with
FastAPI, signing a short-lived identity header on every call. Provider API keys
stay in the backend environment and are never sent to browser code.

## One-time setup

You need Node.js, Python 3.12 or newer, Docker Desktop, a Google OAuth client,
and `make`. On macOS, `make` is included with the Xcode command-line tools.

From the repository root:

```bash
make setup
```

`make setup` creates both ignored environment files and generates the required
local secrets without printing them. It never replaces existing values. Create a
Google OAuth client, use
`http://localhost:3000/api/auth/callback/google` as its authorized redirect URI,
and add its client ID and secret to `frontend/.env.local` as `AUTH_GOOGLE_ID` and
`AUTH_GOOGLE_SECRET`. Add `ANTHROPIC_API_KEY` to the root `.env` file to enable
live AI replies, and `VOYAGE_API_KEY` to enable document search. Without a Voyage
key, uploads still succeed but the copilot answers from goals and accomplishments
only. Never commit either environment file.

Run `make configure` again at any time to create missing files or secrets safely.

## Run the app

Keep Docker Desktop open, then use three VS Code terminals from the repository root.

Terminal 1 starts PostgreSQL, then applies database migrations:

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

Open [http://localhost:3000](http://localhost:3000) for the dashboard, [http://localhost:3000/documents](http://localhost:3000/documents) for document uploads, [http://localhost:3000/chat](http://localhost:3000/chat) for the career copilot, [http://localhost:3000/resume-reviews](http://localhost:3000/resume-reviews) for resume feedback, and [http://localhost:3000/interviews](http://localhost:3000/interviews) for mock interviews. FastAPI's interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

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

Check current production dependency advisories separately when online:

```bash
make security-check
```

Two maintenance commands are available once the app is running:

```bash
make reindex                          # rebuild embeddings from stored text
make claim-owner OWNER=google:1234    # move pre-auth records to an account
```

## Repository layout

```text
career-os-app/
├── backend/         # FastAPI application, migrations, tests, and deploy config
├── docs/            # Architecture decisions and roadmap
├── frontend/        # Next.js application
├── compose.yaml     # Local PostgreSQL service
├── Makefile         # Short, repeatable development commands
└── README.md
```

See [the architecture](docs/ARCHITECTURE.md) for system boundaries and [the roadmap](docs/ROADMAP.md) for the incremental build plan.
See [the security policy](docs/SECURITY.md) before deploying or using real career
documents, and [the deployment runbook](docs/DEPLOYMENT.md) to put CareerOS
online.

## Current milestone

Checkpoints 1 through 6 are complete: goals and accomplishments, persistent
Claude chat, document ingestion with grounded retrieval, resume review, and mock
interviews.

Checkpoint 7 is functionally complete. Google authentication with an optional
allowlist, per-user isolation across every resource, per-user rate limits,
document deletion, fail-closed production settings, structured logging, pgvector
document search, object storage for uploads, a production container image, CI,
and a deployment runbook are all in place. What remains is running the deployment
itself, then accessibility and responsive polish.
