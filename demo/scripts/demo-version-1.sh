#!/bin/bash
# Demo script for version-1 - lancé par asciinema rec

SESSION="demo-v1"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

tmux kill-session -t "$SESSION" 2>/dev/null || true
tmux new-session -d -s "$SESSION" -c "$DIR"

tmux send-keys -t "$SESSION" "bash setup-tmux.sh 1 demo && exit" Enter

for i in $(seq 1 20); do
    tmux list-windows -t "$SESSION" 2>/dev/null | grep -q "version-1" && break
    sleep 0.5
done

exec tmux attach -t "$SESSION":version-1
