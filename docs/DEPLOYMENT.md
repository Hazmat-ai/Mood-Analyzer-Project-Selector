# Setup and deployment

Use Python 3.12 and Node.js 24. Keep the Python virtual environment activated while running the browser tests; Playwright starts the API with `python app.py`. Production uses Flask under Gunicorn and serves the built React frontend on the same origin.

## Local

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
cd frontend
npm ci
npm run test:unit
npm run build
npx playwright install chromium
npm run test:e2e
```

On Windows activate `.venv\Scripts\activate` instead; use Docker/WSL or Linux for Gunicorn production. To run the built application, return to the repository root and run `python app.py`, then open http://localhost:5000. For hot reload, run `python app.py` in one terminal and `cd frontend && npm run dev` in another. Vite uses localhost:5173 and proxies API requests; that origin is accepted only in development. The API does not load .env automatically. Export variables explicitly for native execution; Docker Compose reads .env itself.

## Verify the candidate

```
python -m pytest -q
pip-audit -r requirements.txt
cd frontend
npm ci
npm run test:unit
npm run build
npm audit --audit-level=high
npx playwright install --with-deps chromium
npm run test:e2e
cd ..
python scripts/release_check.py
```

The final command intentionally blocks until real UAT, security, content, staging and restore signoffs are recorded. Configure branch protection to require Quality gates. Trigger Release readiness for the exact candidate, then retain immutable image digests and evidence. Audit/review base images and Actions dependencies as part of release; mutable tags are not immutable attestations.

## TLS deployment

Copy .env.example to a local .env and set APP_DOMAIN to a domain pointing at your server. Generate PROXY_TOKEN using `python -c "import secrets; print(secrets.token_hex(32))"` and paste it into that private file. Never commit it or put it in VITE_ variables. Open inbound 80/443 and run:

```
docker compose build --pull
docker compose up -d
docker compose logs --tail=100 app
```

Caddy provisions HTTPS and forwards only one same-origin application. The API port is not exposed publicly. A named volume persists SQLite data. Runtime is non-root with a read-only root filesystem and writable data/tmp mounts. The authenticated client-IP header keeps rate buckets per visitor across Gunicorn workers. Add edge connection/traffic limits and monitor capacity; this is not a distributed DDoS service.

This design is one application deployment on one host with SQLite on durable local disk. Multiple Gunicorn workers are supported through SQLite transactions/WAL. Do not mount the DB on NFS, use ephemeral/serverless storage, or scale multiple hosts over the same file. Larger deployments require shared database/session/rate-limit infrastructure and load testing. There is no online account sync.

Without Docker: build frontend, then export APP_ENV=production, APP_ORIGIN=https://your-domain and DB_PATH=/durable/mood.sqlite before `gunicorn --preload --workers 2 --threads 4 --bind 127.0.0.1:5000 'app:create_app()'` behind a trusted TLS proxy preserving Host and Origin. Configure the proxy token and overwritten IP header as in Caddyfile. Do not run the Flask development server publicly.

## Backup, cleanup and rollback

Use `python scripts/backup.py --source /path/mood.sqlite --destination /restricted/backup.sqlite` on a host checkout with access to the data directory. It uses SQLite's online backup API and verifies integrity; it refuses to overwrite an existing file. Restrict/encrypt backups and define retention. It does not back up your deployment secrets or configure scheduled jobs.

Run `DB_PATH=/path/mood.sqlite python scripts/cleanup.py` on a regular host schedule, even when the service has no requests. Expired identities are rejected immediately; this command physically removes expired session/pick rows and rate buckets. Monitor job success. Never export the legacy analytics/activity_log.json into the new public service: visitor ownership is unknown.

Restore with the app stopped. Preserve the current database and image first; replace the DB with a verified snapshot, remove stale -wal/-shm sidecars only while no process uses the DB, restore runtime ownership (container UID 10001), restart, and verify known history plus /api/health. The automated round-trip test does not replace this deployment drill. Retain a prior image and matching DB snapshot for rollback; future schema changes need explicit migration/rollback planning.

Monitor database size/free disk, backup age, 5xx and rate-limit counts, request latency, certificate renewal and cleanup jobs. Health checks require the canonical Host and perform a DB query. Request IDs support correlation; do not add cookies, CSRF tokens, fingerprints or raw quiz content to logs. Review log retention and hosting privacy.
