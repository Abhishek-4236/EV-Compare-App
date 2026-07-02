# Deployment Guide

## Production Checklist

- Use a strong `JWT_SECRET`.
- Store secrets in the hosting provider, not in Git.
- Set `APP_ENV=production`.
- Restrict `FRONTEND_URL` to production domains.
- Use managed PostgreSQL with pgvector enabled.
- Run `alembic upgrade head` before serving traffic.
- Configure HTTPS at the reverse proxy or hosting layer.
- Add database backups and monitoring.

## Docker Deployment

Build locally:

```powershell
docker compose build
```

Run locally:

```powershell
docker compose up
```

For a server, copy the repository, create `.env`, and run the same compose command. For real production, use a deployment platform with managed secrets and persistent volumes.

## Backend Deployment

Backend command:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Before starting backend:

```bash
alembic upgrade head
```

## Frontend Deployment

Build frontend:

```bash
cd frontend
npm ci
npm run build
```

Serve `frontend/dist` with a static web server. Configure the frontend host to call the deployed backend API.

## Database Deployment

Enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then run migrations.

## Rollback

Keep the previous image and database backup. If a release fails, redeploy the previous image and restore the backup if schema/data changes require it.
