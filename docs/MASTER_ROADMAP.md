# Master roadmap

| Sprint | Status | Local evidence / next dependency |
|---|---|---|
| 1 Foundation | PASS | Branch audit, API tests and Next build. Browser automation unavailable. |
| 2 Data and inventory | PASS | Fresh SQLite migration, atomic idempotent CSV import/export, canonical mass conversion, entities and stock-integrity tests pass. Production sets `GHOSTWASTE_AUTO_SCHEMA=false` after migration. |
| 3 Forecasting | PARTIAL | Forecast runs/predictions have safe migrations; rolling-origin selection/history APIs plus separately held-out empirical interval coverage pass tests. LightGBM is unavailable locally (`libomp.dylib` missing). |
| 4 Waste risk | PARTIAL | Persisted simulated forecast→recipe→FEFO scenarios expose batch risk, cost, shortage and provenance; Monte Carlo uncertainty is not yet connected to stored workflows. |
| 5 Optimization | PARTIAL | Integrated workflow invokes multi-ingredient planning and creates approval-required persisted recommendations; recipe/prep capacity and persisted optimization scenarios remain. |
| 6 Web app | PARTIAL | Functional scenario lab and recommendation flow; required product pages remain. |
| 7 Evaluation | PARTIAL | Reproducible synthetic fixture experiment script; no real dataset/pilot. |
| 8 Security/QA | PARTIAL | Input validation and API tests; no auth, browser tests, lint/a11y suite. |
| 9 Deployment | PARTIAL | Compose build, frontend-to-API proxy, and SQLite volume persistence are verified locally; external hosting authorization not granted. |
| 10 Presentation | PARTIAL | Submission draft and script; no video/screenshots. |
| 11 Submission | BLOCKED | Eligibility, registration, publishing, and final submit require user access/approval. |
