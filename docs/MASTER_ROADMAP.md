# Master roadmap

| Sprint | Status | Local evidence / next dependency |
|---|---|---|
| 1 Foundation | PASS | Branch audit, API tests and Next build. Browser automation unavailable. |
| 2 Data and inventory | PASS | Fresh SQLite migration, atomic idempotent CSV import/export, canonical mass conversion, entities and stock-integrity tests pass. Production sets `GHOSTWASTE_AUTO_SCHEMA=false` after migration. |
| 3 Forecasting | PARTIAL | Rolling-origin baseline selection, persisted forecast runs/history APIs and reproducible synthetic evidence pass tests; LightGBM and interval calibration remain. |
| 4 Waste risk | PASS | Multi-batch FEFO plus seeded Monte Carlo API and tests. |
| 5 Optimization | PARTIAL | OR-Tools linear purchase planner; no multi-ingredient recipe/prep solver. |
| 6 Web app | PARTIAL | Functional scenario lab and recommendation flow; required product pages remain. |
| 7 Evaluation | PARTIAL | Reproducible synthetic fixture experiment script; no real dataset/pilot. |
| 8 Security/QA | PARTIAL | Input validation and API tests; no auth, browser tests, lint/a11y suite. |
| 9 Deployment | PARTIAL | Compose build, frontend-to-API proxy, and SQLite volume persistence are verified locally; external hosting authorization not granted. |
| 10 Presentation | PARTIAL | Submission draft and script; no video/screenshots. |
| 11 Submission | BLOCKED | Eligibility, registration, publishing, and final submit require user access/approval. |
