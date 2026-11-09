# Online deployment readiness — Railway staging candidate

## Status

| Area | Status | Evidence |
|---|---|---|
| Hosted URL | UNKNOWN | No Railway project/account access or deployment authorization was provided. |
| Railway architecture | PASS | Two-service design configured in `deploy/railway/`; public web + private API + API-only volume. |
| Access boundary | PASS for configured staging design | Web Basic Auth covers pages and `/api/*`; API has no public domain and requires the internal bearer token for writes. |
| Persistent storage | PASS in local rehearsal / PARTIAL hosted | Temporary bind-mounted SQLite persisted through API restart. Hosted Railway volume has not been provisioned. |
| Container builds | PASS | `ghostwaste-api:staging-check` and `ghostwaste-web:staging-check` built. |
| 13 workspaces | PASS locally / UNKNOWN hosted | Isolated browser workflows pass; no live URL exists. |
| Internet deployment | BLOCKED | Requires account, explicit authorization, reviewed commit, sealed secrets and a Railway staging environment. |

## Exact Railway layout

Create an isolated Railway **staging environment** with two services from the same reviewed Git commit:

1. `web` — assign the only public Railway domain. Set custom config path `deploy/railway/web.railway.toml`.
2. `api` — **do not generate a public domain**. Set custom config path `deploy/railway/api.railway.toml`, attach one Railway volume at `/app/data` and retain it during redeploys.

Set `BACKEND_ORIGIN=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}` in `web`; Railway documents this private-domain reference pattern. Set a common random secret as `API_INTERNAL_TOKEN` on web and `GHOSTWASTE_API_TOKEN` on API. The browser never receives that API secret: `apps/web/src/app/api/[...path]/route.ts` injects it server-side.

### Required sealed variables

**Web:** `STAGING_AUTH_REQUIRED=true`, `STAGING_AUTH_USER`, `STAGING_AUTH_PASSWORD`, `API_INTERNAL_TOKEN`, `BACKEND_ORIGIN`.

**API:** `GHOSTWASTE_STAGING_MODE=true`, `GHOSTWASTE_DB_PATH=/app/data/ghostwaste.db`, `GHOSTWASTE_AUTO_SCHEMA=false`, `GHOSTWASTE_API_TOKEN`, `GHOSTWASTE_CORS_ORIGINS=https://<web-domain>`, `GHOSTWASTE_ALLOWED_HOSTS=api.railway.internal,healthcheck.railway.app`, `GHOSTWASTE_ENABLE_DOCS=false`.

Never commit values; Railway sealed variables are the source of truth. Before traffic, run reviewed Alembic migrations against the empty staging volume from a controlled administrative command. Do not copy the local demo database.

## Public security limits

This is guarded staging, not a multi-user production authorization system. HTTP Basic Auth must be used only over Railway HTTPS. Basic credentials are shared staging access, there are no user roles, API rate limits, WAF, session revocation, managed secrets rotation, or production observability. API docs are disabled in staging. Never give the API a public domain; doing so bypasses the web access boundary.

## Local production rehearsal

Built images:

```text
docker build -t ghostwaste-api:staging-check -f Dockerfile.api .
docker build -t ghostwaste-web:staging-check -f Dockerfile.web .
```

Temporary stack checks:

- `GET /ready` on API → `200 {"status":"ready"}`.
- unauthenticated public web root → `401`.
- authenticated web `/api/health` → `200`, proving proxy-to-token-protected API flow.
- synthetic demo loaded only into `/private/tmp/ghostwaste-staging-check/staging.sqlite3`.
- API restarted; authenticated proxied dashboard returned `"ingredients":4`.
- named temporary containers/network were removed afterward. A first immediate post-restart proxy request reset before readiness; retrying only after `/ready` succeeds resolved it. This demonstrates the need to use Railway health checks during deployment.

## Provider and cost research

As checked on 2026-11-09, Railway’s published pricing says the free trial grants $5 for 30 days; its Free tier has 0.5 GB volume storage after trial, and Hobby has a $5/month minimum including $5 usage with storage up to 5 GB. Current published resource pricing lists RAM $10/GB/month, CPU $20/vCPU/month, volume storage $0.15/GB/month, and egress $0.05/GB. Actual cost depends on runtime/resource settings and must be confirmed in the account before provisioning. Official sources: [Railway pricing](https://railway.com/pricing), [pricing documentation](https://docs.railway.com/pricing), [volumes](https://docs.railway.com/volumes), [private domains](https://docs.railway.com/networking/domains/working-with-domains).

## Rollback and recovery

1. In Railway, redeploy the previous known-good commit to both services; do not detach/delete the API volume.
2. Confirm web auth returns `401` without credentials, then `/api/health` and API `/ready` return healthy through the authenticated web service.
3. If data is implicated, stop writes, create/download a Railway volume backup, restore into a **new staging environment**, validate it, and only then decide whether an operator-approved restore is warranted. Do not overwrite a live volume during diagnosis.

## Hosted verification plan after authorization

Use a fresh synthetic namespace in staging, not real restaurant records. Run protected browser checks for all 13 workspaces, full restaurant workflow, approval/rejection/audit, scenario consistency, restart persistence, network/console status capture, and 390/768/1024/1280/1440/1600 screenshots. Record the actual HTTPS URL and deployment logs here only after verification.

## Approval gate

Required before provisioning/deploying: Railway account/project access, a reviewed Git commit or branch, permission to create a staging project/services/volume/domain, accepted estimated costs, sealed credentials, and explicit authorization to publish/deploy. None were supplied; no hosted resource was created.
