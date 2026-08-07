# CareerOS frontend

The CareerOS web interface is built with Next.js, TypeScript, Tailwind CSS, and the App Router.

## Run locally

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

The dashboard checks the FastAPI health endpoint at `http://localhost:8000` by default. To use a different backend address, copy `.env.example` to `.env.local` and update `API_URL`.

## Validate changes

```bash
npm run lint
npm run build
```

The current interface is a static foundation preview. Backend connectivity and interactive career features will be added in later checkpoints.
