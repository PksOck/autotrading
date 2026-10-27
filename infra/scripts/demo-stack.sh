#!/usr/bin/env sh
# Demo stack for e2e and development (BL-162): own project "preza-demo", own database, web on :3100.
#   demo-stack.sh up     build, start and load demo data
#   demo-stack.sh seed   reload demo data (idempotent)
#   demo-stack.sh stop   stop containers, keep the demo database
# e2e: BASE_URL=http://127.0.0.1:3100 pnpm exec playwright test
set -eu
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
DC="docker compose -f docker-compose.demo.yml"

seed() {
  $DC exec -T -e PREZA_DEMO_DB=1 api python -m preza.cli.seed_demo
}

case "${1:-up}" in
  up)
    $DC up -d --build --wait
    seed
    echo "demo: http://127.0.0.1:3100"
    ;;
  seed) seed ;;
  stop) $DC stop ;;
  *)
    echo "usage: $0 [up|seed|stop]" >&2
    exit 2
    ;;
esac
