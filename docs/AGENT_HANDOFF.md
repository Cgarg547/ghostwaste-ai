# Agent handoff

- **Branch:** `feat/full-local-demo`
- **Starting checkpoint:** `2800e91`
- **Current work:** deterministic risk simulation, forecasting utilities and purchase optimizer verified locally (10 passed; Next production build passed).
- **Resume:** `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`; `python scripts/run_experiments.py`.
- **Known external blockers:** deployment account/access, public repository, Devpost, verified video, student eligibility.
- **Next actionable task:** add migration/CSV safe import and recipe-backed inventory flow, then frontend routes and browser test tooling.
