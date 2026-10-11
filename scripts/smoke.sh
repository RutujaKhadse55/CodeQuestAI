#!/usr/bin/env bash
# Appendix B. Each role adds its own steps under scripts/smoke.d/*.sh (sourced in order).
set -e
B=${B:-http://localhost:8000}
API_TOKEN=${API_TOKEN:-change-me}
H="X-API-Token: $API_TOKEN"
J='content-type: application/json'
curl -sf -H "$H" "$B/health" >/dev/null
for f in "$(dirname "$0")"/smoke.d/*.sh; do [ -f "$f" ] && source "$f"; done
echo SMOKE_OK
