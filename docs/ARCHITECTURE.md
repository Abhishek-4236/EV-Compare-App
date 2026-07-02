# Architecture

## Overview

EV Compare App is split into three main layers:

1. React frontend for user workflows.
2. FastAPI backend for API, retrieval, auth, and business logic.
3. PostgreSQL/Redis/data artifacts for persistence and infrastructure.

## Request Flow

```text
Browser -> Vite React frontend -> /api proxy -> FastAPI router -> service layer -> database or bundled artifact -> response
```

## Backend Modules

- `main.py`: app factory, middleware, CORS, router registration, startup sync.
- `database.py`: SQLAlchemy engine and sessions.
- `models.py`: database tables.
- `schemas.py`: Pydantic request and response models.
- `routes/`: HTTP endpoints.
- `services/`: reusable business logic.
- `rag/`: compatibility namespace for retrieval service imports.
- `scripts/`: import, seed, evaluation, and benchmark tools.

## Retrieval Architecture

The app uses bundled EV data and knowledge articles. Processed JSON and FAISS files live in `backend/data/processed/`. This lets the repository restore the core browsing and chat behavior without relying on a missing local model directory.

The chat system is intentionally strict. If the data cannot support an answer, the expected refusal string is `Not enough data available`.

## Frontend Architecture

The frontend is a Vite React SPA. Pages call `frontend/src/services/api.js`, which uses Axios and attaches JWT tokens from local storage when available.

## Data Architecture

- Source Excel file: `data/raw/India_EV_All_Segments_Dataset_2026_filled.xlsx`
- Curated articles: `backend/data/articles/`
- Processed data and indexes: `backend/data/processed/`
- Relational database: PostgreSQL tables created through Alembic.

## Deployment Architecture

Docker Compose starts:

- `postgres`: pgvector-enabled PostgreSQL
- `redis`: Redis 7
- `backend`: FastAPI container
- `frontend`: production static frontend container
