# Agent handoff — current checkpoint

Current local-demo readiness is **PASS**. Rerun: `source .venv/bin/activate && python -m pytest tests -q`, `./scripts/e2e_local_demo.sh`, then the web checks in `README.md`. The E2E runner uses a temporary database and web copy, requiring free ports 18000/13000 and macOS Google Chrome.

Do not call this production-ready: Safari and Docker runtime verification remain incomplete, and production needs identity/RBAC, rate limits, TLS, managed secrets/database, and dependency scanning.

## Superseded baseline notes

- **Branch:** `feat/full-local-demo`
- **Starting checkpoint:** `7ee0a4b`
- **Current work:** Stored forecast workflows now include reproducible Monte Carlo risk and CBC planning diagnostics; the route-addressable web console covers the local restaurant workflow.
- **Resume:** `source .venv/bin/activate && python -m pytest tests -q`; `cd apps/web && npm run build`.
- **Known external blockers:** deployment account/access, public repository, Devpost, verified video, student eligibility.
- **Next actionable task:** install Playwright/browser binaries when network approval is available, then run desktop and mobile E2E against Docker Compose or local API/web processes.
# 2026-11 intelligence handoff

New UI lives in `apps/web/src/components/IntelligenceViews.tsx`; API logic is in `apps/api/main.py`. Do not convert `/scenario-studio/run` or `/impact/compare` into persistence paths without an additive migration and isolation tests. Preserve the safety statements around synthetic impact and expired stock.
