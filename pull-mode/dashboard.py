#!/usr/bin/env python3
import os
import time
import requests


class MinimalDashboard:
    def __init__(self, api_url="http://localhost:8080"):
        self.api_url = api_url

    def get_nodes_state(self):
        """Récupère l'état des nœuds"""
        try:
            response = requests.get(f"{self.api_url}/api/nodes", timeout=2)
            data = response.json()
            return data.get("nodes", []), None
        except Exception as e:
            return [], str(e)

    def get_containers_state(self):
        """Récupère l'état des containers"""
        try:
            response = requests.get(f"{self.api_url}/api/containers", timeout=2)
            data = response.json()
            return data.get("containers", []), None
        except Exception as e:
            return [], str(e)

    def render(self):
        """Affiche l'état du cluster"""
        nodes, nodes_error = self.get_nodes_state()
        containers, containers_error = self.get_containers_state()

        if nodes_error or containers_error:
            print("❌ API inaccessible")
            return

        # Grouper containers par nœud
        nodes_containers = {}
        for container in containers:
            node = container.get('node')
            if node:
                if node not in nodes_containers:
                    nodes_containers[node] = []
                nodes_containers[node].append(container['name'])

        # Afficher chaque nœud
        print()
        for node in nodes:
            node_name = node['name']
            status = node['status']
            
            status_icon = "🟢" if status == 'up' else "🔴"
            
            containers_on_node = nodes_containers.get(node_name, [])
            containers_str = ", ".join(containers_on_node) if containers_on_node else "(vide)"
            
            print(f"{status_icon} {node_name:<10} {containers_str}")
        
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