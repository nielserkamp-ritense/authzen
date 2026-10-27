#!/usr/bin/env bash
# Prepares the demo: a fresh stack (unless --no-reset), the demo data, and a check that every user sees
# what docs/demo-script.md says they will. Run it shortly before presenting; it takes a few minutes.
#
# Usage: scripts/demo-prepare.sh [--no-reset]
set -euo pipefail

cd "$(dirname "$0")/.."
start=$SECONDS

case "${1:-}" in
    --no-reset) ;;
    "") ./run.sh --reset -d ;;
    *) echo "Usage: scripts/demo-prepare.sh [--no-reset]" >&2; exit 2 ;;
esac

scripts/demo-seed.py

cat <<'EOF'

=== before you start
  GZAC                   http://localhost              password = username for every demo user
  OpenFTV management UI  http://localhost:8180         author-user / password (edits and publishes)

  Open one private window (or browser profile) per user and log in beforehand:
    klachten-behandelaar-szw, klachten-kcc, bezwaar-behandelaar, bezwaar-adviseur, todo-anna, todo-bram
  and one for the management UI as author-user. Then follow docs/demo-script.md.

  Just before presenting:  scripts/demo-seed.py --check
  After the demo:          ./run.sh --reload-policies   (undoes the live policy change)
EOF
echo "  Prepared in $(( (SECONDS - start) / 60 )) min $(( (SECONDS - start) % 60 )) s."
