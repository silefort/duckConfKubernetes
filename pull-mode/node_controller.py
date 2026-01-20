#!/usr/bin/env python3
import time
import os
import requests

API_URL = os.getenv("API_URL", "http://localhost:8081")

# état observé
def etat_observe():
    response = requests.get(f"{API_URL}/api/nodes")
    return response.json().get("nodes", [])

# réconcilier l'état
def reconcilie(noeuds):
    noeuds_down = [n for n in noeuds if n['status'] == 'down']

    if not noeuds_down:
        print("Rien à faire (tous les noeuds sont UP)")
        return

    for noeud in noeuds_down:
        print(f"Noeud DOWN détecté: {noeud['name']}")

    apps_a_delier = []
    for noeud in noeuds_down:
        for app in noeud.get('apps', []):
            apps_a_delier.append({"name": app, "node": noeud['name']})

    if not apps_a_delier:
        print("  Aucune app à délier")
        return

    print(f"\nRECONCILIATION")
    for app in apps_a_delier:
        requests.patch(f"{API_URL}/api/apps/{app['name']}", json={"node": None})
        print(f"  Délie: {app['name']} (était sur {app['node']})")

    print(f"Terminé\n")

print("NODE CONTROLLER")
print(f"API Server: {API_URL}")
print()

while True:

    # Observe l'état Réel
    observe = etat_observe()

    # État souhaité: aucune app sur un noeud "down"

    # Réconcilie les 2 états
    reconcilie(observe)
    time.sleep(10)
