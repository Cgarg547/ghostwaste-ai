# API and database reference

Interactive OpenAPI documentation is available locally at `/docs` unless disabled. This reference groups the implemented endpoints; all write endpoints are local only.

## API overview

| Area | Endpoints | Purpose |
|---|---|---|
| Health/dashboard | `GET /health`, `GET /dashboard` | Local service status and read-only operational rollup |
| Demo/scenario | `POST /demo/load`, `POST /scenario`, `POST /risk/simulate` | Idempotent namespaced demo load; deterministic FEFO; seeded simulation |
| Planning | `POST /optimization/purchase`, `POST /optimization/multi-ingredient`, `POST /workflows/forecast/{run_id}` | Isolated planning functions and the persisted end-to-end workflow |
| Inventory | `GET/POST /ingredients`, `GET/POST /batches`, `POST /batches/{id}/consume`, `POST /batches/{id}/waste`, `GET /inventory/export.csv`, `POST /inventory/import` | Local inventory lifecycle; import validates before committing |
| Sales/forecast | `GET/POST /sales`, `GET /forecast/{menu_item}`, `POST /forecasts/{menu_item}`, `GET /forecast-runs`, `GET /forecast-runs/{id}`, `GET /forecasts/{menu_item}/history` | Baseline preview and persisted evaluated forecast runs |
| Recipes/demand | `GET/POST /recipes`, `POST /recipes/{id}/ingredients`, `GET /forecasts/{run_id}/ingredient-demand` | Recipe mapping and forecast-to-ingredient translation |
| Suppliers | `GET/POST /suppliers`, `POST /suppliers/{id}/ingredients` | Explicit local lead time, minimum, ingredient price association |
| Evidence/workflow | `GET /risk-scenarios`, `GET /risk-scenarios/{id}`, `POST /recommendations/from-scenario`, `GET /recommendations`, `POST /recommendations/{id}/decision`, `GET /audit-events` | Persist/retrieve modeled outputs and record final local review |

Responses label the relevant provenance, such as `synthetic_scenario`, `local_demo_sales`, or `simulated_forecast_recipe_inventory`. Do not relabel these fields as observed outcomes.

## Core database model

| Table | Key fields | Role |
|---|---|---|
| `ingredients` | name, unit, storage category | Ingredient catalog |
| `inventory_batches` | ingredient, quantity kg, unit cost, received/use-by dates | Batch-aware stock state |
| `daily_sales` | menu item, day, quantity | Local time series |
| `recipes`, `recipe_ingredients` | yield; ingredient kg per yield | Sales-to-demand translation |
| `suppliers`, `supplier_ingredients` | lead days, minimum; explicit unit price | Eligible planning constraints |
| `forecast_runs`, `forecast_predictions` | model, metrics JSON, prediction JSON/date/interval | Reproducible forecast evidence |
| `risk_scenarios` | forecast run, seed, inputs JSON, outputs JSON | Reproducible modeled workflow snapshot |
| `recommendations` | title, pending/accepted/rejected, estimated kg | Approval queue only |
| `audit_events` | event type, detail, timestamp | Local accountability trail |
| `consumption_events`, `waste_events` | batch, amount, date, note/reason | Stock-change history |

Foreign keys link batches to ingredients; recipe and supplier association tables avoid implicit relationships. The current SQLite schema is created automatically for the local demo; Alembic migration files are present for controlled schema evolution. A production service must execute and verify migrations deliberately rather than relying on automatic schema creation.

## Integrity and safety controls

- Batch use-by may not precede received date; negative stock and waste above available stock are rejected.
- CSV import stages and validates all rows before one commit; failures roll back. Export escapes spreadsheet-formula-leading text.
- Supplier use is explicit; unknown prices create visible unmet shortage instead of a recommendation.
- Recommendation decisions are final and require a reason; repeat decisions return a conflict.
- Tests isolate the database and reject protected development/Docker paths.
- Optional token verification applies to non-read methods when `GHOSTWASTE_API_TOKEN` is set. This is not full authentication or authorization.
# New read-only contracts

- `POST /intelligence/ask`: deterministic intent-matched explanation with source route and no side effects.
- `POST /scenario-studio/run`: validated `StudioIn`; returns ephemeral seeded simulation and solver result.
- `GET /use-first`: FEFO batch priorities, units, expiry and forecast exposure.
- `POST /impact/compare`: two compatible `StudioIn` objects; rejects incompatible methodology.
- `GET /action-plan`: stable suggested task identifiers. Completion is not an API mutation.
