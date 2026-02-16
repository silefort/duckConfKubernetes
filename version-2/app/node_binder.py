#!/usr/bin/env python3
import time
from app.utils.log_helper import create_logger
from app.utils.http_utils import get, put

log = create_logger("node-binder")

API_SERVER = "http://api-server:8080"
NODES = ["node-1", "node-2", "node-3"]
compteur_node = 0

while True:
    log("======================================================")
    log("NODE BINDER - BOUCLE DE CONTRÔLE")
    log("======================================================")

    # --- 01. CAPTEUR - Récupérer les applications qui n'ont pas de node assignés
    #                   sur l'API Server ---
    try:
        apps_sans_noeud = get(f"{API_SERVER}/apps?nodeName=")
    except Exception as e:
        log(f"API server non disponible: {e}")
        apps_sans_noeud = {}
    log("01. CAPTEUR : apps en attente de binding :")
    for app, info in apps_sans_noeud.items():
        log(f"    {app}: {info.get('image', 'N/A')}")

    # --- 02. ETAT_DESIRE - Implicite : toutes les applications doivent avoir un noeud d'assigné ---
    log(f"02. ETAT_DESIRE : Implicite : toutes les applications doivent avoir un noeud d'assigné")

    # --- 03. DETECTEUR - Identifier l'écart ---
    apps_a_assigner = list(apps_sans_noeud.keys())
    log("03. DETECTEUR : apps en attente de binding :")
    for app, info in apps_sans_noeud.items():
        log(f"    {app}: {info.get('image', 'N/A')}")

    # --- 04. ACTIONNEUR - Appliquer les changements ---
    for app in apps_a_assigner:
        node = NODES[compteur_node % len(NODES)]
        compteur_node += 1
        put(f"{API_SERVER}/app/{app}", {"node": node})
        log(f"04. ACTIONNEUR : {app} -> {node}")

    log("")
    log("")
    time.sleep(10)
