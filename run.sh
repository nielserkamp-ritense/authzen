#!/usr/bin/env bash
#
# Starts the AuthZEN + GZAC + OpenFTV demo stack.
# No named volumes are used: `--down` (or `--reset`) removes all demo state.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

COMPOSE=(docker compose --project-directory docker -f docker/docker-compose.yaml --profile gzac)

usage() {
    cat <<EOF
Usage: ./run.sh [option]

  (no option)    Build and start the stack in the foreground. Existing containers are reused, so state is kept.
  -d, --detach   Build and start the stack in the background.
  --stop         Stop the stack. Containers and data are kept; ./run.sh resumes.
  --down         Remove containers, networks and volumes. Nothing persists.
  --reset        Same as --down, then start the stack fresh (combine with -d to detach).
  -h, --help     Show this help.
EOF
}

fail() {
    echo "Error: $*" >&2
    exit 1
}

check_prerequisites() {
    command -v docker >/dev/null 2>&1 || fail "docker is not installed or not on PATH."
    docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 ('docker compose') is not available."
    docker info >/dev/null 2>&1 || fail "the Docker daemon is not running or not reachable."
    [[ -f valtimo/settings.gradle && -f open-ftv/apps/pdp/Dockerfile ]] \
        || fail "submodules are not initialised. Run: git submodule update --init"
}

print_urls() {
    cat <<EOF

Demo stack started in the background. Main URLs:
  GZAC frontend          http://localhost
  GZAC backend           http://localhost:8080
  GZAC Keycloak          http://localhost:8081/auth
  OpenFTV management UI  http://localhost:8180
  OpenFTV Keycloak       http://localhost:8088
  Open Zaak              http://localhost:8001

The backend needs a minute or two to start. Follow it with:
  docker compose -f docker/docker-compose.yaml --profile gzac logs -f gzac-backend
EOF
}

detach=false
reset=false
action=up

while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--detach) detach=true ;;
        --reset) reset=true ;;
        --stop) action=stop ;;
        --down) action=down ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

check_prerequisites

case "$action" in
    stop)
        "${COMPOSE[@]}" stop
        ;;
    down)
        "${COMPOSE[@]}" down -v --remove-orphans
        ;;
    up)
        if $reset; then
            "${COMPOSE[@]}" down -v --remove-orphans
        fi
        if $detach; then
            "${COMPOSE[@]}" up --build -d
            print_urls
        else
            "${COMPOSE[@]}" up --build
        fi
        ;;
esac
