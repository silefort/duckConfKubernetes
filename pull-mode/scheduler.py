#!/usr/bin/env python3
"""
Scheduler - Assigne les containers aux nœuds
"""

import time
import os
import requests
from pathlib import Path


class Scheduler:
    def __init__(self, api_url="http://localhost:8081", nodes=None):
        self.api_url = api_url
        self.nodes = nodes or ["node-1", "node-2", "node-3"]
        self.current_node_index = 0

    def get_next_node(self):
        """Round-robin simple pour choisir un nœud"""
        node = self.nodes[self.current_node_index]
        self.current_node_index = (self.current_node_index + 1) % len(self.nodes)
        return node

    def get_containers(self):
        """Récupère tous les containers"""
        response = requests.get(f"{self.api_url}/api/containers")
        data = response.json()
        return data.get("containers", [])

    def update_container_node(self, container_name, node_name):
        """Met à jour le nœud d'un container"""
        response = requests.patch(
            f"{self.api_url}/api/containers/{container_name}",
            json={"node": node_name}
        )
        return response.ok

    def schedule(self):
        """Assigne un nœud aux containers qui n'en ont pas"""
        containers = self.get_containers()

        unscheduled = [c for c in containers if not c.get('node')]

        if not unscheduled:
            print("✓ Tous les containers sont schedulés")
            return

        print(f"\n📋 {len(unscheduled)} container(s) à scheduler")

        for container in unscheduled:
            node = self.get_next_node()
            success = self.update_container_node(container['name'], node)
            if success:
                print(f"  ✓ {container['name']} → {node}")
            else:
                print(f"  ✗ Échec pour {container['name']}")

    def run(self):
        """Boucle de scheduling"""
        print("SCHEDULER")
        print(f"API Server: {self.api_url}")
        print(f"Nœuds disponibles: {', '.join(self.nodes)}")
        print()

        try:
            while True:
                self.schedule()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt\n")


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8081")
    nodes = os.getenv("NODES", "node-1,node-2,node-3").split(",")
    scheduler = Scheduler(api_url=api_url, nodes=nodes)
    scheduler.run()
