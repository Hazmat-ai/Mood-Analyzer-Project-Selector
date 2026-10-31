# Applying this patch

Baseline: Hazmat-ai/Mood-Analyzer-Project-Selector main commit b61ec4532546136a26b43689ef67368dad02094b. Apply to a clean checkout, then review and test before merging.

```
git switch -c feature/mood-picker-fullstack
git apply --check ~/Downloads/Mood-Analyzer-fullstack-reviewed.patch
git apply ~/Downloads/Mood-Analyzer-fullstack-reviewed.patch
```

See DEPLOYMENT.md for Python virtual environment, frontend installation and complete QA commands. Install Playwright's Chromium before running the browser tests. The patch includes no node_modules, Python virtual environment, browser executable, database, private key or secret. Applying it does not deploy the app, import old shared logs, or complete pending human checks.
