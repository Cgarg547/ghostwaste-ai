# Agent handoff

- **Branch:** `feat/full-local-demo`
- **Starting checkpoint:** `2800e91`
- **Current work:** Docker proxy and persistence verified: frontend `/api/openapi.json` responds and an ingredient survived an API-only safe recreation of the volume-backed SQLite container.
- **Resume:** `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`; `python scripts/run_experiments.py`.
- **Known external blockers:** deployment account/access, public repository, Devpost, verified video, student eligibility.
- **Next actionable task:** feed recipe-driven demand into persisted FEFO risk scenarios, then multi-ingredient optimization.
