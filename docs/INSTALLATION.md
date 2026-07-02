# Installation Guide

This guide assumes a brand-new Windows PC.

## Step 1: Install Git

Download Git from https://git-scm.com/download/win and install it with the default options. Restart PowerShell after installation.

Verify:

```powershell
git --version
```

## Step 2: Install Python

Install Python 3.11 or newer from https://www.python.org/downloads/. During installation, enable "Add python.exe to PATH".

Verify:

```powershell
python --version
python -m pip --version
```

## Step 3: Install Node.js

Install Node.js 20 LTS or newer from https://nodejs.org/.

Verify:

```powershell
node --version
npm --version
```

## Step 4: Install PostgreSQL

Install PostgreSQL 16 from https://www.postgresql.org/download/windows/. Remember the password you set for the `postgres` user.

Create a database named `ev_compare` using pgAdmin or PowerShell:

```powershell
createdb -U postgres ev_compare
```

## Step 5: Install Redis

On Windows, Redis is easiest through Docker:

```powershell
docker run --name ev-redis -p 6379:6379 -d redis:7-alpine
```

If you use `docker compose up --build`, Redis starts automatically.

## Step 6: Clone Repository

```powershell
git clone https://github.com/Abhishek-4236/EV-Compare-App.git
cd EV-Compare-App
```

## Step 7: Create Virtual Environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Step 8: Install Backend Packages

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Step 9: Install Frontend Packages

Open another PowerShell window:

```powershell
cd EV-Compare-App\frontend
npm install
```

## Step 10: Configure Environment Variables

From the repository root:

```powershell
copy .env.example .env
```

Edit `.env`. At minimum, confirm `DATABASE_URL` and replace `JWT_SECRET`.

## Step 11: Run Database Migration

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
```

## Step 12: Seed Database

```powershell
python scripts\seed_manager.py --all
```

The app also includes processed JSON and FAISS artifacts, so the chat and browse features can use bundled files even before a full database seed.

## Step 13: Start Backend

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Step 14: Start Frontend

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Step 15: Open Browser

Open http://127.0.0.1:5173 and verify that pages load. Also open http://127.0.0.1:8000/docs for API docs.
