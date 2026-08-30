# Deploying CareerOS

The target topology is Next.js on Vercel, FastAPI on Fly.io, managed PostgreSQL
with the `pgvector` extension, and Cloudflare R2 for uploaded documents.

```text
Browser -> Vercel (Next.js) -> Fly.io (FastAPI) -> PostgreSQL + pgvector
                                     |-> Cloudflare R2 (documents)
                                     |-> Anthropic (coaching, review, interviews)
                                     `-> Voyage AI (embeddings)
```

Only Vercel and Fly are reachable from the internet. The browser never talks to
FastAPI: Next.js server code signs an identity header per request, and FastAPI
verifies it.

## Before you start

You need accounts for Vercel, Fly.io, a PostgreSQL host, Cloudflare R2,
Google Cloud (OAuth), Anthropic, and Voyage AI. Install the `fly` and `vercel`
CLIs and run `make check` locally so you deploy a green tree.

## 1. PostgreSQL with pgvector

Any host that offers the `vector` extension works — Neon, Supabase, or Fly
Managed Postgres. Put it in the same region as the backend (`iad` pairs with
AWS `us-east-1`).

Two connection-string details matter:

- **Driver.** The URL must start with `postgresql+asyncpg://`, not
  `postgres://`.
- **TLS.** asyncpg does not understand libpq's `sslmode`. Replace
  `?sslmode=require` with `?ssl=require`.

If you use a **pooled** endpoint (PgBouncer in transaction mode, or Neon's
`-pooler` host), also set `DATABASE_STATEMENT_CACHE_SIZE=0`. asyncpg's prepared
statements are per-connection and break when the pooler reassigns connections.
The direct endpoint needs no such change.

The `vector` extension is created by the first migration, so the database user
must be allowed to run `CREATE EXTENSION`. On managed hosts this is usually the
default owner role.

## 2. Cloudflare R2

Create a **private** bucket named `careeros-documents` and an API token scoped
to it with object read and write. Record the account endpoint
(`https://<account-id>.r2.cloudflarestorage.com`), the access key ID, and the
secret. No public access and no custom domain: documents are only ever read by
the backend.

## 3. Google OAuth

In Google Cloud Console create an OAuth client of type "Web application" and add
both redirect URIs:

```text
http://localhost:3000/api/auth/callback/google
https://<your-vercel-domain>/api/auth/callback/google
```

Add the production domain to the OAuth consent screen's authorized domains.

## 4. Shared secrets

Generate two independent secrets and keep them out of the repository:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # INTERNAL_AUTH_SECRET
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # AUTH_SECRET
```

`INTERNAL_AUTH_SECRET` must be **identical** in Fly and Vercel — it is the key
both sides use to sign and verify the identity header. `AUTH_SECRET` belongs to
Vercel only. Use different values from your local `.env` files.

## 5. Deploy the backend to Fly

`backend/fly.toml` already pins the safe values:
`ENVIRONMENT=production`, `EXPOSE_API_DOCS=false`, and
`DOCUMENT_STORAGE_BACKEND=s3`. Everything secret is set separately:

Run these from `backend/`, which is the build context the Dockerfile expects:

```bash
cd backend
fly launch --no-deploy --copy-config --name careeros-api
fly secrets set \
  INTERNAL_AUTH_SECRET="…" \
  DATABASE_URL="postgresql+asyncpg://…?ssl=require" \
  ANTHROPIC_API_KEY="…" \
  VOYAGE_API_KEY="…" \
  S3_BUCKET="careeros-documents" \
  S3_ENDPOINT_URL="https://<account-id>.r2.cloudflarestorage.com" \
  S3_ACCESS_KEY_ID="…" \
  S3_SECRET_ACCESS_KEY="…" \
  BACKEND_CORS_ORIGINS="https://<your-vercel-domain>"
fly deploy
```

`release_command` runs `alembic upgrade head` before new machines take traffic,
so migrations never race the application.

The backend refuses to start if `INTERNAL_AUTH_SECRET` is missing or shorter
than 32 characters, if `BACKEND_CORS_ORIGINS` contains a non-HTTPS origin, or if
object storage is selected without a bucket. A failed release is the intended
outcome for a misconfigured deployment.

Confirm the deploy:

```bash
curl -si https://careeros-api.fly.dev/health | head -1        # 200
curl -si https://careeros-api.fly.dev/goals | head -1         # 401
curl -si https://careeros-api.fly.dev/docs | head -1          # 404
```

A `401` on `/goals` is the important one: it proves the unsigned-request path is
closed in production.

## 6. Deploy the frontend to Vercel

Point Vercel at the repository with **Root Directory** set to `frontend`, then
set environment variables for the Production environment:

| Variable | Value |
| --- | --- |
| `API_URL` | `https://careeros-api.fly.dev` |
| `INTERNAL_AUTH_SECRET` | the same value set in Fly |
| `AUTH_SECRET` | the second generated secret |
| `AUTH_GOOGLE_ID` | Google OAuth client ID |
| `AUTH_GOOGLE_SECRET` | Google OAuth client secret |
| `AUTH_ALLOWED_EMAILS` | optional comma-separated allowlist |
| `AUTH_URL` | `https://<your-vercel-domain>` |

Set `AUTH_ALLOWED_EMAILS` unless you intend the deployment to be open. Without
it, any Google account can sign in and spend your Anthropic and Voyage budget;
the per-user rate limits bound the damage but do not prevent it.

Vercel manages Server Action encryption keys automatically. If you ever move the
frontend to your own multi-instance hosting, set a stable
`NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` across instances.

## 7. First-run tasks

Move any pre-authentication records to your real account. Owner IDs are
deliberately absent from the logs, so ask the database which ones exist. Sign in
once and save a goal, then:

```bash
cd backend
fly ssh console -C "python -m app.cli owners"
```

That prints each owner ID and how many records it holds — your new
`google:<numeric-id>` beside the `development:local` rows it should absorb:

```bash
fly ssh console -C "python -m app.cli claim-owner --owner google:1234567890"
```

If you are restoring from a database that predates pgvector, rebuild embeddings
from the stored extracted text:

```bash
fly ssh console -C "python -m app.cli reindex"
```

## 8. Verify the deployment

- Sign in with an allowlisted Google account; a non-allowlisted one is rejected.
- Create a goal and an accomplishment, and confirm they survive a reload.
- Upload a resume and confirm it reaches `ready`.
- Ask the copilot something answerable only from that resume and confirm the
  reply cites it.
- Delete the document and confirm its reviews disappear with it.
- Sign in as a second account and confirm none of the first account's data is
  visible.

## Operations

**Logs.** The backend emits one JSON object per line with a `request_id`,
method, path, status, and duration. No request bodies, prompts, resume text, or
secrets are logged. `fly logs` streams them.

**Backups.** Managed PostgreSQL handles point-in-time recovery; confirm the
retention window on your plan. R2 objects are the only data not in PostgreSQL —
enable object versioning if you want them recoverable.

**Scaling.** The rate limiter counts requests in-process, so it is exact for one
machine. `min_machines_running = 1` with a single worker keeps that true. Before
running several machines, move those counters into PostgreSQL or Redis,
otherwise each instance enforces the full limit independently.

**Secret rotation.** Rotating `INTERNAL_AUTH_SECRET` requires updating Fly and
Vercel together; requests signed with the old value fail closed within the
60-second signature window. Rotate `AUTH_SECRET` to invalidate all sessions.

**Cost.** Anthropic calls dominate. `RATE_LIMIT_AI_REQUESTS` (default 60 per
hour per user) is the ceiling; lower it before opening the app more widely.
