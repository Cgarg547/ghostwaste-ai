#!/usr/bin/env bash
# Starts FastAPI and Next.js against a uniquely named throwaway SQLite file.
# The DB and screenshots are deliberately retained for post-run verification.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
temp_root="$(mktemp -d -t ghostwaste-e2e-XXXXXX)"
case "$temp_root" in *ghostwaste-e2e-*) ;; *) echo "Unsafe E2E temp path: $temp_root" >&2; exit 2 ;; esac
export GHOSTWASTE_TESTING=1
export GHOSTWASTE_DB_PATH="$temp_root/isolated.sqlite3"
export GHOSTWASTE_AUTO_SCHEMA=true
export GHOSTWASTE_E2E_EVIDENCE_DIR="$temp_root/screenshots"
printf 'Isolated E2E database: %s\n' "$GHOSTWASTE_DB_PATH"
printf 'Browser screenshots: %s\n' "$GHOSTWASTE_E2E_EVIDENCE_DIR"
cd "$root/apps/web"
if [ "$#" -eq 0 ]; then
  # Public-demo coverage intentionally has its own production build and must
  # never run against this local FastAPI/SQLite harness.
  set -- e2e/ghostwaste.spec.ts
fi
npx playwright test --output="$temp_root/playwright-results" "$@"
"$root/.venv/bin/python" - "$GHOSTWASTE_DB_PATH" <<'PY'
import sqlite3, sys
from pathlib import Path
path = Path(sys.argv[1]).resolve()
assert "ghostwaste-e2e-" in str(path.parent), f"Refusing unexpected DB path: {path}"
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
try:
    for table in ("ingredients", "inventory_batches", "recipes", "daily_sales", "forecast_runs", "risk_scenarios", "recommendations", "audit_events"):
        count = connection.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        print(f"persisted {table}: {count}")
finally:
    connection.close()
PY
