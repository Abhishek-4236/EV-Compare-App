# Personal Git and Run Notes

## 1. Basic Git flow for this repo

GitHub repository:

```text
https://github.com/Abhishek-4236/EV-Compare-App.git
```

Use these commands from the project root:

```powershell
git status
git add .
git commit -m "your message here"
git push origin main
```

If someone is setting the remote for the first time:

```powershell
git init
git branch -M main
git remote add origin https://github.com/Abhishek-4236/EV-Compare-App.git
git push -u origin main
```

If `origin` already exists, update it with:

```powershell
git remote set-url origin https://github.com/Abhishek-4236/EV-Compare-App.git
git push -u origin main
```

If this is the first push for the branch:

```powershell
git push -u origin main
```

If you create a new file, for example this notes file, the same flow works:

```powershell
git add docs/personal-git-and-run-notes.md
git commit -m "Add personal run notes"
git push origin main
```

## 2. If GitHub blocks the push because of secrets

Never put real API keys inside tracked files like `.env.example`.

If a secret gets committed by mistake:

```powershell
git status
```

Fix the file, then run:

```powershell
git add .env.example
git commit --amend --no-edit
git push -u origin main
```

Then rotate the leaked key in the provider dashboard.

## 3. Local backend setup

The backend reads environment variables from:

```text
backend/.env
```

Create it from the example file:

```powershell
Copy-Item .env.example backend/.env
```

Open `backend/.env` and fill in your real local values. Do not commit real keys.

Create and activate the backend virtual environment:

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the backend:

```powershell
uvicorn main:app --reload
```

Backend URLs:

```text
API:  http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs
```

## 4. Local frontend setup

Open a new terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

The frontend proxy is already configured to talk to the backend on port `8000`.

## 5. Database note

Default backend database URL:

```text
postgresql://postgres:postgres@localhost:5432/ev_compare
```

So PostgreSQL should be running locally on port `5432`, unless you change `DATABASE_URL` in `backend/.env`.

## 6. Docker option

If you want to run the stack with Docker instead:

```powershell
+

```

This starts:

```text
Postgres: 5432
Backend:  8000
Frontend: 3000
Redis:    6379
```

## 7. Daily quick-start

Backend terminal:

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn main:app --reload
```

Frontend terminal:

```powershell
cd frontend
npm run dev
```
