#!/bin/bash
set -e

echo "=== DevForge FastAPI Backend Startup ==="

# Wait for database
echo "Waiting for PostgreSQL..."
max_attempts=30
attempt=0
while ! nc -z postgres 5432 2>/dev/null; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo "PostgreSQL failed to start in time"
        exit 1
    fi
    echo "Attempt $attempt/$max_attempts: Waiting for PostgreSQL..."
    sleep 2
done

echo "PostgreSQL is ready"

# Wait for Redis
echo "Waiting for Redis..."
attempt=0
while ! nc -z redis 6379 2>/dev/null; do
    attempt=$((attempt+1))
    if [ $attempt -ge $max_attempts ]; then
        echo "Redis failed to start in time"
        exit 1
    fi
    echo "Attempt $attempt/$max_attempts: Waiting for Redis..."
    sleep 2
done

echo "Redis is ready"

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head 2>/dev/null || echo "Alembic not configured, skipping migrations"

# Start FastAPI server
echo "Starting FastAPI server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --access-log
