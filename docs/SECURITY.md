# Security policy and v1 release gate

## Current deployment boundary

CareerOS is currently a single-user development application. It has no end-user
authentication and its database records and vector index are not partitioned by
user. Do not expose the frontend, FastAPI, PostgreSQL, ChromaDB, or uploaded-file
directory to the public internet in this state.

Authentication and per-user authorization are release blockers for a public,
multi-user v1. Every database query, uploaded object, and Chroma record must be
scoped to the authenticated user before public deployment. Hiding the FastAPI URL,
adding CORS, or placing a shared API key between services does not provide that
isolation.

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
- API documentation can be disabled with `EXPOSE_API_DOCS=false`.

## Public v1 checklist

- [ ] Select an identity provider and validate sessions on both Next.js and
  FastAPI.
- [ ] Add immutable user IDs and ownership constraints to every authoritative
  table.
- [ ] Apply ownership filters to every read, update, archive, delete, AI-context,
  and document operation.
- [ ] Partition Chroma records and searches by user ID.
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
