#!/usr/bin/env python3
import time
import os
from app.utils.log_helper import create_logger
from app.utils.shell_utils import shell
from datetime import datetime
from app.utils.http_utils import get, put

log = create_logger("app-controller")

API_SERVER = "http://api-server:8080"
NODE_NAME = os.environ.get("NODE_NAME", "unknown")

apps_voulues = {}

while True:

    log("======================================================")
    log("APP CONTROLLER - BOUCLE DE CONTRÔLE LOCALE")
    log("======================================================")

    # --- 00. Envoyer un heartbeat à l'API Server
    try:
        put(f"{API_SERVER}/node/{NODE_NAME}/heartbeat", {"timestamp": datetime.now().isoformat()})
    except Exception as e:
        log(f"00. HEARTBEAT : échec ({e})")

    # --- 01. CAPTEUR - Observer l'état actuel ---
    apps_actuelles = {}
    response = shell("docker ps --format '{{.Names}}\t{{.Image}}'")
    applications = response.split('\n') if response else []
    for application in applications:
        name, image = application.split('\t')
        apps_actuelles[name] = image
    log(f"01. CAPTEUR : applications en cours d'exécution : {apps_actuelles}")


    # --- 02. ETAT_DESIRE - Lire l'état désiré pour ce noeud ---
    try:
        response = get(f"{API_SERVER}/apps?nodeName={NODE_NAME}")
        apps_voulues = {app: info["image"] for app, info in response.items()}
    except:
        log("API server non disponible, utilisation du cache local")
    log(f"02. ETAT_DESIRE : état désiré par l'utilisateur : {apps_voulues}")


    # --- 03. COMPARATEUR - Identifier l'écart ---
    apps_a_demarrer = set(apps_voulues.keys()) - set(apps_actuelles.keys())
    apps_a_arreter = set(apps_actuelles.keys()) - set(apps_voulues.keys())
    log(f"03. COMPARATEUR : applications à demarrer = {apps_a_demarrer}")
    log(f"03. COMPARATEUR : applications à arreter = {apps_a_arreter}")


    # --- 04. ACTIONNEUR - Appliquer les changements ---
    for app in apps_a_demarrer:
        log(f"04. ACTIONNEUR : Démarrage de l'application {app}")
        shell(f"docker run -d --name {app} {apps_voulues[app]}")

    for app in apps_a_arreter:
        log(f"04. ACTIONNEUR : Arrêt de l'application {app}")
        shell(f"docker rm -f {app}")

    print()
    time.sleep(10)
