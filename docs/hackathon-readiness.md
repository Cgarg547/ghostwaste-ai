# Hackathon readiness audit — 2026-11-08

| Requirement | Status | Evidence / next action |
|---|---|---|
| Theme alignment | PASS | Expiry-aware food inventory planning; `apps/api/main.py`. |
| Working local functionality | PASS | Scenario, inventory, sales, forecast baseline, recommendations; `pytest tests -q` (7 passed) and `npm run build` passed. |
| AI forecasting | PARTIAL | Moving-average baseline endpoint exists; no validated ML model or chronological metrics. |
| FEFO waste risk | PASS | Deterministic multi-batch FEFO, expiry hard boundary, tests in `tests/test_api.py`. |
| Optimization engine | FAIL | OR-Tools purchasing/prep/menu optimization not implemented. |
| Waste impact evidence | PARTIAL | Synthetic projections explicitly labeled; no observed intervention outcomes. |
| Security / production API | PARTIAL | Validated API inputs and local transactions exist; auth, CORS restriction, migrations, rate limits, and upload safety are missing. |
| Browser functionality | PARTIAL | Production web build passes; no Playwright browser run in this environment. |
| Public deployment | BLOCKED | Requires user-controlled hosting/account authorization. |
| Public repository, video, Devpost | BLOCKED | External publication and eligibility confirmation require the user. |

Do not call this submission-ready until the FAIL/PARTIAL items are addressed. Test commands: `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`.
