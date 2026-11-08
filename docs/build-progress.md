# Build progress

| Stage | Status | Evidence |
|---|---|---|
| Baseline audit | PASS | `docs/baseline-audit.md`; initial test/build output. |
| Persistent inventory vertical slice | PASS | SQLite ingredient/batch/supplier/recipe APIs plus transactional consumption and waste recording in `apps/api/main.py`; integrity test passes. |
| FEFO waste-risk engine | PASS | `/scenario` uses ordered batch allocation; unit tests cover primary and overlap cases. |
| Forecasting | PARTIAL | Moving-average baseline endpoint only; no backtested ML candidate. |
| Optimization | PARTIAL | OR-Tools single-ingredient purchase planner implemented; multi-ingredient preparation model remains. |
| Approval flow | PASS | Generated recommendations, manager accept/reject endpoint, audit events. |
| Production hardening | PARTIAL | Pydantic validation and local transaction commits; auth, Alembic, CORS policy and upload controls remain. |
| Frontend expansion | PARTIAL | Functional scenario lab; full multi-page operational dashboard remains. |
