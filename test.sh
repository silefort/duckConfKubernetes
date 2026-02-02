#!/bin/bash
# test.sh — Tests de régression pour le simulateur Kubernetes
# Usage: ./test.sh [0|1|2|all]

set -o pipefail

DOCKER=${DOCKER:-podman}
DOCKER_COMPOSE=${DOCKER_COMPOSE:-podman-compose}
PASSED=0
FAILED=0
ERRORS=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

pass()    { echo -e "  ${GREEN}✓ $1${NC}"; ((PASSED++)); }
fail()    { echo -e "  ${RED}✗ $1${NC}"; ((FAILED++)); ERRORS="${ERRORS}\n  - [$CUR_VERSION] $1"; }
info()    { echo -e "  ${YELLOW}→ $1${NC}"; }
section() { echo -e "\n${BLUE}══ $1 ══${NC}"; }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
compose() {
    local v=$1; shift
    $DOCKER_COMPOSE -f version-$v/docker-compose.yml -p version-$v "$@" 2>/dev/null
}

wait_for_api() {
    info "Attente de l'API..."
    for i in $(seq 1 30); do
        local code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null)
        [ "$code" != "000" ] && return 0
        sleep 2
    done
    return 1
}

wait_for_app() {
    local name=$1 timeout=${2:-25}
    for i in $(seq 1 $timeout); do
        $DOCKER ps --filter "label=type=app" --format "{{.Names}}" 2>/dev/null | grep -q "^${name}$" && return 0
        sleep 1
    done
    return 1
}

wait_for_app_gone() {
    local name=$1 timeout=${2:-15}
    for i in $(seq 1 $timeout); do
        $DOCKER ps --filter "label=type=app" --format "{{.Names}}" 2>/dev/null | grep -q "^${name}$" || return 0
        sleep 1
    done
    return 1
}

get_app_node() {
    $DOCKER ps --filter "label=type=app" --filter "name=^$1$" --format "{{.Labels.node}}" 2>/dev/null
}

cleanup() {
    local v=$1
    info "Nettoyage..."
    $DOCKER rm -f $($DOCKER ps -aq --filter "label=type=app") 2>/dev/null
    rm -f version-$v/.paused_*
    compose $v down -t 0
}

# ---------------------------------------------------------------------------
# VERSION 0 — Mode imperatif
# ---------------------------------------------------------------------------
test_version_0() {
    CUR_VERSION="version-0"
    section "VERSION 0 — Mode imperatif"
    cleanup 0

    compose 0 up -d
    wait_for_api || { fail "API non disponible"; cleanup 0; return; }
    pass "Cluster démarré"

    # Ajout d'une app via POST /app/start
    info "Ajout d'une application..."
    RESP=$(curl -s -X POST http://localhost:8080/app/start \
        -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}')
    APP=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['app'])" 2>/dev/null)
    NODE=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['node'])" 2>/dev/null)
    [ -n "$APP" ] && pass "App créée: $APP sur $NODE" || { fail "Création échouée: $RESP"; cleanup 0; return; }

    wait_for_app "$APP" 10 && pass "App $APP en cours d'exécution" || fail "App $APP non trouvée"

    # Arrêt du noeud où tourne l'app
    info "Arrêt du noeud $NODE..."
    make VERSION=0 node_stop $NODE >/dev/null 2>&1
    wait_for_app_gone "$APP" 5 && pass "App disparue après node_stop" || fail "App encore présente après node_stop"

    # Redémarrage du noeud — pas de boucle de contrôle, l'app ne revient pas
    info "Redémarrage du noeud $NODE..."
    make VERSION=0 node_start $NODE >/dev/null 2>&1
    sleep 3
    ! wait_for_app "$APP" 3 && pass "App ne revient pas (attendu : pas de boucle de contrôle)" || fail "App revenue inattenduement"

    cleanup 0
}

