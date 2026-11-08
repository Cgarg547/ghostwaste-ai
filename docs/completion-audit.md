# Completion audit — local demo

## Verified

- Forecasts use leakage-free rolling-origin selection and a final chronological holdout when sufficient history exists.
- Stored workflows include deterministic FEFO risk, reproducible seeded Monte Carlo uncertainty, and CBC planning diagnostics.
- Supplier lead time/minimum orders, storage, and optional preparation capacity are modelled. Recommendations require a recorded human decision and never place orders.
- Direct routes cover inventory/CSV, sales, recipes, forecasts, Waste Radar, optimization, approvals, analytics, and suppliers.
- Local safety includes bounded validation, atomic formula-safe CSV, optional `GHOSTWASTE_API_TOKEN` bearer protection for writes and explicit `GHOSTWASTE_CORS_ORIGINS` opt-in.

## Executed checks

- `python -m pytest tests -q`: **21 passed**.
- `npm run build` in `apps/web`: **passed**; `/` and `/[section]` compiled.

## Remaining blockers

- Playwright/browser binaries are unavailable: `npx playwright --version` did not complete in the sandbox. No browser E2E claim is made.
- Production requires identity/RBAC, rate limits, managed secrets/database, real consented data, and a browser test runner.
