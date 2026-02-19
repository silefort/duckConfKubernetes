#!/usr/bin/env python3
import time
from app.utils.log_helper import create_logger
from app.utils.http_utils import get, put

log = create_logger("node-binder")

API_SERVER = "http://api-server:8080"
NODES = ["node-1", "node-2", "node-3"]
compteur_node = 0
iteration = 0

while True:
    iteration += 1
    api_error = None
    try:
        apps_sans_noeud = get(f"{API_SERVER}/apps?nodeName=")
    except Exception as e:
        api_error = e
        apps_sans_noeud = {}

    # --- 02. ETAT_DESIRE - Implicite : toutes les applications doivent avoir un noeud d'assigné ---

    # --- 03. DETECTEUR - Identifier l'écart ---
    apps_a_assigner = list(apps_sans_noeud.keys())

    if api_error:
        log(f"#{iteration} API server non disponible ({api_error})")
    elif not apps_a_assigner:
        log(f"#{iteration} toutes les apps assignées")
    else:
        log(f"#{iteration} {len(apps_a_assigner)} app(s) à assigner")
        # --- 04. ACTIONNEUR - Appliquer les changements ---
        for app in apps_a_assigner:
            node = NODES[compteur_node % len(NODES)]
            compteur_node += 1
            put(f"{API_SERVER}/app/{app}", {"node": node})
            log(f"#{iteration} assigner {app} à {node}")
    time.sleep(10)
