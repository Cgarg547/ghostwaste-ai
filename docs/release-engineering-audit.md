# Release engineering audit — 2026-11-09

## Baseline and worktree

- Branch / HEAD: `feat/full-local-demo` / `efc1906`.
- The worktree was already dirty with tracked and untracked implementation, test, documentation, assets, and migration files. It was preserved; no reset, clean, volume operation, or persistent SQLite write was performed.
- This audit was performed against source and isolated tests, not prior PASS statements.

## Implemented inventory

| Area | Verified status | Evidence |
|---|---|---|
| Eight core workspaces | PASS | Routes and isolated Playwright workflow cover setup, forecast, workflow, decisions, audit and responsive navigation. |
| Intelligence workspaces | PASS, bounded | `IntelligenceViews.tsx`, five read-only APIs, isolated API and browser tests. |
| Data model | PASS for local demo | SQLite SQLAlchemy tables for ingredients, batches, sales, suppliers, recipes, forecasts, scenarios, recommendations and audits. No task table by design. |
| Migrations | PARTIAL | Alembic revisions exist; Compose still enables local `create_all`, so migration-first deployment is a prerequisite. |
| Docker | PARTIAL | Images build app stages and Compose validates; no public deployment security posture is asserted. |

## API inventory

Core: `/health`, `/dashboard`, `/demo/load`, inventory, supplier, recipe, sale, forecast, risk-scenario, recommendation and audit routes. Calculation APIs: `/scenario`, `/risk/simulate`, `/optimization/purchase`, `/optimization/multi-ingredient`, `/workflows/forecast/{run_id}`. Intelligence APIs: `/intelligence/ask`, `/scenario-studio/run`, `/use-first`, `/impact/compare`, `/action-plan`.

## Findings

- PASS: tests force a uniquely named temporary SQLite parent and reject development/Docker DB paths.
- PASS: input models use Pydantic bounds; SQLAlchemy parameterization and SQLite foreign keys are enabled; CSV import rejects formula-leading cells.
- PASS: deterministic seed is returned for Monte Carlo/Studio; saved scenarios are immutable snapshots; recommendation decisions are final.
- PARTIAL: local API write protection is optional bearer-token protection, not multi-user authentication or authorization.
- PARTIAL: new calculation endpoints return structured dictionaries but not explicit Pydantic response models.
- PARTIAL: browser task state is intentionally device/browser-local, not staff history.
- FAIL for public deployment: SQLite, optional auth, auto schema, no TLS/reverse proxy/observability/backup automation, and no authorization model.

## Verified test scope

See `final-release-readiness.md` for command results. Chrome was available for the isolated Playwright runner. Safari was not available and remains unverified.
