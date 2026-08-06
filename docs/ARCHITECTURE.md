# Architecture

## Overview

CareerOS will be a monorepo containing a Next.js frontend and a FastAPI backend. The frontend will call FastAPI for all application data and AI features. The Anthropic API key will exist only in the backend environment and will never be sent to the browser.

```text
Browser -> Next.js -> FastAPI
                         |-> PostgreSQL
                         |-> ChromaDB
                         `-> Anthropic API
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
- Authorization boundaries when authentication is added

### PostgreSQL

PostgreSQL is the authoritative data store for profiles, conversations, messages, goals, accomplishments, document metadata, resume reviews, and interview sessions.

### ChromaDB

ChromaDB stores derived embeddings for searchable document chunks and selected conversation memories. Each vector record will reference its source PostgreSQL record. ChromaDB data must be rebuildable from authoritative records and uploaded source files.

## Backend organization

FastAPI will separate HTTP routes from application logic and infrastructure:

```text
routes -> services -> repositories and integrations
```

- Routes translate HTTP requests and responses.
- Services implement use cases.
- Repositories isolate PostgreSQL and ChromaDB operations.
- Integrations isolate Anthropic and document-processing libraries.

This prevents API routes from becoming tightly coupled to a particular database or model SDK.

## RAG response flow

1. Save the user's message in PostgreSQL.
2. Search relevant document chunks and selected memories in ChromaDB.
3. Build a prompt from system instructions, user profile data, recent messages, and retrieved evidence.
4. Ask Claude to generate a response grounded in that evidence.
5. Save the answer and its source references in PostgreSQL.
6. Return the response and references to the frontend.

## Initial API boundaries

- `/health` for service health
- `/chat` for copilot conversations
- `/documents` for upload and ingestion
- `/goals` for goal tracking
- `/accomplishments` for the accomplishment journal
- `/resume-reviews` for structured resume feedback
- `/interviews` for mock interview sessions

The first runnable version will implement only health checks and one thin end-to-end feature.

## Security baseline

- Store secrets only in ignored local environment files or deployment secret stores.
- Never expose the Anthropic key through a `NEXT_PUBLIC_` variable.
- Restrict uploaded file types and sizes.
- Do not log API keys, full prompts, resumes, or personal document contents.
- Add authentication and per-user retrieval filters before accepting real public users.
- Treat retrieved document text as untrusted content, not system instructions.

## MVP scope

The initial portfolio MVP will prioritize a polished demonstration over a wide feature set:

1. Career dashboard with goals and accomplishments
2. Persistent Claude-powered career chat
3. Resume/document upload and grounded RAG answers
4. One focused resume-feedback workflow

Mock interviews and more advanced planning features will follow as separate increments.
