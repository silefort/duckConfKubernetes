#!/bin/bash

# Démarrer SSH daemon
/usr/sbin/sshd

# Lancer l'agent Python
python3 /app/node_agent.py
