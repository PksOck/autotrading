#!/usr/bin/env bash
# Collect one deep analysis run for review (BL-092): the run as JSON plus agent and
# LiteLLM logs, packed into one archive you can attach to the Claude session.
# Usage (from the repo root or anywhere): infra/scripts/collect-analysis.sh [run-id]
# Without a run id it takes the newest run. WEB_URL overrides http://127.0.0.1:3000.
set -euo pipefail
cd "$(dirname "$0")/.."

WEB=${WEB_URL:-http://127.0.0.1:3000}
ID=${1:-$(curl -fsS "$WEB/api/analyses?limit=1" | python3 -c 'import json, sys; print(json.load(sys.stdin)[0]["id"])')}
OUT="analysis-$ID"
mkdir -p "$OUT"

curl -fsS "$WEB/api/analyses/$ID" > "$OUT/run.json"
compose() { docker compose --env-file ../.env "$@"; }
compose logs --no-color --since 12h agents > "$OUT/agents.log" 2>&1 || true
# Drop anything that looks like a key before it leaves the server.
compose logs --no-color --since 12h litellm 2>&1 \
  | grep -viE 'authorization|api[_-]?key|bearer|sk-[a-z0-9]' > "$OUT/litellm.log" || true

tar czf "$OUT.tar.gz" "$OUT"
rm -rf "$OUT"
echo "Ready: infra/$OUT.tar.gz"