# ---------------------------------------------------------------------------
# VERSION 1 — Boucle de contrôle centralisée
# ---------------------------------------------------------------------------
test_version_1() {
    CUR_VERSION="version-1"
    section "VERSION 1 — Boucle de contrôle"
    cleanup 1

    compose 1 up -d
    wait_for_api || { fail "API non disponible"; cleanup 1; return; }
    pass "Cluster démarré"

    # Déclaration d'une app via PUT /app/<name>
    APP="test-v1"
    info "Déclaration de $APP..."
    RESP=$(curl -s -X PUT http://localhost:8080/app/$APP \
        -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}')
    echo "$RESP" | grep -q "$APP" && pass "App $APP déclarée" || { fail "Déclaration échouée: $RESP"; cleanup 1; return; }

    # La boucle de contrôle doit démarrer l'app (loop à 10s)
    wait_for_app "$APP" 25 && pass "App démarrée par la boucle de contrôle" || { fail "App non démarrée après 25s"; cleanup 1; return; }

    # Idempotence : second PUT, toujours un seul container
    info "Test idempotence..."
    curl -s -X PUT http://localhost:8080/app/$APP \
        -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}' >/dev/null
    sleep 2
    COUNT=$($DOCKER ps --filter "label=type=app" --filter "name=^${APP}$" --format "{{.Names}}" | wc -l)
    [ "$COUNT" -eq 1 ] && pass "Idempotence OK (1 container après 2 PUT)" || fail "Idempotence : $COUNT containers"

    # Arrêt du noeud où tourne l'app
    NODE=$(get_app_node "$APP")
    info "Arrêt du noeud $NODE..."
    make VERSION=1 node_stop $NODE >/dev/null 2>&1
    wait_for_app_gone "$APP" 5 && pass "App disparue après node_stop" || fail "App encore présente après node_stop"

    # Redémarrage — la boucle de contrôle détecte l'écart et relance
    info "Redémarrage du noeud $NODE..."
    make VERSION=1 node_start $NODE >/dev/null 2>&1
    wait_for_app "$APP" 25 && pass "App relancée par la boucle de contrôle" || fail "App non relancée après 25s"

    cleanup 1
}

# ---------------------------------------------------------------------------
# VERSION 2 — Scheduleur + contrôleurs distribuées
# ---------------------------------------------------------------------------
test_version_2() {
    CUR_VERSION="version-2"
    section "VERSION 2 — Scheduleur + contrôleurs"
    cleanup 2

    compose 2 up -d
    wait_for_api || { fail "API non disponible"; cleanup 2; return; }
    pass "Cluster démarré"

    # Déclaration d'une app via PUT /app/<name>
    APP="test-v2"
    info "Déclaration de $APP..."
    RESP=$(curl -s -X PUT http://localhost:8080/app/$APP \
        -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}')
    echo "$RESP" | grep -q "$APP" && pass "App $APP déclarée" || { fail "Déclaration échouée: $RESP"; cleanup 2; return; }

    # Scheduler (10s) + app_controller (10s) = jusqu'à 20s
    wait_for_app "$APP" 25 && pass "App schedulée et démarrée" || { fail "App non démarrée après 25s"; cleanup 2; return; }

    # Idempotence
    info "Test idempotence..."
    curl -s -X PUT http://localhost:8080/app/$APP \
        -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}' >/dev/null
    sleep 12
    COUNT=$($DOCKER ps --filter "label=type=app" --filter "name=^${APP}$" --format "{{.Names}}" | wc -l)
    [ "$COUNT" -eq 1 ] && pass "Idempotence OK (1 container après 2 PUT)" || fail "Idempotence : $COUNT containers"

    # Distribution : 3 apps sur plusieurs noeuds
    info "Test distribution sur les noeuds..."
    for i in 1 2 3; do
        curl -s -X PUT http://localhost:8080/app/dist-$i \
            -H "Content-Type: application/json" -d '{"image": "nginx:alpine"}' >/dev/null
    done
    sleep 25
    UNIQUE_NODES=$($DOCKER ps --filter "label=type=app" --format "{{.Labels.node}}" | sort -u | grep -v "^$" | wc -l)
    [ "$UNIQUE_NODES" -gt 1 ] && pass "Apps distribuées sur $UNIQUE_NODES noeuds" || fail "Toutes les apps sur 1 seul noeud"

    # Arrêt d'un noeud — apps dessus disparaissent
    NODE=$(get_app_node "$APP")
    info "Arrêt du noeud $NODE..."
    make VERSION=2 node_stop $NODE >/dev/null 2>&1
    wait_for_app_gone "$APP" 5 && pass "App disparue après node_stop" || fail "App encore présente après node_stop"

    # Redémarrage du noeud, puis attente du reschedule complet
    # (node_controller : heartbeat timeout 20s + loop 10s, scheduler : 10s, app_controller : 10s)
    info "Redémarrage du noeud $NODE..."
    make VERSION=2 node_start $NODE >/dev/null 2>&1
    wait_for_app "$APP" 55 && pass "App revenue après reschedule" || fail "App non revenue après 55s"

    cleanup 2
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
TARGET=${1:-all}

echo -e "\n${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DuckConf Kubernetes — Tests de régression   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

case $TARGET in
    0)   test_version_0 ;;
    1)   test_version_1 ;;
    2)   test_version_2 ;;
    all) test_version_0; test_version_1; test_version_2 ;;
    *)   echo "Usage: $0 [0|1|2|all]"; exit 1 ;;
esac

# Résumé
section "RÉSULTAT"
echo -e "  ${GREEN}Passés:  $PASSED${NC}"
echo -e "  ${RED}Échoués: $FAILED${NC}"
[ -n "$ERRORS" ] && echo -e "\n  Détails:${ERRORS}"
echo
[ $FAILED -eq 0 ]
