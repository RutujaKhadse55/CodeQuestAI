#!/usr/bin/env bash
# Appendix B. Each role adds its own steps under scripts/smoke.d/*.sh
set -e
B=${B:-http://localhost:8000}
curl -sf "$B/health"
for f in "$(dirname "$0")"/smoke.d/*.sh; do [ -f "$f" ] && source "$f"; done
echo SMOKE_OK
