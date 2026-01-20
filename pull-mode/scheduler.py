#!/usr/bin/env python3
import time
import os
import requests

API_URL = os.getenv("API_URL", "http://localhost:8081")
NOEUDS = os.getenv("NODES", "node-1,node-2,node-3").split(",")
noeud_courant = 0

# état observé
def etat_observe():
    response = requests.get(f"{API_URL}/api/apps")
    return response.json().get("apps", [])

# état souhaité (implicite: toutes les apps assignées à un noeud)

# réconcilier l'état
def reconcilie(apps):
    global noeud_courant
    non_assignees = [a for a in apps if not a.get('node')]

    if not non_assignees:
        print("Rien à faire (toutes les apps sont assignées)")
        return

    print(f"\nRECONCILIATION")
    for app in non_assignees:
        noeud = NOEUDS[noeud_courant]
        noeud_courant = (noeud_courant + 1) % len(NOEUDS)
        requests.patch(f"{API_URL}/api/apps/{app['name']}", json={"node": noeud})
        print(f"  Assigne: {app['name']} -> {noeud}")

    print(f"Terminé\n")

print("SCHEDULER")
print(f"API Server: {API_URL}")
print(f"Noeuds disponibles: {', '.join(NOEUDS)}")
print()

while True:

    # Observe l'état Réel
    observe = etat_observe()

    # État souhaité: toutes les apps assignées

    # Réconcilie les 2 états
    reconcilie(observe)
    time.sleep(5)
