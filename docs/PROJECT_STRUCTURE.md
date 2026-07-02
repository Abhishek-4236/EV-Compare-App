# Project Structure

```text
EV-Compare-App/
  .dockerignore
  .env.example
  .gitignore
  LICENSE
  README.md
  FINAL_REPORT.md
  PROJECT_CHECKLIST.md
  docker-compose.yml
  package.json
  requirements.txt
  start.bat
  start.sh
  backend/
    alembic.ini
    Dockerfile
    database.py
    main.py
    models.py
    requirements.txt
    schemas.py
    alembic/
    core/
    data/
    rag/
    routes/
    scripts/
    services/
    tests/
  data/
    raw/
  docs/
  frontend/
    Dockerfile
    index.html
    package.json
    package-lock.json
    vite.config.js
    public/
    src/
```

## Backend

`backend/main.py` creates the FastAPI app, middleware, routers, startup data sync, and health route.

`backend/routes/` contains API route modules.

`backend/services/` contains retrieval, chat, safety, dataset, LLM, subsidy, and startup logic.

`backend/alembic/` contains database migrations.

`backend/data/processed/` contains restorable generated artifacts needed by the RAG flow.

## Frontend

`frontend/src/pages/` contains app pages.

`frontend/src/components/` contains reusable UI components.

`frontend/src/services/api.js` is the API client.

`frontend/src/store/` contains Zustand state stores.

## Docs

`docs/` contains beginner-focused operational documentation for setup, database, API, architecture, deployment, and troubleshooting.
