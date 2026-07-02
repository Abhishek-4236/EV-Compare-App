# Database Guide

## Database Engine

The application uses PostgreSQL. The migration enables the `vector` extension through pgvector for embedding columns.

## Connection String

Set `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ev_compare
```

Docker Compose overrides this to connect to the internal `postgres` service.

## Migrations

Alembic files live in `backend/alembic/`.

Run migrations from `backend/`:

```powershell
python -m alembic upgrade head
```

Create a future migration after model changes:

```powershell
python -m alembic revision --autogenerate -m "describe change"
```

## Seeding

Seed all data:

```powershell
python scripts\seed_manager.py --all
```

Force reload:

```powershell
python scripts\seed_manager.py --all --force
```

## Main Tables

- `users`: registered users and roles.
- `vehicles`: EV catalog rows and embeddings.
- `charging_stations`: charging location data.
- `knowledge_articles`: EV knowledge chunks.
- `subsidy_rules`: state and segment subsidy rules.
- `chat_sessions`, `chat_messages`, `chat_feedback`: chat history and feedback.
- `saved_comparisons`: saved user comparisons.

## Backups

For production, schedule regular PostgreSQL backups. Do not commit database dumps unless they are sanitized sample fixtures.
