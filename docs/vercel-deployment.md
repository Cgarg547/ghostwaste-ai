# Vercel deployment assessment — 2026-11-09

## Verdict: PARTIAL — the browser-local public demo is suitable; the persistent full stack is not

GhostWaste is a Next.js frontend plus a FastAPI/SQLAlchemy/SQLite backend. The application needs persistent shared records for demo loading, inventory, sales, forecast runs, risk scenarios, approvals, and audit events. Its forecasting stack also includes NumPy, pandas, and OR-Tools.

Vercel currently supports FastAPI as a Python Function, including on Hobby, but this does **not** make the complete application suitable for a single Vercel deployment. Vercel explicitly states that SQLite cannot be used there because Function filesystem storage is ephemeral and concurrently created instances do not share a permanent local file. Therefore a deployed SQLite database could disappear, diverge between instances, or let visitors alter shared records. That violates the demo’s integrity and safety requirements.

## Verified Vercel constraints

| Area | Status | Evidence |
|---|---|---|
| Next.js frontend | PASS | Native Vercel target; current production build passes locally. |
| FastAPI Python Function | PARTIAL | Python/FastAPI Functions are supported, but Python runtime is beta and the full app becomes one Function. |
| Function package | UNKNOWN | Standard Python bundle limit is 500 MB uncompressed. NumPy, pandas, and OR-Tools must be measured in Vercel’s build; no account/deploy was authorized. Large Functions is beta and should not be assumed. |
| Duration / Hobby | PARTIAL | Hobby has free usage quotas and historical 60-second configurable maximum; current Fluid Compute documentation may list 300 seconds. Do not rely on a changed plan limit without confirming it in the deployment dashboard. |
| SQLite persistence | FAIL | Vercel documents that SQLite cannot be used because serverless local storage is ephemeral and unshared. |
| Safe public shared demo | FAIL | Existing write endpoints and demo loader would need a durable database, identity/authorization or a dedicated read-only demo API, and rate/abuse controls. |

Primary sources: [Python runtime](https://vercel.com/docs/functions/runtimes/python), [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Function limits](https://vercel.com/docs/functions/limitations), [SQLite limitation](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel), and [Hobby plan](https://vercel.com/docs/plans/hobby). Recheck them immediately before any deployment because plan/runtime terms change.

## Do not deploy this repository to Vercel as-is

Do not add `vercel.json`, point `GHOSTWASTE_DB_PATH` at `/tmp`, or set `GHOSTWASTE_AUTO_SCHEMA=true` for a public Function. Those changes would make the app appear to work while losing/fragmenting shared state. Do not expose the existing mutable API with an embedded browser token: it would not provide visitor-level authorization.

`GHOSTWASTE_PUBLIC_DEMO=true` is now a server-side fail-closed guard in the Next.js proxy. It blocks every write with `403`, returns `503` for reads, and does not proxy any request to `BACKEND_ORIGIN`. The client uses the bundled `src/lib/publicDemo.ts` synthetic fixture directly, so public-mode page interactions make no network API request. It includes deterministic forecast, FEFO, supplier, scenario/impact example, action-plan, and browser-local simulated approval data. Scenario Studio offers only clearly labeled precomputed synthetic variants; it does not claim to run OR-Tools in the browser.

The public AI Assistant is deterministic and fixture-grounded, not a live LLM. It never calls FastAPI, `/api`, or an external provider. It explains bundled Romaine expiry/FEFO, inventory, forecast values, modeled-waste limitations, precomputed optimization, supplier trade-offs, and missing prices. Unsupported questions explicitly state that only fixed synthetic records are available. Approval state is browser-local; task checks use local storage and Reset Demo clears them.

## Public-demo build

Deploy the `apps/web` directory as a Next.js project with build command `npm run build`. Set only `NEXT_PUBLIC_GHOSTWASTE_PUBLIC_DEMO=true` and `GHOSTWASTE_PUBLIC_DEMO=true`. Do **not** set `BACKEND_ORIGIN`, `API_INTERNAL_TOKEN`, database variables, or Python requirements for this project. The public proxy guard remains a defense-in-depth boundary; the browser fixture is the data source.

## Architecture decision

Option A (client-side/static synthetic dataset) is the only plausible one-project $0 Vercel path. It would require a new, reviewed browser-local implementation of the demonstrable calculations and fixed synthetic fixtures. Option B (stateless Python Functions) can retain FastAPI calculation endpoints but cannot provide the shared SQL workflow; OR-Tools bundle/native compatibility also remains unverified on Vercel. Option C still requires an external durable database and an authorization design. None is safe to claim complete in this repository without that material implementation and Vercel build evidence.

## Smallest honest path

1. **For the hackathon demo now:** run the documented local isolated demo. It preserves the complete workflow and synthetic-data boundary at $0.
2. **For a future public Vercel frontend:** first replace SQLite with a separately approved durable managed SQL service that has a genuinely available free tier, run reviewed migrations, and add a public-demo mode that serves a fixed synthetic snapshot and rejects all persistent write routes. This is a material architecture change, not safe to infer during deployment preparation.
3. **Alternative hosting:** a single always-on/container service with a durable volume can technically run the current stack, but providers’ free tiers and volume availability change frequently. No specific provider is recommended here without owner approval and a fresh pricing/security review.

## Safe local verification

```bash
./.venv/bin/python -m pytest
cd apps/web && npx tsc --noEmit && npm run build
cd ../.. && ./scripts/run_browser_e2e_isolated.sh
```

The isolated browser command uses a fresh temporary SQLite database. It does not alter `data/ghostwaste.db`, create cloud resources, or contact suppliers.

Public-demo production verification (no FastAPI or `BACKEND_ORIGIN`):

```bash
cd apps/web
npx playwright test -c playwright.public-demo.config.ts
```

Latest local result: **2 passed**. The harness builds and starts Next.js with both public-demo variables, verifies browser-local synthetic navigation, scenario, supplier, approval, reset, mobile navigation, and deterministic assistant behavior. It confirms no frontend `/api` request, checks direct public API `POST` is `403` while `GET` is `503`, and verifies assistant history is session-local and cleared by Reset Demo.

Live audit on 2026-11-09: `https://ghostwaste-ai-web.vercel.app` returned HTTP 200 and rendered the public synthetic labels. Its direct `GET /api/ingredients` returned 503 and a rejected `POST /api/ingredients` returned 403. This is a read-only boundary check, not proof that unpublished local changes have reached Vercel.

## Environment reference (not a Vercel deployment recipe)

Local-only API: `GHOSTWASTE_DB_PATH`, `GHOSTWASTE_AUTO_SCHEMA`, optionally `GHOSTWASTE_API_TOKEN`, `GHOSTWASTE_CORS_ORIGINS`, and `GHOSTWASTE_ALLOWED_HOSTS`.

Next.js proxy: `BACKEND_ORIGIN` and, only for a separately secured server-to-server deployment, `API_INTERNAL_TOKEN`. Never expose either token with a `NEXT_PUBLIC_` prefix.
