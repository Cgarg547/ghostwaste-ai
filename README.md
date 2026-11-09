# GhostWaste AI — restaurant food-waste planning demo

GhostWaste is a local-only restaurant inventory planning demo. It stores data in SQLite, uses synthetic demo records, and creates approval-only recommendations. It never places orders, initiates payments, or contacts suppliers.

It connects dated inventory, recorded sales, evaluated demand forecasts, FEFO expiry exposure, seeded simulation, constrained planning, and explicitly linked supplier intelligence. All impact values are synthetic/modelled—not customer outcomes, savings, or food-safety guidance.

## Judge journey

Load demo data, then follow: Inventory → Forecasting → Waste Radar → Optimization Lab → Supplier Intelligence → Scenario Studio → AI Assistant → Use-First Planner → Daily Action Plan → Action Center → Analytics. Supplier comparisons are read-only; approval writes only a local audit event.

## Requirements

- Python 3.11+ (the supplied containers use Python 3.14)
- Node.js 22+
- Optional: Docker Compose, Google Chrome for the browser smoke suite

## Clean local setup

From a fresh checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
cd apps/web && npm ci && cd ../..
cp .env.example .env  # optional; do not commit it
```

The default database is `data/ghostwaste.db`. For an explicit location, set `GHOSTWASTE_DB_PATH`. SQLite creates the parent directory. Never point tests at an existing demo database.

To use explicit migrations instead of the local-demo auto-schema:

```bash
export GHOSTWASTE_DB_PATH="$PWD/data/ghostwaste.db"
export GHOSTWASTE_AUTO_SCHEMA=false
alembic upgrade head
```

## Run and use the demo

Start the API:

```bash
source .venv/bin/activate
uvicorn apps.api.main:app --reload --port 8000
```

In another terminal:

```bash
cd apps/web
npm run dev
```

Open http://127.0.0.1:3000 and choose **Load demo data**. The loader is idempotent and only adds its namespaced synthetic records; it does not delete or update other local data. It creates inventory, recipe links, sales history, and a persisted forecast. Create a scenario from Waste Radar/Optimization, then approve or reject a recommendation in Action Center. Approval only writes a local audit event.

For Docker, run `docker compose up --build`; open http://127.0.0.1:3000. The compose database is a named volume. Do not use `docker compose down -v` if you want to retain it.

## Checks

```bash
source .venv/bin/activate
python -m pytest tests -q
cd apps/web && npx tsc --noEmit && npm run build
cd ../.. && git diff --check && docker compose config
./scripts/e2e_local_demo.sh
./scripts/run_browser_e2e_isolated.sh
```

The pytest fixture requires a unique temporary path and refuses the development and Docker database locations. The E2E script starts a separate API and web server on loopback with a temporary SQLite file, then renders all eight browser routes in headless Chrome.

## Local safety configuration

`GHOSTWASTE_API_TOKEN` optionally requires a bearer token for writes. `GHOSTWASTE_CORS_ORIGINS` is an explicit comma-separated allow-list; leaving it unset enables no cross-origin browser access. Bind the API to `127.0.0.1` for the documented demo scope. This is not production authentication or authorization.

## Troubleshooting

- Port 8000/3000 in use: stop the other local service or change both the Uvicorn port and `BACKEND_ORIGIN`.
- Fresh database has no data: use **Load demo data**; do not edit SQLite manually.
- `alembic upgrade head` stops on a legacy duplicate daily sale: resolve that data deliberately before rerunning; the migration does not delete records automatically.
- Browser E2E needs macOS Google Chrome at `/Applications/Google Chrome.app`; use the API/backend checks if it is unavailable and record browser verification as partial.

## Submission material

See [submission readiness](docs/submission-readiness.md), [judge walkthrough](docs/submission/demo-script.md), [submission draft](docs/submission-draft.md), and [Vercel public-demo notes](docs/vercel-deployment.md). The public judge build is browser-local synthetic data; it has no FastAPI or SQLite dependency. Screenshots and a public video are intentionally pending until a human records and publishes them.
# Intelligence & kitchen planning additions

The local demo includes GhostWaste Intelligence (deterministic evidence answers), Scenario Studio (ephemeral seeded FEFO/Monte Carlo/CBC calculations), Use-First Planner, Impact Studio, and a Daily Kitchen Action Plan. Load demo data, select its forecast, then use the five new sidebar workspaces. These are planning aids only: simulated changes are not observed savings, and task ticks are browser-local planning state.
