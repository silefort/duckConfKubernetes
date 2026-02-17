#!/usr/bin/env python3
import json
import time
import pprint
from app.utils.ssh_utils import ssh
from app.utils.log_helper import create_logger

log = create_logger("app-controller")

NODES = ["node-1", "node-2", "node-3"]
APPS_FILE = "/app/apps.json"
compteur_node = 0

while True:
    debut_boucle = time.time()
    log("======================================================")
    log("BOUCLE DE CONTROLE CENTRALISÉE")
    log("======================================================")

    log("1. CAPTEUR - Observer l'état actuel")
    apps_actuelles = {}
    for node in NODES:
        containers = ssh(node, "docker ps --format '{{.Names}}'")
        for container in containers.split('\n'):
            if container:
                apps_actuelles[container] = node
    log(f"01. CAPTEUR : applications observées sur tous les noeuds : {pprint.pformat(apps_actuelles)}")

    log("2. ETAT_DESIRE - Lire l'état désiré")
    with open(APPS_FILE, 'r') as f:
        apps = json.load(f)
    apps_voulues = {nom: info["image"] for nom, info in apps.items()}
    log(f"02. ETAT_DESIRE : état désiré par l'utilisateur : {pprint.pformat(apps_voulues)}")

    log("3. DETECTEUR - Identifier l'écart")
    apps_a_demarrer = set(apps_voulues.keys()) - set(apps_actuelles.keys())
    log(f"03. DETECTEUR : applications à démarrer = {apps_a_demarrer}")
    apps_a_arreter = set(apps_actuelles.keys()) - set(apps_voulues.keys())
    log(f"03. DETECTEUR : applications à arrêter = {apps_a_arreter}")

    log("4. ACTIONNEUR - Appliquer les changements")
    for app in apps_a_demarrer:
        node = NODES[compteur_node % len(NODES)]  # ← Décision de scheduling
        compteur_node += 1
        image = apps_voulues[app]
        log(f"04. ACTIONNEUR : Démarrage de l'application {app} sur {node}")
        ssh(node, f"docker run -d --name {app} {image}")

    for app in apps_a_arreter:
        node = apps_actuelles[app]
        log(f"04. ACTIONNEUR : Arrêt de l'application {app} sur {node}")
        ssh(node, f"docker stop {app} && docker rm {app}")

    fin_boucle = time.time()
    duree = fin_boucle - debut_boucle
    log(f"⏱️  TEMPS DE BOUCLE : {duree:.2f}s")
    log("")
    log("")
    time.sleep(10)
