# Agent handoff

- **Branch:** `feat/full-local-demo`
- **Starting checkpoint:** `2800e91`
- **Current work:** executable fresh-DB migration and atomic CSV import/export added (13 passed; Next production build passed).
- **Resume:** `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`; `python scripts/run_experiments.py`.
- **Known external blockers:** deployment account/access, public repository, Devpost, verified video, student eligibility.
- **Next actionable task:** add unit conversion and duplicate import policy, then rolling-origin forecast selection and recipe-backed inventory flow.
