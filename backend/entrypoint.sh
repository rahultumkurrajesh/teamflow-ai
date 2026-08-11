#!/usr/bin/env bash
# Runs database migrations, then starts the API server.
# Putting migrations here (not in the app) means the schema is always current
# before the app serves a request, and migrations run exactly once per deploy.
set -euo pipefail

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
