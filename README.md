# CareerOS

CareerOS is an AI-powered career copilot for planning and documenting career
growth. It keeps your goals and accomplishments in one workspace, reads the
resumes and career documents you upload, and uses them to ground every AI
feature: a persistent career-coaching chat, structured resume reviews, and
question-by-question mock interviews with scored feedback.

It is a full-stack application — Next.js, FastAPI, PostgreSQL with `pgvector`,
and the Anthropic and Voyage AI APIs — with Google authentication, per-user data
isolation, and a documented production deployment.

**[Try it live](https://career-os-sage-ten.vercel.app)** — sign in with Google.
Or, the [local setup](#one-time-setup) below runs the same application.

## Features

**Career dashboard.** Goals carry a short- or long-term horizon, a status of
active, paused, or completed, and an optional target date. Accomplishments form
a running journal of what you have actually delivered. Both can be edited,
archived, restored, or permanently deleted; archiving is the recoverable action
and `DELETE` is the one that is not.

**Document ingestion.** Upload a PDF, DOCX, or TXT file up to 5 MB. CareerOS
validates it, extracts the text, splits it into overlapping chunks, embeds each
chunk with Voyage AI, and stores the vectors in PostgreSQL. Deleting a document
removes its stored bytes, its embeddings, and any resume reviews built from it.

**Career copilot.** A persistent chat grounded in your structured profile and
your documents. Each question is embedded and matched against your own chunks by
cosine distance, and replies cite the sources they drew on. Conversations and
messages are saved, so context survives a restart.

**Resume review.** Point a review at one indexed document and an optional target
role. Claude returns a summary, evidence-backed strengths and gaps, and concrete
rewrite suggestions, validated against a schema and stored as review history.

**Mock interviews.** Configure a target role, an interview type of behavioral,
technical, or mixed, a difficulty, and a question limit. Each answer is scored
from 1 to 5 with specific strengths and one improvement, and the finished
session produces a debrief of strengths, improvements, and learning
recommendations.

**Accounts.** Google sign-in with an optional email allowlist. Every record,
embedding, and retrieval is filtered by owner, and per-user rate limits bound the
endpoints that cost money.

## How it works

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
FastAPI, signing a short-lived identity header on every call. The browser never
talks to FastAPI directly, and provider API keys stay in the backend environment
where browser code cannot reach them.

See [the architecture](docs/ARCHITECTURE.md) for the full system boundaries.

## Technology

- Next.js 16, React 19, TypeScript, and Tailwind CSS 4
- FastAPI, SQLAlchemy, Alembic, and Python 3.12+
- PostgreSQL 17 with `pgvector`, in Docker Compose locally
- Auth.js with Google OAuth
- Anthropic Claude API for coaching, resume review, and interviews
- Voyage AI embeddings for document search
- S3-compatible object storage for uploaded documents in deployments

## One-time setup

You need Node.js 22 or newer, Python 3.12 or newer, Docker Desktop, a Google
OAuth client, and `make`. On macOS, `make` is included with the Xcode
command-line tools.

From the repository root:

```bash
make setup
```

`make setup` installs both dependency sets, creates the two ignored environment
files, and generates the required local secrets without printing them. It never
replaces existing values, so you can run `make configure` again at any time to
fill in anything missing.

Then add your own credentials:

1. Create a Google OAuth client of type "Web application" with
   `http://localhost:3000/api/auth/callback/google` as its authorized redirect
   URI. Put its client ID and secret in `frontend/.env.local` as
   `AUTH_GOOGLE_ID` and `AUTH_GOOGLE_SECRET`.
2. Add `ANTHROPIC_API_KEY` to the root `.env` file to enable live AI replies.
3. Add `VOYAGE_API_KEY` to the root `.env` file to enable document search.
   Without a Voyage key, uploads still succeed but the copilot answers from
   goals and accomplishments only.

Never commit either environment file. Both are ignored, and `make setup` gives
them `600` permissions.

## Run the app

Keep Docker Desktop open, then use three terminals from the repository root.

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

Then open:

| Page | URL |
| --- | --- |
| Dashboard | [localhost:3000](http://localhost:3000) |
| Documents | [localhost:3000/documents](http://localhost:3000/documents) |
| Career copilot | [localhost:3000/chat](http://localhost:3000/chat) |
| Resume reviews | [localhost:3000/resume-reviews](http://localhost:3000/resume-reviews) |
| Mock interviews | [localhost:3000/interviews](http://localhost:3000/interviews) |
| API documentation | [localhost:8000/docs](http://localhost:8000/docs) |

Stop either development server with `Control-C`. Stop PostgreSQL without
deleting saved data with:

```bash
make database-stop
```

## Configuration

`make setup` writes both files from their checked-in templates, which document
every available setting. The values that matter most:

| Setting | File | Purpose |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | `.env` | Required for chat, resume review, and interviews. |
| `ANTHROPIC_MODEL` | `.env` | Defaults to `claude-sonnet-5`. |
| `VOYAGE_API_KEY` | `.env` | Optional. Enables document embedding and grounded retrieval. |
| `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` | `frontend/.env.local` | Required for sign-in. |
| `AUTH_ALLOWED_EMAILS` | `frontend/.env.local` | Optional allowlist. When empty, any Google account may sign in. |
| `INTERNAL_AUTH_SECRET` | both | Signs the identity header. Generated by `make setup`; the two files must match. |
| `ENVIRONMENT` | `.env` | `development` accepts unsigned local requests. `production` does not. |
| `DOCUMENT_STORAGE_BACKEND` | `.env` | `local` writes to `data/uploads`; `s3` is required in deployments. |

Every security-relevant setting defaults to its safe value, so a forgotten
variable stops the service rather than opening it. See
[the environment template](.env.example) for the complete list, including
database pooling, retrieval distance, and rate-limit settings.

## Quality checks

Run all backend and frontend checks from the repository root:

```bash
make check
```

This checks Python formatting and lint rules, runs the backend test suite (208
tests across 34 files, covering models, services, APIs, cross-user isolation,
rate limits, and fail-closed settings), lints the frontend, and creates a
production frontend build. The tests mock external infrastructure and never make
paid Anthropic calls.

Check current production dependency advisories separately when online:

```bash
make security-check
```

The same checks run in CI on every push and pull request, alongside a backend
image build and CodeQL analysis.

## Maintenance commands

Available once the app is running:

```bash
make owners                           # list owner IDs and their record counts
make reindex                          # rebuild embeddings from stored text
make claim-owner OWNER=google:1234    # move pre-auth records to an account
make migrate                          # apply migrations without restarting Postgres
make database-status                  # show the Postgres container's state
```

## Deployment

The backend is deployed as a container on Fly.io, with the frontend on Vercel,
managed PostgreSQL with `pgvector`, and Cloudflare R2 for uploaded documents.
Production refuses to start without a strong `INTERNAL_AUTH_SECRET`, with a
non-HTTPS CORS origin, or with object storage selected but no bucket, and it
serves no interactive API documentation.

[The deployment runbook](docs/DEPLOYMENT.md) covers the whole path: database and
bucket provisioning, OAuth setup, secrets, both deploys, first-run data
migration, and the operational notes on logs, backups, scaling, secret rotation,
and cost.

## Repository layout

```text
career-os-app/
├── backend/         # FastAPI application, migrations, tests, and deploy config
│   ├── app/         # routes -> services -> repositories and integrations
│   ├── migrations/  # Alembic migrations
│   └── tests/       # pytest suite
├── frontend/        # Next.js App Router application
│   └── src/         # app routes, server actions, components, and API clients
├── docs/            # architecture, roadmap, security policy, deployment runbook
├── scripts/         # local environment and secret setup
├── compose.yaml     # local PostgreSQL service
├── Makefile         # short, repeatable development commands
└── README.md
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system boundaries, data ownership, and the AI response flow.
- [Security policy](docs/SECURITY.md) — implemented controls, the release checklist, and known limitations. Read this before using real career documents.
- [Deployment runbook](docs/DEPLOYMENT.md) — provisioning, deploying, and operating a live instance.
- [Roadmap](docs/ROADMAP.md) — the incremental build plan the project followed.
- [Backend API reference](backend/README.md) — every endpoint, grouped by feature.
- [Frontend notes](frontend/README.md) — running and validating the web interface.

## Project status

Complete. Checkpoints 1 through 7 are done: goals and accomplishments, persistent
Claude chat, document ingestion with grounded retrieval, resume review, mock
interviews, and a portfolio release with Google authentication, per-user
isolation, rate limits, fail-closed production settings, structured logging,
pgvector search, object storage, a production container image, CI, and a live
deployment.

### Known limitations

- **Rate limits are per process.** The counters live in memory, which is exact
  for the single-machine deployment in `backend/fly.toml`. Running several
  instances would give each one the full limit.
- **Sign-in is open by default.** Without `AUTH_ALLOWED_EMAILS`, any Google
  account can use a deployment within the rate limits.
- **Multipart upload signatures are not body-bound.** They cover the method,
  path, owner, and timestamp but not the file bytes, because authenticating the
  body would mean buffering the whole upload in memory.
- **Accessibility has a baseline, not an audit.** Form controls are labelled and
  asynchronous updates announce through live regions, but no formal
  accessibility or responsive-design pass has been run.

[The security policy](docs/SECURITY.md) explains each of these in more detail.
