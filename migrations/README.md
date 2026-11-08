# Migrations

Alembic is pinned in `apps/api/requirements.txt`. The application currently creates its local demo SQLite schema at startup for backwards-compatible developer setup. Before production, replace `Base.metadata.create_all` with migration-only startup and generate a complete revision from `apps.api.main.Base.metadata`.

Run a fresh schema upgrade after adding standard Alembic environment files:

```bash
alembic upgrade head
```

This repository does not yet treat the migration layer as production-ready; it is tracked as PARTIAL in the roadmap.
