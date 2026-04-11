# Database Migrations (Alembic)

This project now uses Alembic for schema changes.

## Setup

- Ensure backend venv is active, or use `.venv\Scripts\python` on Windows.
- Ensure `DATABASE_URL` is set in `backend/.env`.

## Apply migrations

```bash
.venv\Scripts\python -m alembic upgrade head
```

## Create a new migration (future schema updates)

```bash
.venv\Scripts\python -m alembic revision -m "describe change"
```

For model-driven diffs (after wiring/validating metadata):

```bash
.venv\Scripts\python -m alembic revision --autogenerate -m "describe change"
```

## Roll back one revision

```bash
.venv\Scripts\python -m alembic downgrade -1
```

## Current migration included

- `20260409_01_add_vehicle_segment_enum.py`
  - Creates enum `vehicle_segment`
  - Adds `vehicles.segment`
  - Backfills from `vehicles.category`
  - Sets default to `FOUR_WHEELER`
