#!/usr/bin/env python3
import time
import os
import requests
from pathlib import Path

API_URL = os.getenv("API_URL", "http://localhost:8081")
NODE_NAME = os.getenv("NODE_NAME", "node-1")
ETAT_SOUHAITE_FILE = Path(f"nodes/{NODE_NAME}_souhaite.txt")
ETAT_OBSERVE_FILE = Path(f"nodes/{NODE_NAME}_observe.txt")

# état observé
def etat_observe():
    if not ETAT_OBSERVE_FILE.exists():
        return set()
    content = ETAT_OBSERVE_FILE.read_text().strip()
    return set(content.split('\n')) if content else set()

# état souhaité
def etat_souhaite():
    try:
        response = requests.get(f"{API_URL}/api/apps?node={NODE_NAME}", timeout=2)
        apps = [a['name'] for a in response.json().get("apps", [])]
        ETAT_SOUHAITE_FILE.write_text('\n'.join(apps))
        return set(apps)
    except:
        print("API inaccessible, utilisation de l'etat local")
        if not ETAT_SOUHAITE_FILE.exists():
            return set()
        content = ETAT_SOUHAITE_FILE.read_text().strip()
        return set(content.split('\n')) if content else set()

# réconcilier l'état
def reconcilie(observe, souhaite):
    a_demarrer = souhaite - observe
    a_stopper = observe - souhaite

    if not a_demarrer and not a_stopper:
        print(f"Rien à faire ({len(observe)} apps en cours)")
        return

    print(f"\nRECONCILIATION")

    for app in a_stopper:
        stop_app(app)

    for app in a_demarrer:
        start_app(app)

    print(f"Terminé\n")

def start_app(app_name):
    applications = etat_observe()
    applications.add(app_name)
    ETAT_OBSERVE_FILE.write_text('\n'.join(applications))
    print(f"  Démarre: {app_name}")

def stop_app(app_name):
    applications = etat_observe()
    applications.discard(app_name)
    ETAT_OBSERVE_FILE.write_text('\n'.join(applications))
    print(f"  Arrête: {app_name}")

def envoyer_heartbeat():
    try:
        requests.post(f"{API_URL}/api/nodes/{NODE_NAME}/heartbeat", timeout=2)
    except:
        pass

print(f"APP CONTROLLER - {NODE_NAME}")
print(f"Etat souhaité: {ETAT_SOUHAITE_FILE}")
print(f"Etat observé: {ETAT_OBSERVE_FILE}")
print()

while True:
    # Envoie le heartbeat
    envoyer_heartbeat()

    # Observe l'état Réel
    observe = etat_observe()

    # Récupère l'état souhaité
    souhaite = etat_souhaite()

    # Réconcilie les 2 états
    reconcilie(observe, souhaite)
    time.sleep(5)
