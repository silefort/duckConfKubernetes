#!/bin/bash
# Demo script for version-0 - lancé par asciinema rec

SESSION="demo-v0"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Tuer la session existante si elle existe
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Créer une session tmux détachée (fenêtre 0 = bootstrap)
tmux new-session -d -s "$SESSION" -c "$DIR"

# Lancer setup-tmux.sh depuis l'intérieur de la session
# (setup-tmux.sh crée la fenêtre "version-0" via tmux new-window)
tmux send-keys -t "$SESSION" "bash setup-tmux.sh 0 && exit" Enter

# Attendre que la fenêtre "version-0" soit créée
for i in $(seq 1 20); do
    tmux list-windows -t "$SESSION" 2>/dev/null | grep -q "version-0" && break
    sleep 0.5
done

# S'attacher à la fenêtre de démo (la fenêtre 0 bootstrap se fermera seule via exit)
exec tmux attach -t "$SESSION":version-0
