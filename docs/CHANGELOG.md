# Changelog

## Unreleased

- Rewrote the root README for full restore instructions.
- Added beginner documentation for installation, setup, database, API, project structure, architecture, deployment, and troubleshooting.
- Added root `requirements.txt` and `package.json` helper manifests.
- Added `start.bat` and `start.sh` Docker startup scripts.
- Added `PROJECT_CHECKLIST.md` and `FINAL_REPORT.md`.
- Expanded `.env.example` with every backend and Docker variable using placeholder values only.
- Removed generated local dependency/cache folders from the working copy.
- Fixed duplicate chat router registration in the backend app.
- Fixed backend Docker healthcheck to avoid requiring the unlisted `requests` package.
