#!/bin/bash
VERSION=${1:-0}
DEMO=${2:-}
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# === Fonctions pour le mode démo scriptée ===
TYPING_SPEED=0.05

# Tape un texte caractère par caractère dans un pane tmux
type_in_pane() {
    local target="$1" text="$2"
    for ((i=0; i<${#text}; i++)); do
        tmux send-keys -t "$target" "${text:$i:1}" ""
        sleep "$TYPING_SPEED"
    done
}

# Tape et exécute une commande dans un pane (avec pause après)
run_step() {
    local target="$1" cmd="$2" pause="${3:-8}"
    type_in_pane "$target" "$cmd"
    tmux send-keys -t "$target" "" C-m
    sleep "$pause"
}

# Affiche un commentaire pédagogique instantanément
show_note() {
    local target="$1" text="$2" pause="${3:-3}"
    tmux send-keys -t "$target" "echo '# $text'" C-m
    sleep "$pause"
}
# === Fin des fonctions démo ===

case "$VERSION" in
  0)
    # ┌─────────────────────┬─────────────────────┐
    # │  [1] logs           │  [2] watch          │
    # │  app-manager        │  apps en cours      │
    # ├─────────────────────┴─────────────────────┤
    # │  [3] commandes                            │
    # └───────────────────────────────────────────┘
    WIN=$(tmux new-window -n "version-0" -P -F "#{window_index}")

    # Découpage : haut (70%) / bas (30% - commandes)
    tmux split-window -v -l '20%' -t "${WIN}.1"
    # pane 1 = haut, pane 2 = bas (commandes)

    # Découper le haut en deux (logs | watch)
    tmux split-window -h -t "${WIN}.1"

    # Démarrer les logs à gauche
    tmux send-keys -t "${WIN}.1" "cd $DIR && make delete_all && make cluster_restart VERSION=0 && make logs SERVICE=app-manager VERSION=0" C-m
    tmux send-keys -t "${WIN}.1" "cd $DIR && make logs SERVICE=app-manager VERSION=0" C-m
    # Démarrer le watch à droite
    tmux send-keys -t "${WIN}.2" "cd $DIR && make watch VERSION=0" C-m

    tmux select-pane -t "${WIN}.3"
    tmux send-keys -t "${WIN}.3" "cd $DIR && export VERSION=0 && clear" C-m

    if [ -n "$DEMO" ]; then
        sleep 18
        show_note "${WIN}.3" "Version 0"
        run_step "${WIN}.3" "make app_start NAME=duck-1 IMAGE=nginx:alpine VERSION=0"
        run_step "${WIN}.3" "make app_start NAME=duck-2 IMAGE=nginx:alpine VERSION=0"
        run_step "${WIN}.3" "make app_start NAME=duck-3 IMAGE=nginx:alpine VERSION=0"
        show_note "${WIN}.3" "Les 3 apps tournent sur node-1 ✓" 5
        show_note "${WIN}.3" "Que se passe-t-il si l'application duck-1 crashe ?" 3
        run_step "${WIN}.3" "make app_crash NAME=duck-1 VERSION=0" 5
        show_note "${WIN}.3" "duck-1 disparu et ne revient pas ✗" 5
        show_note "${WIN}.3" "Pas de boucle de contrôle = pas de résilience" 5
    fi
    ;;

  1)
    # ┌─────────────────────┬─────────────────────┐
    # │  [1] logs           │  [2] watch          │
    # │  app-controller     │  état désiré +      │
    # │                     │  apps en cours      │
    # ├─────────────────────┴─────────────────────┤
    # │  [3] commandes                            │
    # └───────────────────────────────────────────┘
    WIN=$(tmux new-window -n "version-1" -P -F "#{window_index}")

    # Découpage : haut (70%) / bas (30% - commandes)
    tmux split-window -v -l '20%' -t "${WIN}.1"
    # Découper le haut en deux (logs | watch)
    tmux split-window -h -t "${WIN}.1"

    tmux send-keys -t "${WIN}.1" "cd $DIR && make delete_all && make cluster_restart VERSION=1 && make logs SERVICE=app-manager VERSION=1" C-m
    tmux send-keys -t "${WIN}.1" "cd $DIR && make logs SERVICE=app-controller VERSION=1" C-m
    tmux send-keys -t "${WIN}.2" "cd $DIR && make watch VERSION=1" C-m

    tmux select-pane -t "${WIN}.3"
    tmux send-keys -t "${WIN}.3" "cd $DIR && export VERSION=1 && clear" C-m

    if [ -n "$DEMO" ]; then
        sleep 18
        show_note "${WIN}.3" "Version 1 : mode déclaratif + boucle de contrôle"
        run_step "${WIN}.3" "make app_apply NAME=duck-1 IMAGE=nginx:alpine VERSION=1"
        run_step "${WIN}.3" "make app_apply NAME=duck-2 IMAGE=nginx:alpine VERSION=1"
        run_step "${WIN}.3" "make app_apply NAME=duck-3 IMAGE=nginx:alpine VERSION=1"
        show_note "${WIN}.3" "L'app-controller a schedulé les apps ✓" 5
        show_note "${WIN}.3" "Que se passe-t-il si duck-1 crashe ?" 3
        run_step "${WIN}.3" "make app_crash NAME=duck-1 VERSION=1" 12
        show_note "${WIN}.3" "L'app-controller a relancé duck-1 ✓" 5
        show_note "${WIN}.3" "Boucle de contrôle : détecte la divergence et corrige" 5
    fi
    ;;

  2)
    # ┌─────────────────┬───────────────────────┐
    # │  [1]            │  [3] watch            │
    # │node-binder      │                       │
    # │node-ctrl        │                       │
    # ├─────────────────┤                       │
    # │  [2]            │                       │
    # │ node-1          │                       │
    # └─────────────────┴───────────────────────┘
    # │  [4] commandes                          │
    # └─────────────────────────────────────────┘
    WIN=$(tmux new-window -n "version-2" -P -F "#{window_index}")

    # Découpage : haut (70%) / bas (30% - commandes)
    tmux split-window -v -l '20%' -t "${WIN}.1"
    # Découper le haut en deux (logs | watch)
    tmux split-window -h -l '40%' -t "${WIN}.1"
    # Découper le pane de gauche en 2
    tmux split-window -v -t "${WIN}.1"

    tmux send-keys -t "${WIN}.1" "cd $DIR && make delete_all && make cluster_restart VERSION=2 && make logs SERVICE=node-binder,node-controller VERSION=2" C-m
    tmux send-keys -t "${WIN}.2" "cd $DIR && sleep 10 && make logs SERVICE=node-1 VERSION=2" C-m
    tmux send-keys -t "${WIN}.3" "cd $DIR && make watch VERSION=2" C-m

    tmux select-pane -t "${WIN}.4"
    tmux send-keys -t "${WIN}.4" "cd $DIR && export VERSION=2 && clear" C-m

    if [ -n "$DEMO" ]; then
        sleep 22
        show_note "${WIN}.4" "Version 2 : contrôle distribué avec heartbeats"
        run_step "${WIN}.4" "make app_apply NAME=duck-1 IMAGE=nginx:alpine VERSION=2"
        run_step "${WIN}.4" "make app_apply NAME=duck-2 IMAGE=nginx:alpine VERSION=2"
        run_step "${WIN}.4" "make app_apply NAME=duck-3 IMAGE=nginx:alpine VERSION=2"
        show_note "${WIN}.4" "Le node-binder a distribué les apps sur les noeuds ✓" 5
        show_note "${WIN}.4" "Simulation de panne : node-1 s'arrête" 3
        run_step "${WIN}.4" "make node_stop NODE=node-1 VERSION=2" 28
        show_note "${WIN}.4" "node-controller a détecté la panne ✓" 3
        show_note "${WIN}.4" "node-binder a redistribué les apps de node-1 ✓" 5
        run_step "${WIN}.4" "make node_start NODE=node-1 VERSION=2" 12
        show_note "${WIN}.4" "node-1 est de retour - le cluster se rééquilibre" 5
    fi
    ;;

  *)
    echo "Usage: $0 <VERSION> [demo]"
    echo "Versions disponibles: 0, 1, 2"
    echo "Passer 'demo' en second argument pour le mode démo scriptée"
    exit 1
    ;;
esac
