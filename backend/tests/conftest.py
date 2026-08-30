"""Pin the test environment before application settings are constructed.

`Settings` defaults to production and refuses to start without a strong
`INTERNAL_AUTH_SECRET`, so the suite declares its own environment here. pytest
imports this module before any test module, which is before `app.core.config`
is first imported.
"""

import os

os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("INTERNAL_AUTH_SECRET", "test-only-internal-auth-secret")
os.environ.setdefault("BACKEND_CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("VOYAGE_API_KEY", "test-only-voyage-key")
os.environ.setdefault("DOCUMENT_STORAGE_BACKEND", "local")
# Pinned rather than inherited so the suite does not depend on a developer .env.
os.environ["EXPOSE_API_DOCS"] = "true"
