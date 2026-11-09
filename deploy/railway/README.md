# Railway staging configuration

Create two services from the same repository. Set each service's **custom config path** to the corresponding file in this directory. Attach a Railway volume only to `api` at `/app/data`; do not create a public API domain.

`web` is the only public service. Its server-side route handler forwards `/api/*` to `BACKEND_ORIGIN=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}` and adds `API_INTERNAL_TOKEN`. Set `STAGING_AUTH_REQUIRED=true`, `STAGING_AUTH_USER`, and a long random `STAGING_AUTH_PASSWORD` as sealed Railway variables.

For `api`, set `GHOSTWASTE_DB_PATH=/app/data/ghostwaste.db`, `GHOSTWASTE_AUTO_SCHEMA=false`, `GHOSTWASTE_API_TOKEN` equal to the web's internal token, `GHOSTWASTE_CORS_ORIGINS=https://<web-public-domain>`, `GHOSTWASTE_ALLOWED_HOSTS=api.railway.internal,healthcheck.railway.app`, and `GHOSTWASTE_ENABLE_DOCS=false`. Apply Alembic migrations manually against an empty staging volume before enabling public traffic; do not set up an API public domain.
