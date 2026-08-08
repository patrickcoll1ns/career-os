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

## Run tests

From the repository root:

```bash
make backend-check
```

The automated tests mock external infrastructure and never make paid Anthropic calls. A live PostgreSQL connection is verified separately by `make database`.
