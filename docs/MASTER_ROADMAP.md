# Master roadmap

| Sprint | Status | Local evidence / next dependency |
|---|---|---|
| 1 Foundation | PASS | Branch audit, API tests and Next build. Browser automation unavailable. |
| 2 Data and inventory | PASS | Fresh SQLite migration, atomic idempotent CSV import/export, canonical mass conversion, entities and stock-integrity tests pass. Production sets `GHOSTWASTE_AUTO_SCHEMA=false` after migration. |
| 3 Forecasting | PASS (local demo) | Persisted runs/predictions, leakage-free rolling-origin selection, and separately held-out interval coverage. LightGBM remains optional/unavailable locally (`libomp.dylib` missing). |
| 4 Waste risk | PASS (synthetic) | Forecast→recipe→FEFO scenarios persist deterministic risk plus seeded 500-trial Monte Carlo output, inputs and provenance. |
| 5 Optimization | PASS (local demo) | CBC mixed-integer multi-ingredient plans expose lead-time, supplier-minimum, storage and optional preparation-capacity diagnostics; recommendations require recorded human approval. |
| 6 Web app | PASS (build) | Route-addressable responsive Next app connects inventory/CSV, sales, recipes, forecasts, Waste Radar, optimization, approvals, analytics and suppliers. Browser E2E remains environment-dependent. |
| 7 Evaluation | PARTIAL | Reproducible synthetic fixture experiment script; no real dataset/pilot. |
| 8 Security/QA | PARTIAL | Pydantic limits, atomic formula-safe CSV, optional constant-time bearer write token, explicit opt-in CORS, approval audit trail, 21 backend tests and Next production build. Browser E2E requires local Playwright browser installation. |
| 9 Deployment | PARTIAL | Compose build, frontend-to-API proxy, and SQLite volume persistence are verified locally; external hosting authorization not granted. |
| 10 Presentation | PARTIAL | Submission draft and script; no video/screenshots. |
| 11 Submission | BLOCKED | Eligibility, registration, publishing, and final submit require user access/approval. |
