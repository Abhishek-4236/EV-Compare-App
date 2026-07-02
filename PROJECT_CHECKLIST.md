# Project Backup Checklist

Use this checklist before deleting the local working copy.

## Required repository files

- [x] `README.md`
- [x] `LICENSE`
- [x] `.gitignore`
- [x] `.env.example`
- [x] `requirements.txt`
- [x] `package.json`
- [x] `docker-compose.yml`
- [x] `start.bat`
- [x] `start.sh`
- [x] `PROJECT_CHECKLIST.md`
- [x] `FINAL_REPORT.md`
- [x] `backend/`
- [x] `frontend/`
- [x] `data/raw/India_EV_All_Segments_Dataset_2026_filled.xlsx`
- [x] `backend/data/processed/vehicles.json`
- [x] `backend/data/processed/vehicles.faiss`
- [x] `backend/data/processed/knowledge_chunks.json`
- [x] `backend/data/processed/knowledge.faiss`
- [x] `backend/alembic/`
- [x] `docs/`

## Files intentionally not committed

- [x] `.env`
- [x] `backend/.venv/`
- [x] `frontend/node_modules/`
- [x] `frontend/dist/`
- [x] `__pycache__/`
- [x] `.pytest_cache/`
- [x] local database dumps and logs

## Verification

- [ ] Backend dependencies install on a fresh machine.
- [ ] Frontend dependencies install on a fresh machine.
- [ ] `alembic upgrade head` runs.
- [ ] Backend starts at `http://127.0.0.1:8000`.
- [ ] Frontend starts at `http://127.0.0.1:5173`.
- [ ] Docker Compose starts Postgres, Redis, backend, and frontend.
- [ ] Git working tree is clean.
- [ ] Latest commit is pushed to GitHub.
