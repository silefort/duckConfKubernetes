#!/usr/bin/env python3
"""
Node Controller - Surveille la santé des nœuds
"""

import time
import os
import requests
from datetime import datetime, timedelta


class NodeController:
    def __init__(self, api_url="http://localhost:8081", heartbeat_timeout=15):
        self.api_url = api_url
        self.heartbeat_timeout = heartbeat_timeout

    def get_nodes(self):
        """Récupère l'état de tous les nœuds"""
        response = requests.get(f"{self.api_url}/api/nodes")
        data = response.json()
        return data.get("nodes", [])

    def get_containers(self):
        """Récupère tous les containers"""
        response = requests.get(f"{self.api_url}/api/containers")
        data = response.json()
        return data.get("containers", [])

    def mark_for_rescheduling(self, container_name):
        """Force le réassignement d'un container"""
        response = requests.patch(
            f"{self.api_url}/api/containers/{container_name}",
            json={"node": None}
        )
        return response.ok

    def check_nodes(self):
        """Vérifie la santé des nœuds et indique les containers à réassigner sur de nouveaux noeuds si nécessaire"""
        nodes = self.get_nodes()
        containers = self.get_containers()

        # Identifier les nœuds down
        down_nodes = []
        for node in nodes:
            if node['status'] == 'down':
                down_nodes.append(node['name'])
                print(f"⚠ Nœud DOWN détecté: {node['name']}")

        if not down_nodes:
            print("✓ Tous les nœuds sont UP")
            return

        # Marque les containers des nœuds down qui doivent être réassigner
        containers_to_reschedule = [
            c for c in containers
            if c.get('node') in down_nodes
        ]

        if not containers_to_reschedule:
            print(f"  Aucun container à réassigner")
            return

        print(f"📋 Marque {len(containers_to_reschedule)} container(s) à réassigner sur de nouveaux noeuds")
        for container in containers_to_reschedule:
            success = self.mark_for_rescheduling(container['name'])
            if success:
                print(f"  ✓ {container['name']} (était sur {container['node']})")
            else:
                print(f"  ✗ Échec pour {container['name']}")

    def run(self):
        """Boucle de surveillance"""
        print("NODE CONTROLLER")
        print(f"API Server: {self.api_url}")
        print(f"Heartbeat timeout: {self.heartbeat_timeout}s")
        print()

        try:
            while True:
                self.check_nodes()
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt\n")


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8081")
    heartbeat_timeout = int(os.getenv("HEARTBEAT_TIMEOUT", "15"))
    controller = NodeController(api_url=api_url, heartbeat_timeout=heartbeat_timeout)
    controller.run()
