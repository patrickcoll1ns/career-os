# Architecture

## Overview

CareerOS is a monorepo containing a Next.js frontend and a FastAPI backend. The frontend calls FastAPI for all application data and AI features. The Anthropic API key exists only in the backend environment and is never sent to the browser.

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

ChromaDB will store derived embeddings for searchable document chunks and selected conversation memories. Each vector record will reference its source PostgreSQL record. ChromaDB data must be rebuildable from authoritative records and uploaded source files.

## Backend organization

FastAPI separates HTTP routes from application logic and infrastructure:

```text
routes -> services -> repositories and integrations
```

- Routes translate HTTP requests and responses.
- Services implement use cases.
- Repositories isolate PostgreSQL and ChromaDB operations.
- Integrations isolate Anthropic and document-processing libraries.

This prevents API routes from becoming tightly coupled to a particular database or model SDK.

## AI response flow

1. Validate the user's message and load recent conversation history from PostgreSQL.
2. When RAG is enabled, search relevant document chunks and selected memories in ChromaDB.
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
- Add authentication and per-user retrieval filters before accepting real public users.
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
