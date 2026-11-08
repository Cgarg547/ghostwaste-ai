# Test results

Run after adding deterministic simulation and OR-Tools purchase planning:

```text
source .venv/bin/activate && python -m pytest tests -q
cd apps/web && npm run build
python scripts/run_experiments.py
```

Verification checkpoint on `feat/full-local-demo`: `10 passed` in 0.64s; `npm run build` passed; the experiment script completed and regenerated `docs/evaluation-results.md`. The run emitted 7 warnings: FastAPI's deprecated startup decorator, Starlette's TestClient deprecation, SQLAlchemy `utcnow` deprecation, and OR-Tools SWIG module metadata warnings. They are non-blocking but should be resolved before release.
