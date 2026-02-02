#!/usr/bin/env python3
import time
from datetime import datetime
from app.utils.log_helper import create_logger
from app.utils.http_utils import get, put

log = create_logger("node-controller")

API_SERVER = "http://api-server:8080"
HEARTBEAT_TIMEOUT = 20  # secondes — si plus de 20s sans heartbeat, le noeud est considéré down

while True:
    log("======================================================")
    log("NODE CONTROLLER - BOUCLE DE CONTRÔLE")
    log("======================================================")

    # --- 01. CAPTEUR - Récupérer les heartbeats des noeuds sur l'API Server---
    try:
        nodes = get(f"{API_SERVER}/nodes")
    except Exception as e:
        log(f"API server non disponible: {e}")
        nodes = {}
    log(f"01. CAPTEUR : heartbeats = {nodes}")

    # --- 02. CONSIGNE - Implicite, aucune application ne doit être sur un noeud considéré comme "down"---

    
    # --- 03. COMPARATEUR - Identifier les noeuds down ---
    now = datetime.now()
    noeuds_down = []
    for node, timestamp in nodes.items():
        derniere_activite = datetime.fromisoformat(timestamp)
        if (now - derniere_activite).total_seconds() > HEARTBEAT_TIMEOUT:
            noeuds_down.append(node)
    log(f"03. COMPARATEUR : noeuds down = {noeuds_down}")

    # --- 04. ACTIONNEUR - retirer les noeuds aux applications dont le noeud est down ---
    for node in noeuds_down:
        try:
            apps = get(f"{API_SERVER}/apps?nodeName={node}")
        except Exception as e:
            log(f"04. ACTIONNEUR : impossible de récupérer les apps de {node}: {e}")
            continue
        for app in apps:
            try:
                put(f"{API_SERVER}/app/{app}", {"node": ""})
                log(f"04. ACTIONNEUR : {app} unschedulée (noeud {node} down)")
            except Exception as e:
                log(f"04. ACTIONNEUR : impossible de unschuler {app}: {e}")

    print()
    time.sleep(10)
