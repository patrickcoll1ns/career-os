# Security policy and v1 release gate

## Current deployment boundary

CareerOS uses Google OAuth through Auth.js. Next.js derives a stable provider user
ID from the authenticated session and signs short-lived identity headers sent to
FastAPI. FastAPI verifies those headers before resolving protected routes. Parent
database records and document embeddings are scoped to that owner ID; child
messages and interview turns are authorized through their parent.

Every security-relevant setting defaults to its safe value. `ENVIRONMENT`
defaults to `production`, API documentation defaults to disabled, and the CORS
allowlist defaults to empty, so a forgotten environment variable stops the
service rather than opening it. Production additionally refuses to start without
an `INTERNAL_AUTH_SECRET` of at least 32 characters, with a non-HTTPS CORS
origin, or with object storage selected but no bucket.

Development and test environments permit unsigned local API requests and assign
them to the explicit `development:local` owner, keeping tests and local API
exploration simple. Reaching that path requires setting `ENVIRONMENT` away from
its default. Never do that on a public host.

## Implemented controls

- Secrets are read server-side from ignored environment files or a platform
  secret store.
- The browser talks to FastAPI through Next.js server code; the Anthropic and
  Voyage keys are never public environment variables.
- Request schemas bound titles, messages, interview answers, target roles, and
  descriptions.
- Uploads are streamed to a private temporary file with a 5 MB limit, validated,
  then written to storage under a generated UUID name.
- Upload validation checks MIME type, extension, file signature, empty files, and
  generated storage keys, identically for local and object storage.
- PDF page counts, extracted text, DOCX member counts, and DOCX expanded size are
  bounded before AI processing.
- User-authored profile and document content is delimited and explicitly treated
  as untrusted in AI prompts.
- React renders model output through `react-markdown` without raw HTML support.
- Frontend and API responses set clickjacking, MIME-sniffing, referrer,
  permissions, and cache controls; the frontend also sets a Content Security
  Policy.
- CORS is limited to configured origins, necessary methods, and the headers the
  frontend actually sends.
- Google OAuth protects application routes, Auth.js manages encrypted session
  cookies, and unverified Google addresses are rejected.
- `AUTH_ALLOWED_EMAILS` optionally restricts sign-in to named accounts.
- FastAPI verifies HMAC-signed user IDs with a 60-second replay window. The
  signature covers the method, path, timestamp, owner, and a digest of the
  request body, so a captured signature cannot be reused with different content.
- Per-owner sliding-window rate limits bound AI and upload requests, which are
  the endpoints that cost money.
- PostgreSQL operations filter every read, write, and delete by the verified
  owner ID, and cross-user tests assert this for every resource type.
- Structured JSON logs carry a request ID, method, path, status, and duration,
  and never request bodies, prompts, document text, or secrets.
- Deleting a document removes its embeddings, its resume reviews, and its stored
  bytes.
- The backend image runs as a non-root user and contains no test code or build
  toolchain.
- CI runs formatting, lint, tests, an image build, CodeQL, `pip-audit`, and
  `npm audit` on every push and pull request.
- API documentation is disabled unless `EXPOSE_API_DOCS=true` is set explicitly.

## Public v1 checklist

- [x] Select an identity provider and validate identity at both Next.js and
  FastAPI boundaries.
- [x] Add immutable owner IDs to every authoritative parent table.
- [x] Apply ownership filters to every read, update, archive, delete, AI-context,
  and document operation.
- [x] Partition vector records and searches by owner ID.
- [x] Migrate existing single-user records to an explicitly selected owner
  (`make claim-owner OWNER=…`).
- [x] Add cross-user authorization tests for every resource type.
- [x] Add rate limits for upload, chat, review, and interview endpoints.
- [x] Store uploads in private object storage.
- [x] Run dependency and code scans in CI.
- [x] Default `EXPOSE_API_DOCS` to false, require HTTPS CORS origins in
  production, and keep PostgreSQL on a private network.
- [x] Emit structured, redacted logs.
- [ ] Configure object retention and deletion policies in R2, and confirm the
  PostgreSQL backup retention window on your plan.
- [ ] Set a calendar reminder to rotate `INTERNAL_AUTH_SECRET`, `AUTH_SECRET`,
  and the provider API keys.

## Known limitations

- **Rate limits are per process.** The counters live in memory, which is exact
  for the single-machine deployment in `fly.toml`. Running several instances
  divides the effective limit; move the counters into PostgreSQL or Redis first.
- **Multipart uploads are not body-bound.** Their signature covers the method,
  path, owner, and timestamp but not the file bytes, because authenticating the
  body would mean buffering the whole upload in memory. Size, type, and
  signature validation still apply.
- **Signatures are replayable inside 60 seconds.** An identical request replayed
  within the window is accepted. Requests travel server-to-server over TLS, so
  capturing one requires already holding a stronger position.
- **Sign-in is open by default.** Without `AUTH_ALLOWED_EMAILS`, any Google
  account can use the deployment within the rate limits.

## Reporting

Do not include resumes, prompts, API keys, environment files, or other personal
data in an issue. Report suspected vulnerabilities privately to the repository
owner with reproduction steps and the affected commit.
