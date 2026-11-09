# Deployment configuration runbook

## Readiness

- **Local demo ready:** yes, after the verification suite passes.
- **Deployment configuration ready:** partial; Dockerfiles and Compose exist, but a migration-first, authenticated deployment has not been exercised.
- **Public internet ready:** no. Do not expose this build publicly as-is.

## Required gates before any deployment

1. Use managed durable storage (not SQLite volume) and take a tested backup.
2. Set `GHOSTWASTE_AUTO_SCHEMA=false`; run reviewed Alembic migrations in a maintenance workflow.
3. Put API behind authenticated, authorized access and an HTTPS reverse proxy; set a high-entropy `GHOSTWASTE_API_TOKEN` only as an interim local guard.
4. Set explicit `GHOSTWASTE_CORS_ORIGINS`, run as a non-root user, constrain network exposure, and add secret management, logs, monitoring, alerts, and retention.
5. Run the test, TypeScript, build, Compose validation and isolated E2E commands before promoting an artifact.

## Backup and restore (operator procedure)

Stop application writes first. Copy the SQLite file using SQLite's backup mechanism or a filesystem snapshot, checksum it, encrypt/store it under approved retention policy, and restore only into a separate environment for validation. Never overwrite a live DB while diagnosing.

## Compose notes

Compose owns a named `ghostwaste_data` volume. Do not run `docker compose down -v` unless an operator explicitly intends to erase it. No service was started, restarted, rebuilt, or migrated during this release audit.
