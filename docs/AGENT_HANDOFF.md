# Agent handoff

- **Branch:** `feat/full-local-demo`
- **Starting checkpoint:** `2800e91`
- **Current work:** supplier/recipe entities and transaction-safe stock events added (11 passed; Next production build passed).
- **Resume:** `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`; `python scripts/run_experiments.py`.
- **Known external blockers:** deployment account/access, public repository, Devpost, verified video, student eligibility.
- **Next actionable task:** add migration/CSV safe import and recipe-backed inventory flow, then frontend routes and browser test tooling. Re-run `docker compose build` after this session; initial build did not complete within the command window.
