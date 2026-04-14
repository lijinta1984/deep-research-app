#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
cd /app && alembic upgrade head

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A backend.tasks.celery_tasks:celery_app worker \
    --loglevel=info --concurrency=2 &

# Start FastAPI server
echo "Starting FastAPI server..."
uvicorn backend.main:app --host 0.0.0.0 --port 10000
