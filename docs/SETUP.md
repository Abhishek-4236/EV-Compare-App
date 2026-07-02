# Setup Guide

## Fastest Setup With Docker

From the repository root:

```powershell
copy .env.example .env
docker compose up --build
```

Open:

- Frontend: http://127.0.0.1:3000
- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs

## Manual Developer Setup

Use manual setup when you want hot reload for both backend and frontend.

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Environment File Rules

Do not commit `.env`. Commit only `.env.example` with placeholder values.

## Data Files Required For Restore

Keep these files in Git because they are part of the restorable project state:

- `data/raw/India_EV_All_Segments_Dataset_2026_filled.xlsx`
- `backend/data/articles/*.md`
- `backend/data/processed/*.json`
- `backend/data/processed/*.faiss`

## Local Folders Not Required For Restore

These folders are generated locally and must stay out of Git:

- `backend/.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`
- `__pycache__/`
