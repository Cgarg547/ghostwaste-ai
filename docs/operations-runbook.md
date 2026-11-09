# Operations runbook

## Local smoke test

Use an isolated database only:

```bash
PYTHONPATH=. .venv/bin/pytest -q
cd apps/web && npx tsc --noEmit --incremental false && npm run build
cd ../.. && ./scripts/run_browser_e2e_isolated.sh
```

The browser runner prints its temporary database and screenshot directory. Retain those paths when collecting evidence; they are not the persistent demo database.

## Incident boundaries

Do not respond to a planning result by changing inventory, approving recommendations, or contacting suppliers automatically. Treat failed optimization, missing prices, unavailable recipe mappings and incompatible comparisons as visible planning failures requiring manager review.

## Data handling

`/demo/load` is idempotent and adds namespaced synthetic records. Browser action checks are local storage only and are not an execution or staff record.
