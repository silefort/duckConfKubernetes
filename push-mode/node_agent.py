#!/usr/bin/env python3
"""
Node Agent - Push Mode
Nœud simple qui tourne et attend les connexions SSH
"""
import time
import os

NODE_NAME = os.getenv("NODE_NAME", "node-unknown")

if __name__ == "__main__":
    print(f"NODE {NODE_NAME} démarré")
    print("En attente de commandes SSH...")

    # Créer le fichier running.txt vide s'il n'existe pas
    running_file = f"/app/{NODE_NAME}_running.txt"
    if not os.path.exists(running_file):
        with open(running_file, 'w') as f:
            f.write('')

    # Boucle infinie pour garder le container actif
    while True:
        time.sleep(60)
