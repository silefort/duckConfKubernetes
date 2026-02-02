#!/bin/bash
# setup-tmux.sh — Session tmux : 1 pane par container + 2 panes de commandes
# Usage : ./setup-tmux.sh [VERSION]    ou    make VERSION=2 tmux
set -e

VERSION=${1:-${VERSION:-2}}
DOCKER=${DOCKER:-podman}
PREFIX="version-${VERSION}"
CWD="$(cd "$(dirname "$0")" && pwd)"

# --- Services par version (ordre : control plane puis nodes) ---
case $VERSION in
    0) SERVICES=("app-manager"     "node-1" "node-2" "node-3") ;;
    1) SERVICES=("app-controller"  "node-1" "node-2" "node-3") ;;
    2) SERVICES=("node-1" "node-2" "node-3" "scheduler" "api-server" "node-controller") ;;
    *) echo "VERSION non supportée : $VERSION (0 | 1 | 2)"; exit 1 ;;
esac

NUM=${#SERVICES[@]}

# --- Vérifie que les containers sont en cours ---
MISSING=()
for svc in "${SERVICES[@]}"; do
    STATUS=$($DOCKER inspect --format "{{.State.Status}}" "${PREFIX}_${svc}_1" 2>/dev/null || echo "absent")
    [[ "$STATUS" == "running" || "$STATUS" == "paused" ]] || MISSING+=("$svc")
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "Containers manquants : ${MISSING[*]}"
    echo "Lancez d'abord :  make VERSION=$VERSION cluster_start"
    exit 1
fi

# --- Grille : 2 colonnes si ≤4 services, 3 sinon ---
[[ $NUM -le 4 ]] && COLS=2 || COLS=3

# --- Base-index tmux (par défaut 0, mais souvent 1 en config perso) ---
BASE=$(tmux show-options -gv base-index)

# --- Contexte : déjà dans tmux ou non ---
if [[ -n "$TMUX" ]]; then
    SESSION=$(tmux display-message -p '#{session_name}')
    LOGS_WIN="v${VERSION}-logs"
    CMDS_WIN="v${VERSION}-cmds"
    # Nettoyer les fenêtres d'une exécution précédente
    tmux kill-window -t "$SESSION:$LOGS_WIN" 2>/dev/null || true
    tmux kill-window -t "$SESSION:$CMDS_WIN" 2>/dev/null || true
    # Créer la fenêtre logs avec le premier container
    tmux new-window -t "$SESSION" -n "$LOGS_WIN" \
        -- bash -c "printf '\\033]2;${SERVICES[0]}\\007'; exec $DOCKER logs -f '${PREFIX}_${SERVICES[0]}_1'"
else
    SESSION="duckconf-v${VERSION}"
    LOGS_WIN="logs"
    CMDS_WIN="cmds"
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    tmux new-session -d -s "$SESSION" -n "$LOGS_WIN" -x 240 -y 60 \
        -- bash -c "printf '\\033]2;${SERVICES[0]}\\007'; exec $DOCKER logs -f '${PREFIX}_${SERVICES[0]}_1'"
fi

# === Grille logs : première ligne (splits horizontaux, tailles égales) ===
for ((c = 1; c < COLS && c < NUM; c++)); do
    PERCENT=$(( 100 * (COLS - c) / (COLS - c + 1) ))
    tmux split-window -h -l ${PERCENT}% -t "$SESSION:$LOGS_WIN.$(( c - 1 + BASE ))" \
        -- bash -c "printf '\\033]2;${SERVICES[$c]}\\007'; exec $DOCKER logs -f '${PREFIX}_${SERVICES[$c]}_1'"
done

# === Grille logs : deuxième ligne (splits verticaux par colonne) ===
# On split chaque pane de la première ligne vers le bas.
for ((c = 0; c < COLS && c + COLS < NUM; c++)); do
    tmux split-window -v -t "$SESSION:$LOGS_WIN.$(( c + BASE ))" \
        -- bash -c "printf '\\033]2;${SERVICES[$((c + COLS))]}\\007'; exec $DOCKER logs -f '${PREFIX}_${SERVICES[$((c + COLS))]}_1'"
done

# --- Bordure des panes avec titre du service ---
tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format ' #{pane_title} '

# === Fenêtre cmds : 2 panes libres dans le bon répertoire ===
tmux new-window -t "$SESSION" -n "$CMDS_WIN" \
    -- bash -c "cd $CWD && export VERSION=$VERSION && exec bash"
tmux split-window -h -t "$SESSION:$CMDS_WIN" \
    -- bash -c "cd $CWD && export VERSION=$VERSION && exec bash"

# === Retour sur logs ===
tmux select-window -t "$SESSION:$LOGS_WIN"
[[ -z "$TMUX" ]] && tmux attach-session -t "$SESSION" || true
