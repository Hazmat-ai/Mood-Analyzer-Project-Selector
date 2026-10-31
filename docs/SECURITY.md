# Security and privacy model

History previously belonged to every visitor on an instance. The API now uses a random 256-bit opaque browser cookie and stores only its SHA-256 hash, a CSRF token and expiry. There are no passwords, email addresses, privileged roles, or account recovery endpoints. Browser cookie possession grants access to that browser's records; losing it loses access. This is anonymous session isolation, not cross-device user authentication.

| Threat | Control | Remaining review |
|---|---|---|
| Access to another visitor's history | Every query/update is scoped to server-resolved session; parameterized SQL; server-owned pick/title lookup | Session theft remains bearer access; require HTTPS |
| Cross-site mutations | Strict SameSite HttpOnly cookie; Secure + __Host in production; exact Origin + per-session CSRF header; no CORS | Review proxy/origin configuration; development permits localhost:5173 only outside production |
| Duplicate picks after timeouts | Per-session idempotency key and keyed request fingerprint; SQLite unique constraint plus immediate transaction | Retention is 200 picks, not indefinite deduplication; new quiz is a new intent |
| Injection and payload abuse | Exact object schemas, strict integer indexes, catalogue allowlists, 4KiB JSON limit, generic errors | Browser UAT and deployment security review remain required |
| XSS/clickjacking | React escaping, no HTML injection, CSP self-only scripts, nosniff/frame denial; remote font requests removed | Inline styles allowed; no claim of an independent penetration test |
| Rate-limit evasion | SQLite-backed buckets shared across Gunicorn workers; private authenticated proxy token; Caddy overwrites client IP header | Add edge connection/traffic controls and load-test realistic traffic |
| Sensitive history exposure | No raw answers or mood vectors in saved history; anonymous project picks only; scoped export and deletion | A project choice may still reveal preferences; protect database and backups |
| Database loss | SQLite WAL, transaction replacement, backups through SQLite API, schema-version guard | Durable volume, host encryption, restricted backup access and restore drills |
| Build secret exposure | .env variants, runtime data, legacy logs and dependencies excluded from Docker context | Never put the proxy token in VITE_ variables or publish container port 5000 |

Only the current request computes the preference vector. Saved picks contain canonical project ID/title, specialty, difficulty, timestamps, completion state, request key and a fingerprint keyed with the raw random browser token. Raw quiz answers/vectors are not persisted. Rate buckets store a hash of the client IP for a one-minute window, not raw IP addresses. Normal request logs do not include bodies, cookies or CSRF tokens. Access logs may include IP/path information; configure logging retention and trusted hosting appropriately.

Expired sessions cannot be used. Database rows are purged on subsequent API activity; run scripts/cleanup.py periodically for idle-service retention. The database does not make encrypted copies or expire your external backups automatically. Define and implement backup retention separately. The original shared JSON log is excluded from deployment and is not automatically migrated because it has no visitor ownership.

Production requires an explicit HTTPS APP_ORIGIN and a matching Host. X-Forwarded-For is ignored. X-Real-IP is accepted only alongside a constant-time-verified 64-character secret PROXY_TOKEN in X-Mood-Proxy-Token. Caddy overwrites both headers. Rotate both services together. Without a valid credential, requests fall back to their socket-IP bucket; they cannot choose an arbitrary rate bucket.

The matching algorithm is a hand-tagged preference heuristic. It is not a trained mental-state classifier, productivity measurement, or validated psychological assessment. Completion is self-reported, not a trusted grade. Content is rendered as text; generic outlines are labelled in the UI.

References: https://flask.palletsprojects.com/en/stable/web-security/ and https://docs.python.org/3.12/library/sqlite3.html . Dependency audits are point-in-time advisory checks, not proof that the system has no vulnerabilities.
