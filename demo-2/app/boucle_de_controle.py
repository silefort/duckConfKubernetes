#!/usr/bin/env python3
import time
import pprint
from app.ssh_utils import ssh
from app.log_helper import create_logger

log = create_logger("controlleur")

NODES = ["node-1", "node-2", "node-3"]
STATE_FILE = "/app/desired_state.csv"
compteur_node = 0

while True:
    log("======================================================")
    log("BOUCLE DE CONTROLE")
    log("======================================================")

    log("1. CAPTEUR - Observer l'état actuel")
    apps_observees = {}
    for node in NODES:
        containers = ssh(node, "docker ps --format '{{.Names}}'")
        for container in containers.split('\n'):
            if container:
                apps_observees[container] = node
    log(f"{pprint.pformat(apps_observees)}")

    log("2. CONSIGNE - Lire l'état désiré")
    apps_desirees = {}
    with open(STATE_FILE, 'r') as f:
        for line in f:
            app, image = line.strip().split(',')
            apps_desirees[app] = image
    log(f"{pprint.pformat(apps_desirees)}")

    log("3. COMPARATEUR - Identifier l'écart")
    a_demarrer = set(apps_desirees.keys()) - set(apps_observees.keys())
    log(f"a_demarrer = {a_demarrer}")
    a_arreter = set(apps_observees.keys()) - set(apps_desirees.keys())
    log(f"a_arreter = {a_arreter}")

    log("4. ACTIONNEUR - Appliquer les changements")
    for app in a_demarrer:
        node = NODES[compteur_node % len(NODES)]
        compteur_node += 1
        image = apps_desirees[app]
        log(f"Démarrage {app} sur {node}")
        ssh(node, f"docker run -d --name {app} {image}")

    for app in a_arreter:
        node = apps_observees[app]
        log(f"Arrêt {app} sur {node}")
        ssh(node, f"docker stop {app} && docker rm {app}")

    time.sleep(10)
