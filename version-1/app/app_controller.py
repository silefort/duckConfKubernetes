#!/usr/bin/env python3
import json
import time
from app.utils.ssh_utils import ssh
from app.utils.log_helper import create_logger

log = create_logger("app-controller")

NODES = ["node-1", "node-2", "node-3"]
APPS_FILE = "/app/apps.json"
compteur_node = 0
iteration = 0

while True:
    iteration += 1
    # CAPTEUR
    apps_actuelles = {}
    for node in NODES:
        containers = ssh(node, "docker ps --format '{{.Names}}'")
        for container in containers.split('\n'):
            if container:
                apps_actuelles[container] = node

    # ETAT DESIRE
    with open(APPS_FILE, 'r') as f:
        apps = json.load(f)
    apps_voulues = {nom: info["image"] for nom, info in apps.items()}

    # DETECTEUR
    apps_a_demarrer = set(apps_voulues.keys()) - set(apps_actuelles.keys())
    apps_a_arreter = set(apps_actuelles.keys()) - set(apps_voulues.keys())

    # ACTIONNEUR
    if not apps_a_demarrer and not apps_a_arreter:
        log(f"#{iteration} état désiré atteint")

    for app in apps_a_demarrer:
        node = NODES[compteur_node % len(NODES)]  # ← Décision de scheduling
        compteur_node += 1
        image = apps_voulues[app]
        log(f"#{iteration} {app} -> {node}")
        ssh(node, f"docker run -d --name {app} {image}")

    for app in apps_a_arreter:
        node = apps_actuelles[app]
        log(f"#{iteration} arrêt de {app} (était sur {node})")
        ssh(node, f"docker stop {app} && docker rm {app}")

    time.sleep(7)
