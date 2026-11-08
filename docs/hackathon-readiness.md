# Hackathon readiness audit — 2026-11-08

## Latest verified local gate

- ` .venv/bin/python -m pytest tests -q`: **22 passed** (27 non-failing deprecation warnings).
- `cd apps/web && npm run build`: **passed**; routes `/` and dynamic `/<section>` generated.
- `git diff --check`: passed.
- Supplier constraints are now explicit: a purchase plan only uses a supplier linked to that ingredient with a known local purchase price. Unlinked or price-unknown ingredients generate no purchase recommendation.
- Browser E2E was not run: no Playwright package/binaries were present, and no dependency download was attempted.
- Docker daemon access was unavailable to this sandbox, so running-container/build freshness and named-volume state were not independently inspected. No Docker command that changes volumes was run.

| Requirement | Status | Evidence / next action |
|---|---|---|
| Theme alignment | PASS | Expiry-aware food inventory planning; `apps/api/main.py`. |
| Working local functionality | PASS | Scenario, inventory, sales, forecast baseline, recommendations; `pytest tests -q` (7 passed) and `npm run build` passed. |
| AI forecasting | PARTIAL | Moving-average baseline endpoint exists; no validated ML model or chronological metrics. |
| FEFO waste risk | PASS | Deterministic multi-batch FEFO, expiry hard boundary, tests in `tests/test_api.py`. |
| Optimization engine | PASS (demo) | CBC multi-ingredient planning models lead time, supplier minimums, storage and preparation capacity; no order executes automatically. |
| Waste impact evidence | PARTIAL | Synthetic projections explicitly labeled; no observed intervention outcomes. |
| Security / production API | PARTIAL | Validated inputs, formula-safe atomic CSV, optional token-protected writes, opt-in CORS and audit trails exist. Production still needs identity, RBAC, rate limits and managed secrets. |
| Browser functionality | PARTIAL | Production web build passes; no Playwright browser run in this environment. |
| Public deployment | BLOCKED | Requires user-controlled hosting/account authorization. |
| Public repository, video, Devpost | BLOCKED | External publication and eligibility confirmation require the user. |

Do not call this submission-ready until the FAIL/PARTIAL items are addressed. Test commands: `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`.
