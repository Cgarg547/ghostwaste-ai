#!/bin/sh
set -eu

if [ "${GHOSTWASTE_STAGING_MODE:-false}" = "true" ]; then
    if [ -z "${GHOSTWASTE_DB_PATH:-}" ]; then
        echo "ERROR: GHOSTWASTE_DB_PATH is required in staging."
        exit 1
    fi

    if [ "${GHOSTWASTE_AUTO_SCHEMA:-false}" != "false" ]; then
        echo "ERROR: Automatic schema creation must be disabled in staging."
        exit 1
    fi

    echo "Running database migrations..."
    python -m alembic upgrade head
    echo "Database migrations completed."
fi

echo "Starting GhostWaste API..."
exec uvicorn apps.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}"
