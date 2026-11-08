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
# Completion audit — local implementation increment

Verified on 2026-11-08 against `feat/full-local-demo`:

1. Added an additive `supplier_ingredients` migration and API to associate a supplier, ingredient, and optional purchase price.
2. Removed the unsafe "fastest supplier wins" workflow behavior. Optimization runs only where the ingredient has an explicit supplier association and known purchase price.
3. Made approval decisions final and reasoned: decision reason requires three characters and a second transition returns HTTP 409.
4. Prevented duplicate menu-item/daily-sale entries.
5. Restored a responsive dark-green GhostWaste application shell with accessible focus states and table overflow handling.

The workflow is still local, synthetic, and approval-only. It does not contact suppliers or place orders.

Verification: 22 pytest tests passed; Next production build passed; `git diff --check` passed. Browser E2E and Docker daemon inspection were unavailable in this execution.
