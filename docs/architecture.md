# Architecture

GhostWaste is a local-first demo: a Next.js 16 client calls a FastAPI 0.2 API through the development rewrite. The API stores inventory, daily sales, recommendations, and audit events in local SQLite through SQLAlchemy.

`Web UI → /api rewrite → FastAPI → SQLAlchemy → SQLite`

The risk engine is deterministic and batch-aware: it orders batches FEFO, treats use-by as a hard boundary, and allocates demand before calculating remainder at risk. The forecast endpoint is an explicitly labeled moving-average baseline from recorded local sales. Recommendation generation creates approval-required records only; it never contacts suppliers or takes operational action.

Production needs PostgreSQL, Alembic migrations, authentication, CORS allowlisting, a durable worker, and an independently validated forecast/optimization service. This local demo must not be exposed as an unauthenticated writable API.

Local container packaging is supplied in `Dockerfile.api`, `Dockerfile.web`, and `docker-compose.yml`. It is only a local demonstration configuration: SQLite remains inside the API container until a production database URL and migrations are implemented.
