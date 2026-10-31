# Mood Project Picker

A Flask + React project recommendation app. Choose a specialty, answer seven preference questions, pick a difficulty, and receive a project brief selected with weighted vector similarity. The interface keeps the retro purple/pink style with accessible native controls, back navigation, reduced-motion/skip support, visible recovery states and private project history.

The matching engine is pure Python, not a trained mood-detection model. It uses self-reported energy/creativity/challenge preferences and a weighted draw from nearby catalogue entries. It does not guarantee the closest project or scientifically measure a mental state. Generic build outlines are explicitly labelled.

## Run locally

Requires Python 3.12 and Node.js 24:

```
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cd frontend
npm ci
npm run test:unit
npm run build
cd ..
python app.py
```

Open http://localhost:5000. For development hot reload, also run `cd frontend && npm run dev` and use localhost:5173. Keep the virtual environment active for browser tests. Windows activation and production setup are covered in docs/DEPLOYMENT.md.

## What changed

- SQLite-backed private browser sessions replace shared JSON history in the web API.
- Exact API schemas, strict quiz indexes, scoped project completion, CSRF/origin protection, secure production cookies, shared rate buckets and security headers.
- Idempotent quiz submission makes retries safe after a lost response; concurrent retries create one pick.
- Per-pick history, plan reopening, completion, Markdown plan download, JSON export and data deletion.
- React loading/retry/cancellation recovery, answer review, focus handling, native radio controls and timer cleanup.
- Locked dependencies, automated backend/matching/privacy tests, Playwright journey/accessibility checks, CI, Docker/Caddy TLS configuration, backup/cleanup scripts and human release gates.

The catalogue contains 275 ideas (55 in each of five specialties). Many use generic build-plan outlines; the UI labels them rather than presenting them as individually authored tutorials. No GitHub starter link is fabricated. Project completion is self-reported.

## Quality checks

```
python -m pytest -q
pip-audit -r requirements.txt
cd frontend
npm run test:unit
npm run build
npm audit --audit-level=high
npx playwright install chromium
npm run test:e2e
cd ..
python scripts/release_check.py
```

See docs/QA-RESULTS.md for checks actually performed while preparing this patch. Release is blocked until human UAT, content/security review, staging smoke tests and a restore drill have real evidence. A successful build cannot certify launch readiness.

- [API contract](docs/API.md)
- [Security and privacy](docs/SECURITY.md)
- [Deployment and operations](docs/DEPLOYMENT.md)
- [Human acceptance testing](docs/UAT.md)
- [Patch application](docs/PATCH.md)

History stores at most 200 project picks per anonymous 30-day browser session. No passwords or cross-device accounts are included. Raw answers and mood vectors are not saved in history. Losing the browser cookie loses access; export/delete controls are in History. The old terminal harness/JSON analytics remain legacy local tools and are not used by the web API or shipped in the runtime image.
