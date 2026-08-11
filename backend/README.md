# CareerOS API

FastAPI backend for CareerOS.

## Local setup

The simplest setup is from the repository root:

```bash
make setup
cp .env.example .env
make database
make backend
```

The API is available at [http://localhost:8000](http://localhost:8000), with interactive documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

Health endpoints:

- `/health` checks whether FastAPI is running.
- `/health/database` checks whether FastAPI can query PostgreSQL.

Goal endpoints:

- `POST /goals` validates and creates a career goal.
- `GET /goals` lists current goals with the newest first.
- `PATCH /goals/{goal_id}` updates selected fields on an existing goal.
- `POST /goals/{goal_id}/archive` soft-deletes a goal.
- `POST /goals/{goal_id}/restore` restores an archived goal.
- `GET /goals/archived` lists archived goals.

Accomplishment endpoints:

- `POST /accomplishments` validates and creates a career accomplishment.
- `GET /accomplishments` lists accomplishments with the newest first.

Chat endpoints:

- `POST /chat/conversations` starts a new career-coaching conversation.
- `GET /chat/conversations` lists conversations by most recent activity.
- `GET /chat/conversations/{conversation_id}` returns a conversation with its full message history.
- `POST /chat/conversations/{conversation_id}/messages` sends a user message and returns the conversation with Claude's reply appended.

Live replies require `ANTHROPIC_API_KEY` in the ignored root `.env` file. Without a valid key, sending a message returns `502 Bad Gateway` and no partial user-only exchange is saved. `ANTHROPIC_MODEL` defaults to `claude-sonnet-5` and can be overridden locally.

Resume-review endpoints:

- `POST /resume-reviews` reviews one successfully indexed document for an optional target role.
- `GET /resume-reviews` lists saved review history.
- `GET /resume-reviews/{review_id}` returns one structured review.

Starting a review sends the selected document's extracted text to Anthropic. The resulting summary, evidence-backed strengths and gaps, and rewrite suggestions are validated against a Pydantic schema and persisted in PostgreSQL.

Mock interview endpoints:

- `POST /interviews` starts a session for a target role, interview type, and difficulty, and returns the session with Claude's first question.
- `GET /interviews` lists interview sessions with the newest first.
- `GET /interviews/{session_id}` returns one session with its full question/answer history.
- `POST /interviews/{session_id}/answers` submits an answer to the current open question, returns Claude's score and feedback on that turn, and either appends the next question or completes the session with a structured summary once the question limit is reached.

Each answer is scored and critiqued independently, then the session as a whole is debriefed with evidence-based strengths, improvements, and learning recommendations once the configured question limit is reached. Session and turn state, including partial progress, is always persisted in PostgreSQL; a Claude failure marks the session `abandoned` rather than leaving inconsistent state.

## Run tests

From the repository root:

```bash
make backend-check
```

The automated tests mock external infrastructure and never make paid Anthropic calls. A live PostgreSQL connection is verified separately by `make database`.
