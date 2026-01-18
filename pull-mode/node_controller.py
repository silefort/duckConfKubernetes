#!/usr/bin/env python3
import time
import os
import requests
from datetime import datetime, timedelta


class NodeController:
    def __init__(self, api_url="http://localhost:8081", heartbeat_timeout=15):
        self.api_url = api_url
        self.heartbeat_timeout = heartbeat_timeout

    def get_nodes(self):
        response = requests.get(f"{self.api_url}/api/nodes")
        data = response.json()
        return data.get("nodes", [])

    def get_apps(self):
        response = requests.get(f"{self.api_url}/api/apps")
        data = response.json()
        return data.get("apps", [])

    def reschedule_app(self, app_name):
        response = requests.patch(
            f"{self.api_url}/api/apps/{app_name}",
            json={"node": None}
        )
        return response.ok

    def check_nodes(self):
        nodes = self.get_nodes()
        apps = self.get_apps()
        down_nodes = []
        for node in nodes:
            if node['status'] == 'down':
                down_nodes.append(node['name'])
                print(f"Noeud DOWN detecte: {node['name']}")

        if not down_nodes:
            print("Tous les noeuds sont UP")
            return

        apps_to_reschedule = [
            a for a in apps
            if a.get('node') in down_nodes
        ]

        if not apps_to_reschedule:
            print(f"  Aucune app a reassigner")
            return

        print(f"Reassignation de {len(apps_to_reschedule)} app(s)")
        for app in apps_to_reschedule:
            success = self.reschedule_app(app['name'])
            if success:
                print(f"  {app['name']} (etait sur {app['node']})")
            else:
                print(f"  Echec pour {app['name']}")

    def run(self):
        print("NODE CONTROLLER")
        print(f"API Server: {self.api_url}")
        print(f"Heartbeat timeout: {self.heartbeat_timeout}s")
        print()

        while True:
            self.check_nodes()
            time.sleep(10)


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8081")
    heartbeat_timeout = int(os.getenv("HEARTBEAT_TIMEOUT", "15"))
    controller = NodeController(api_url=api_url, heartbeat_timeout=heartbeat_timeout)
    controller.run()
