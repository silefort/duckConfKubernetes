#!/bin/bash

# Lire NODE_NAME depuis le fichier si la variable n'est pas définie
if [ -z "$NODE_NAME" ] && [ -f /etc/node_name ]; then
  NODE_NAME=$(cat /etc/node_name)
fi

if [ "$1" = "ps" ]; then
  /usr/local/bin/docker.orig ps --filter "label=node=$NODE_NAME" "${@:2}"
elif [ "$1" = "run" ]; then
  /usr/local/bin/docker.orig run --label "node=$NODE_NAME" "${@:2}"
else
  /usr/local/bin/docker.orig "$@"
fi
