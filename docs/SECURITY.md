# Security policy and v1 release gate

## Current deployment boundary

CareerOS uses GitHub OAuth through Auth.js. Next.js derives a stable provider user
ID from the authenticated session and signs short-lived identity headers sent to
FastAPI. FastAPI verifies those headers before resolving protected routes. Parent
database records and Chroma metadata are scoped to that owner ID; child messages
and interview turns are authorized through their parent.

Development mode may run without the internal signing secret and uses the explicit
`development:local` owner. Production configuration fails closed when
`INTERNAL_AUTH_SECRET` is absent. Do not expose development mode publicly.

## Implemented controls

- Secrets are read server-side from ignored environment files.
- The browser talks to FastAPI through Next.js server code; the Anthropic key is
  never a public environment variable.
- Request schemas bound titles, messages, interview answers, target roles, and
  descriptions.
- Uploads are streamed with a 5 MB limit, stored under generated UUID names, and
  restricted to PDF, DOCX, and text formats.
- Upload validation checks MIME type, extension, file signature, empty files, and
  generated storage keys.
- PDF page counts, extracted text, DOCX member counts, and DOCX expanded size are
  bounded before AI processing.
- User-authored profile and document content is delimited and explicitly treated
  as untrusted in AI prompts.
- React renders model output through `react-markdown` without raw HTML support.
- Frontend and API responses set clickjacking, MIME-sniffing, referrer, permissions,
  and cache controls; the frontend also sets a Content Security Policy.
- CORS is limited to configured origins, necessary methods, and the content-type
  header.
- Local PostgreSQL and ChromaDB ports bind only to the loopback interface.
- GitHub OAuth protects application routes, and Auth.js manages encrypted session
  cookies.
- FastAPI verifies HMAC-signed user IDs with a 60-second replay window.
- PostgreSQL and Chroma operations filter records by the verified owner ID.
- API documentation can be disabled with `EXPOSE_API_DOCS=false`.

## Public v1 checklist

- [x] Select an identity provider and validate identity at both Next.js and
  FastAPI boundaries.
- [x] Add immutable owner IDs to every authoritative parent table.
- [x] Apply ownership filters to every read, update, archive, delete, AI-context,
  and document operation.
- [x] Partition Chroma records and searches by owner ID.
- [ ] Migrate existing single-user records to an explicitly selected owner.
- [ ] Add cross-user authorization tests for every resource type.
- [ ] Add rate limits for authentication, upload, chat, review, and interview
  endpoints.
- [ ] Store uploads in private object storage with encryption, retention, and
  deletion policies.
- [ ] Run dependency and container-image vulnerability scans in CI.
- [ ] Set `EXPOSE_API_DOCS=false`, use exact HTTPS CORS origins, and keep PostgreSQL
  and ChromaDB on a private network.
- [ ] Configure HTTPS, secure session cookies, structured redacted logs, backups,
  monitoring, and secret rotation in the deployment platform.

## Reporting

Do not include resumes, prompts, API keys, environment files, or other personal
data in an issue. Report suspected vulnerabilities privately to the repository
owner with reproduction steps and the affected commit.
