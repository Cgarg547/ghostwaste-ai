# GhostWaste AI

**Status: Sprint 1 starter prototype — NOT submission-ready.**

A local, synthetic restaurant inventory expiry-risk demo for Arbiter Hacks V1. This starter intentionally does **not** claim real AI forecasting, FEFO batch allocation, optimization, observed waste prevention, food-safety validation, or live deployment.

## Requirements
- Python 3.11+ and Node.js 22+

## Run locally (two terminals)

Terminal 1, from repository root:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
uvicorn apps.api.main:app --reload --port 8000
```

Terminal 2:
```bash
cd apps/web
npm install
npm run dev
```
Open http://localhost:3000. API docs: http://localhost:8000/docs.

## Run tests
```bash
source .venv/bin/activate
python -m pytest tests -q
```

## Current limitations
- Inventory scenario uses hardcoded synthetic examples; UI date defaults to Nov 8, 2026.
- One batch per ingredient; duplicates rejected rather than miscomputed.
- No real demand forecasting; fixed daily-demand assumptions only.
- No food-safety guidance or actual operational action.
- No hosted database, authentication, CSV ingestion or optimizer yet.
- The frontend requires the API on localhost:8000; deploy needs a real API URL and hosting configuration.

See `docs/ROADMAP.md` for release gates.
