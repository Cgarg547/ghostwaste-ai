# Master roadmap

| Sprint | Status | Local evidence / next dependency |
|---|---|---|
| 1 Foundation | PASS | Branch audit, API tests and Next build. Browser automation unavailable. |
| 2 Data and inventory | PASS | Fresh SQLite migration, atomic idempotent CSV import/export, canonical mass conversion, entities and stock-integrity tests pass. Production sets `GHOSTWASTE_AUTO_SCHEMA=false` after migration. |
| 3 Forecasting | PARTIAL | Forecast runs and individual prediction records have executable safe migrations; rolling-origin selection/history APIs and synthetic evidence pass tests. LightGBM and interval calibration remain. |
| 4 Waste risk | PARTIAL | Multi-batch FEFO plus seeded Monte Carlo API/tests and recipe-driven forecast ingredient-demand endpoint; persisted risk scenarios remain. |
| 5 Optimization | PARTIAL | OR-Tools linear purchase planner; no multi-ingredient recipe/prep solver. |
| 6 Web app | PARTIAL | Functional scenario lab and recommendation flow; required product pages remain. |
| 7 Evaluation | PARTIAL | Reproducible synthetic fixture experiment script; no real dataset/pilot. |
| 8 Security/QA | PARTIAL | Input validation and API tests; no auth, browser tests, lint/a11y suite. |
| 9 Deployment | PARTIAL | Compose build, frontend-to-API proxy, and SQLite volume persistence are verified locally; external hosting authorization not granted. |
| 10 Presentation | PARTIAL | Submission draft and script; no video/screenshots. |
| 11 Submission | BLOCKED | Eligibility, registration, publishing, and final submit require user access/approval. |
