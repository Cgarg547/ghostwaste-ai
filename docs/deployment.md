# Deployment boundary and zero-cost plan

This repository is submission-ready as a local demo, not an approved public production service. SQLite is single-host, has limited write concurrency, and is unsuitable for multi-instance web hosting without a durable shared volume and backup/restore process.

## Local run

Use the README commands. Bind the API to `127.0.0.1`; use a fresh `GHOSTWASTE_DB_PATH` for recordings/tests. `/health` and `/ready` are health endpoints. The Next.js `/api/*` route proxy keeps `BACKEND_ORIGIN` and `API_INTERNAL_TOKEN` server-side.

## Prepared, not executed, staging configuration

`deploy/railway/` documents two services: private API plus public web proxy. Required variables: `BACKEND_ORIGIN`, `API_INTERNAL_TOKEN`, `GHOSTWASTE_API_TOKEN`, `GHOSTWASTE_DB_PATH`, `GHOSTWASTE_AUTO_SCHEMA=false`, `GHOSTWASTE_STAGING_MODE=true`, `GHOSTWASTE_ALLOWED_HOSTS`, `GHOSTWASTE_CORS_ORIGINS`, `GHOSTWASTE_ENABLE_DOCS=false`, and staging basic-auth variables. Start commands are the Dockerfiles and `deploy/railway/start-api.sh`; migrations run with `python -m alembic upgrade head` in staging mode.

Do not deploy without owner approval, a suitable free-tier account review, secret storage, restricted public access, migration rehearsal, and backup/restore test. No public URL exists.
