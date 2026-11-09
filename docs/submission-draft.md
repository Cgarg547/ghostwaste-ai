# GhostWaste AI — Devpost draft

**Tagline:** Turn dated inventory and demand signals into explainable, approval-only food-waste planning.

## Inspiration

Kitchen teams can see stock totals without seeing which dated batches are likely to expire before forecast demand uses them. GhostWaste makes those trade-offs inspectable without pretending that a model can make a purchasing or food-safety decision.

## What it does

GhostWaste combines local inventory, sales, recipes, explicit supplier links, forecast evaluation, FEFO expiry analysis, seeded simulation, constrained planning, and manager review. It highlights use-first work, missing supplier data, lead-time eligibility, minimum orders, and assumptions. It never places orders or contacts suppliers.

## How we built it

Next.js/React frontend, FastAPI/Pydantic/SQLAlchemy API, SQLite local persistence, evaluated forecasting baselines, deterministic FEFO allocation, seeded Monte Carlo, and OR-Tools CBC optimization. Playwright and pytest exercise the workflow in isolated SQLite databases.

## Challenge / accomplishment / lessons

The challenge was keeping planning useful when inputs are incomplete. We chose visible missing-data states and explicit supplier links over invented ratings or prices. We built a reproducible local workflow with a human approval boundary. We learned that operational credibility requires honest uncertainty, traceable assumptions, and deployment/security limits alongside polished visuals.

## Future work

With consented pilots: role-based access, PostgreSQL, backups, observability, supplier/catalog integrations, measured intervention outcomes, and validation against real operating data.

## Theme Track problem and measurement

GhostWaste targets avoidable restaurant food waste caused by expiry risk and planning uncertainty. In a consented pilot, success would be measured with before/after kilograms discarded per ingredient, expiry-related cost, stockouts, and recommendation adoption, using consistent inventory procedures and a defined baseline. This demo reports no real-world reduction or savings.

**Built with:** Next.js, React, TypeScript, FastAPI, Pydantic, SQLAlchemy, SQLite, OR-Tools, Playwright, pytest.
