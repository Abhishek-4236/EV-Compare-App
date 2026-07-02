# Troubleshooting

## Backend Does Not Start

Check Python and dependencies:

```powershell
python --version
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m py_compile main.py
```

## Database Connection Fails

Confirm PostgreSQL is running and `DATABASE_URL` is correct.

```powershell
python -m alembic upgrade head
```

If the database does not exist, create `ev_compare` in pgAdmin or with `createdb`.

## Frontend Cannot Reach Backend

Confirm backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Confirm Vite is using the proxy in `frontend/vite.config.js`.

## Port Already In Use

Find a process on port 8000:

```powershell
netstat -ano | findstr :8000
```

Stop the process in Task Manager or run backend on another port and update the frontend proxy.

## npm Install Fails

Delete generated files and reinstall:

```powershell
cd frontend
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
npm install
```

## Chat Gives Refusal

The chat assistant is strict by design. If the dataset does not support the answer, it should say `Not enough data available`.

## Docker Compose Fails

Confirm Docker Desktop is running:

```powershell
docker version
docker compose version
```

Then rebuild:

```powershell
docker compose up --build
```
