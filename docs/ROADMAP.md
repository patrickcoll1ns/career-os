# Incremental roadmap

## Checkpoint 0 — Architecture foundation

- Define product scope and system boundaries.
- Document PostgreSQL and ChromaDB ownership.
- Define secret-handling and retrieval safety rules.
- Record the incremental implementation plan.

## Checkpoint 1 — Runnable project skeleton

- Scaffold Next.js with TypeScript, Tailwind CSS, ESLint, and App Router.
- Scaffold FastAPI with settings, CORS, tests, and `/health`.
- Configure PostgreSQL and ChromaDB with Docker Compose.
- Document local startup commands.

Done when the browser renders a basic CareerOS shell, the API health test passes, and the frontend can reach the API.

## Checkpoint 2 — Goals and accomplishments

- Add database migrations and initial models.
- Create goal and accomplishment API endpoints.
- Build a small dashboard for viewing and recording progress.

Done when structured career data persists across application restarts.

## Checkpoint 3 — Persistent Claude chat

- Add the server-side Anthropic integration.
- Store conversations and messages.
- Build the chat interface and error states.
- Include structured profile context in the coaching prompt.

Done when the user can have a saved, personalized career conversation.

## Checkpoint 4 — Document ingestion and RAG

- Upload and validate resume/career documents.
- Extract, chunk, embed, and index document text.
- Retrieve relevant chunks for chat requests.
- Show source references with grounded responses.

Done when an answer can cite information from an uploaded resume.

## Checkpoint 5 — Resume review

- Add a focused resume-review workflow.
- Return structured strengths, gaps, and rewrite suggestions.
- Ground claims in the uploaded resume and store review history.

## Checkpoint 6 — Mock interviews

- Configure a target role and interview type.
- Conduct question-by-question interview sessions.
- Produce structured feedback and learning recommendations.

## Checkpoint 7 — Portfolio release

- Add authentication and user isolation.
- Improve accessibility and responsive design.
- Add demo data, screenshots, tests, and deployment documentation.
- Deploy the frontend, API, PostgreSQL, and vector storage.
