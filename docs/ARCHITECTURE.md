# Architecture

## Overview

CareerOS is a monorepo containing a Next.js frontend and a FastAPI backend. The frontend calls FastAPI for all application data and AI features. The Anthropic API key exists only in the backend environment and is never sent to the browser.

```text
Browser -> Next.js -> FastAPI
                         |-> PostgreSQL (records and pgvector embeddings)
                         |-> Object storage (uploaded documents)
                         |-> Anthropic API (coaching, review, interviews)
                         `-> Voyage AI (embeddings)
```

## Service responsibilities

### Next.js frontend

- Dashboard and navigation
- Career-copilot chat interface
- Goal and accomplishment forms
- Resume and document uploads
- Mock interview interface
- Loading, error, and source-reference states

### FastAPI backend

- HTTP API and validation
- Career coaching workflows
- Anthropic API integration
- Conversation and structured-data persistence
- Document extraction and chunking
- Embedding, retrieval, and prompt construction
- Identity verification and per-owner authorization boundaries

### PostgreSQL

PostgreSQL is the authoritative data store for profiles, conversations, messages, goals, accomplishments, document metadata, resume reviews, and interview sessions.

### Vector search

Document chunk embeddings live in the same PostgreSQL database, in a
`document_chunks` table using the `pgvector` extension. Keeping them there means
retrieval is covered by the same ownership filter, transaction, and backup as
everything else, and the deployment has one stateful service instead of two.

Embedding rows are derived data. They reference their source document, cascade
when it is deleted, and can be rebuilt at any time from stored extracted text
with `make reindex`.

### Object storage

Uploaded documents are written to an S3-compatible bucket in deployments and to
`data/uploads` in local development, behind one `DocumentStorage` interface that
performs validation identically for both. Container filesystems do not survive a
restart, so nothing durable may live on local disk in production.

## Backend organization

FastAPI separates HTTP routes from application logic and infrastructure:

```text
routes -> services -> repositories and integrations
```

- Routes translate HTTP requests and responses.
- Services implement use cases.
- Repositories isolate PostgreSQL operations.
- Integrations isolate Anthropic and document-processing libraries.

This prevents API routes from becoming tightly coupled to a particular database or model SDK.

## AI response flow

1. Validate the user's message and load recent conversation history from PostgreSQL.
2. Embed the question and search the owner's document chunks by cosine distance.
3. Build a prompt from system instructions, structured profile data, recent messages, and retrieved evidence.
4. Ask Claude to generate a response grounded in that context.
5. Save the user message and successful assistant response together as one PostgreSQL transaction.
6. Return the complete persisted exchange and source references to the frontend.

Saving the complete exchange atomically prevents a failed external API call from leaving a user-only half-exchange in conversation history.

## Initial API boundaries

- `/health` for service health
- `/chat` for copilot conversations
- `/documents` for upload and ingestion
- `/goals` for goal tracking
- `/accomplishments` for the accomplishment journal
- `/resume-reviews` for structured resume feedback
- `/interviews` for mock interview sessions

## Security baseline

- Store secrets only in ignored local environment files or deployment secret stores.
- Never expose the Anthropic key through a `NEXT_PUBLIC_` variable.
- Restrict uploaded file types and sizes.
- Do not log API keys, full prompts, resumes, or personal document contents.
- Keep authentication and per-user retrieval filters on every data path.
- Treat goals, accomplishments, retrieved documents, and other user-authored text as untrusted data, not system instructions.
- Escape or structurally delimit untrusted profile context before including it in prompts.

## MVP scope

The initial portfolio MVP prioritizes a polished demonstration over a wide feature set:

1. Career dashboard with goals and accomplishments
2. Persistent Claude-powered career chat
3. Resume/document upload and grounded RAG answers
4. One focused resume-feedback workflow
5. Question-by-question mock interviews with scored feedback

More advanced planning features will follow as separate increments.
