#!/usr/bin/env sh
set -eu

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for automatic startup. Install Docker and run this script again."
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example"
  cp .env.example .env
fi

echo "Starting EV Compare App with Docker Compose..."
docker compose up --build
