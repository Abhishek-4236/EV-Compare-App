# EV Compare App

EV Compare App is a full-stack electric vehicle intelligence platform for the Indian EV market. It combines a FastAPI backend, a React/Vite frontend, a PostgreSQL database, Redis infrastructure, bundled EV datasets, FAISS retrieval artifacts, and a strict dataset-first chat experience.

The repository is designed to be restorable from GitHub alone. Local secrets, virtual environments, dependency folders, build output, caches, and logs are intentionally excluded.

## Features

- Browse Indian EVs across two-wheelers, three-wheelers, cars, buses, and commercial vehicles.
- Compare EV models by price, range, battery, charging, warranty, and ownership fields.
- Get recommendation shortlists from dataset-backed filters.
- Use a strict EV chat assistant that refuses unsupported answers with `Not enough data available`.
- Estimate route and charging stops from bundled city and station data.
- View subsidy and policy guidance from curated backend services.
- Sign up, log in, save garage data, and manage admin dataset workflows.
- Run locally with manual services or with Docker Compose.

## Architecture

The frontend runs as a Vite React SPA and calls backend routes under `/api`. During local development, `frontend/vite.config.js` proxies `/api` to `http://127.0.0.1:8000`.

The backend exposes FastAPI routers for vehicles, compare, recommendation, chat, subsidies, route planning, auth, garage, and admin workflows. SQLAlchemy models define the relational schema, Alembic manages migrations, and bundled processed data plus FAISS indexes keep the core demo usable without downloading private model files.

## Tech Stack

- Python 3.11+
- FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic
- PostgreSQL 16 with pgvector
- Redis 7
- React 19, Vite, Tailwind CSS
- Axios, React Router, Zustand, Leaflet, Chart.js
- FAISS, pandas, openpyxl
- Docker and Docker Compose

## Folder Structure

```text
EV-Compare-App/
  backend/                 FastAPI app, routes, services, models, migrations, tests
  backend/data/articles/   Curated EV knowledge articles
  backend/data/processed/  Checked-in JSON and FAISS retrieval artifacts
  data/raw/                Source EV Excel dataset
  docs/                    Beginner documentation
  frontend/                React/Vite application
  docker-compose.yml       Postgres, Redis, backend, and frontend stack
  requirements.txt         Root backend dependency pointer
  package.json             Root helper scripts
  start.bat                Windows Docker startup
  start.sh                 Unix Docker startup
```

## Prerequisites

Install these on a fresh Windows PC:

1. Git: https://git-scm.com/download/win
2. Python 3.11 or newer: https://www.python.org/downloads/
3. Node.js 20 LTS or newer: https://nodejs.org/
4. PostgreSQL 16 with pgvector, or Docker Desktop for the bundled database container.
5. Redis 7, or Docker Desktop for the bundled Redis container.
6. Docker Desktop, recommended for the simplest complete startup.

## Installation

```powershell
git clone https://github.com/Abhishek-4236/EV-Compare-App.git
cd EV-Compare-App
copy .env.example .env
```

Edit `.env` and replace `JWT_SECRET` before production use. Keep `.env` private.

## Environment Variables

All variables are documented in `.env.example`.

Required for local backend:

- `DATABASE_URL`: PostgreSQL connection string.
- `JWT_SECRET`: private JWT signing secret.
- `JWT_ALGORITHM`: usually `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: login token lifetime.

Optional:

- `OPENAI_*`, `GROQ_*`, `HF_*`, `NVIDIA_*`: hosted AI providers and reranker settings.
- `EV_EXCEL_PATH`, `EV_JSON_PATH`, `EV_FAISS_INDEX_PATH`, `EV_FAISS_META_PATH`: dataset and retrieval artifact locations.
- `FRONTEND_URL`: allowed CORS origins.
- `RATE_LIMIT_*`: backend rate limiting values.
- `DATASET_UPLOAD_MAX_BYTES`: admin upload size limit.

## Database Setup

Manual PostgreSQL setup:

```powershell
createdb ev_compare
cd backend
python -m alembic upgrade head
python scripts/seed_manager.py --all
```

If `createdb` is not on your PATH, create the `ev_compare` database using pgAdmin and then run the Alembic and seed commands.

## Redis Setup

Manual Redis setup on Windows is easiest through Docker:

```powershell
docker run --name ev-redis -p 6379:6379 -d redis:7-alpine
```

Docker Compose starts Redis automatically.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m alembic upgrade head
python scripts\seed_manager.py --all
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`.

## Running The Project

Manual two-terminal workflow:

Terminal 1:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Docker Instructions

The simplest full restore path is Docker Compose:

```powershell
copy .env.example .env
docker compose up --build
```

Services:

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Windows shortcut:

```powershell
.\start.bat
```

Unix/macOS/Linux shortcut:

```bash
chmod +x start.sh
./start.sh
```

## Deployment

For production:

1. Build and deploy the backend container.
2. Build and deploy the frontend static bundle.
3. Use managed PostgreSQL with pgvector enabled.
4. Use managed Redis if distributed cache/rate limiting is required.
5. Store secrets in the deployment platform, not in Git.
6. Set a strong `JWT_SECRET`.
7. Restrict `FRONTEND_URL` to production domains.
8. Run `alembic upgrade head` during release.

## Common Errors

- `ModuleNotFoundError`: activate the backend virtual environment and reinstall `backend/requirements.txt`.
- `npm is not recognized`: install Node.js and restart PowerShell.
- `psycopg2` or database connection errors: verify PostgreSQL is running and `DATABASE_URL` is correct.
- `relation does not exist`: run `python -m alembic upgrade head`.
- Frontend API errors: confirm backend is running on `127.0.0.1:8000`.
- Port already in use: stop the process using the port or choose another port.

## Troubleshooting

Run these checks:

```powershell
git status
python --version
node --version
npm --version
docker --version
Invoke-RestMethod http://127.0.0.1:8000/health
```

More beginner instructions are in `docs/TROUBLESHOOTING.md`.

## Contributing

1. Create a branch.
2. Keep `.env`, virtual environments, node modules, caches, and build output out of Git.
3. Run backend tests and frontend checks before opening a pull request.
4. Update docs when setup, routes, or environment variables change.

## License

This project is licensed under the MIT License. See `LICENSE`.
