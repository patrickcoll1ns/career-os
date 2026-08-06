# CareerOS

CareerOS is an AI-powered career copilot that helps people plan and document their career growth. It will provide personalized guidance, resume feedback, mock interviews, goal and accomplishment tracking, and recommendations for what to learn next.

The copilot will use retrieval-augmented generation (RAG) so its answers can be grounded in the user's uploaded documents and relevant conversation history.

## Planned technology

- Next.js and TypeScript frontend
- FastAPI and Python backend
- PostgreSQL primary database
- ChromaDB vector database
- Anthropic Claude API
- Docker Compose for local services

## Project status

The project is currently in its foundation phase. The architecture and incremental implementation plan are documented before application code is introduced.

## Planned repository layout

```text
career-os/
├── frontend/        # Next.js application
├── backend/         # FastAPI application
├── docs/            # Architecture and roadmap
├── compose.yaml     # Local PostgreSQL and ChromaDB services
└── README.md
```

Development will proceed in small, working increments. See [docs/ROADMAP.md](docs/ROADMAP.md) for the planned checkpoints.
