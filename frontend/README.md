# CareerOS frontend

The CareerOS web interface is built with Next.js, TypeScript, Tailwind CSS, and the App Router.

## Run locally

From the repository root, start PostgreSQL and FastAPI first:

```bash
make database
make backend
```

Then start the frontend in another terminal:

```bash
make frontend
```

Open [http://localhost:3000](http://localhost:3000). The dashboard supports persistent goal and accomplishment tracking, and the career-copilot interface is available at [http://localhost:3000/chat](http://localhost:3000/chat).

The frontend uses `http://localhost:8000` by default. To use a different backend address, copy `.env.example` to `.env.local` and update the server-only `API_URL` value.

## Validate changes

From the repository root:

```bash
make frontend-check
```

This runs ESLint, TypeScript checking, and the Next.js production build.
