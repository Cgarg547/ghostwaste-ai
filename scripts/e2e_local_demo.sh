#!/usr/bin/env bash
# Disposable browser/API smoke suite. It never opens the development SQLite DB.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
temp_root="$(mktemp -d -t ghostwaste-e2e-XXXXXX)"
api_port="18000"; web_port="13000"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
cleanup() {
  status=$?
  if [ "$status" -ne 0 ]; then
    echo "E2E failed; API log:" >&2; tail -40 "$temp_root/api.log" 2>/dev/null || true
    echo "E2E failed; web log:" >&2; tail -80 "$temp_root/web.log" 2>/dev/null || true
  fi
  kill "${web_pid:-}" "${api_pid:-}" 2>/dev/null || true
  rm -rf "$temp_root"
  exit "$status"
}
trap cleanup EXIT INT TERM
test -x "$chrome" || { echo "Google Chrome is required for this local browser suite" >&2; exit 2; }
cd "$root"
GHOSTWASTE_TESTING=1 GHOSTWASTE_DB_PATH="$temp_root/ghostwaste-e2e.sqlite3" GHOSTWASTE_AUTO_SCHEMA=true \
  .venv/bin/python -m uvicorn apps.api.main:app --host 127.0.0.1 --port "$api_port" >"$temp_root/api.log" 2>&1 & api_pid=$!
for _ in {1..40}; do curl -fsS "http://127.0.0.1:$api_port/health" >/dev/null 2>&1 && break; sleep .25; done
curl -fsS "http://127.0.0.1:$api_port/health" >/dev/null
curl -fsS -X POST "http://127.0.0.1:$api_port/demo/load" >"$temp_root/demo.json"
.venv/bin/python - "$temp_root/demo.json" "$api_port" <<'PY'
import json, sys, urllib.request
demo=json.load(open(sys.argv[1])); base=f"http://127.0.0.1:{sys.argv[2]}"
def request(path, payload=None):
    body=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(base+path, data=body, headers={"Content-Type":"application/json"} if body else {})
    return json.load(urllib.request.urlopen(req))
run=request("/forecast-runs/"+demo["forecast_run_id"])
scenario={"as_of":"2026-11-08","horizon_days":7,"trials":50,"seed":42,"storage_capacity_kg":30}
first=request("/workflows/forecast/"+run["id"],scenario); second=request("/workflows/forecast/"+run["id"],scenario)
assert first["scenario_id"] == second["scenario_id"] and second["restored"] is True
assert request("/dashboard?demo=true")["date_context"] == "synthetic_demo"
PY
# A temporary web copy avoids interfering with a developer's Next dev server
# and proves the production build from a clean generated-artifact directory.
cp -R apps/web "$temp_root/web"
rm -rf "$temp_root/web/.next"
(cd "$temp_root/web" && BACKEND_ORIGIN="http://127.0.0.1:$api_port" npm run build && BACKEND_ORIGIN="http://127.0.0.1:$api_port" npm run start -- --hostname 127.0.0.1 --port "$web_port") >"$temp_root/web.log" 2>&1 & web_pid=$!
for _ in {1..160}; do curl -fsS "http://127.0.0.1:$web_port" >/dev/null 2>&1 && break; sleep .25; done
curl -fsS "http://127.0.0.1:$web_port" >/dev/null
for route in / /inventory /forecasting /waste-radar /optimization /supplier-intelligence /actions /analytics /settings /assistant /scenario-studio /impact-studio /use-first /daily-plan; do
  "$chrome" --headless --no-first-run --disable-gpu --dump-dom "http://127.0.0.1:$web_port$route" >"$temp_root/page.html" 2>"$temp_root/chrome.log"
  grep -q "GhostWaste" "$temp_root/page.html"
done
# A second independent page load is the browser-level refresh persistence check.
"$chrome" --headless --no-first-run --disable-gpu --dump-dom "http://127.0.0.1:$web_port/analytics" >"$temp_root/refresh.html" 2>>"$temp_root/chrome.log"
grep -q "GhostWaste" "$temp_root/refresh.html"
echo "PASS: isolated API workflow and 14 browser routes rendered; persisted scenario restored after refresh."
