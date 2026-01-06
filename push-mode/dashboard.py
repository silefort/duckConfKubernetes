#!/usr/bin/env python3
"""
Dashboard Minimal - Mode Push
Vue simple : nœuds, containers
"""

import os
import time
import requests


class MinimalDashboard:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url

    def get_cluster_state(self):
        """Récupère l'état du cluster"""
        try:
            response = requests.get(f"{self.api_url}/containers", timeout=2)
            data = response.json()
            return data.get("containers", []), None
        except Exception as e:
            return [], str(e)

    def render(self):
        """Affiche l'état du cluster"""
        containers, error = self.get_cluster_state()

        if error:
            print("❌ API inaccessible")
            return

        # Grouper par nœud
        nodes_data = {}
        for container in containers:
            node = container.get('node', 'unknown')
            if node not in nodes_data:
                nodes_data[node] = []
            nodes_data[node].append(container['name'])

        # Afficher chaque nœud
        print()
        for node in ["node-1", "node-2", "node-3"]:
            containers_on_node = nodes_data.get(node, [])
            containers_str = ", ".join(containers_on_node) if containers_on_node else "(vide)"
            
            print(f"🖥️  {node:<10} {containers_str}")
        
        print()

    def run(self, refresh_interval=5):
        """Boucle principale"""
        try:
            while True:
                self.render()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8080")
    refresh = int(os.getenv("REFRESH_INTERVAL", "5"))
    
    dashboard = MinimalDashboard(api_url=api_url)
    dashboard.run(refresh_interval=refresh)