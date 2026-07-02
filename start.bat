@echo off
setlocal

where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
  echo Docker Desktop is required for automatic startup.
  echo Install Docker Desktop, start it, then run start.bat again.
  exit /b 1
)

if not exist ".env" (
  echo Creating .env from .env.example
  copy ".env.example" ".env" >nul
)

echo Starting EV Compare App with Docker Compose...
docker compose up --build
