#!/usr/bin/env python3
import time
import os
import requests


class Scheduler:
    def __init__(self, api_url="http://localhost:8081", nodes=None):
        self.api_url = api_url
        self.nodes = nodes or ["node-1", "node-2", "node-3"]
        self.current_node_index = 0

    def get_next_node(self):
        node = self.nodes[self.current_node_index]
        self.current_node_index = (self.current_node_index + 1) % len(self.nodes)
        return node

    def get_apps(self):
        response = requests.get(f"{self.api_url}/api/apps")
        data = response.json()
        return data.get("apps", [])

    def update_app_node(self, app_name, node_name):
        response = requests.patch(
            f"{self.api_url}/api/apps/{app_name}",
            json={"node": node_name}
        )
        return response.ok

    def schedule(self):
        apps = self.get_apps()

        unscheduled = [a for a in apps if not a.get('node')]

        if not unscheduled:
            print("Toutes les apps sont schedulees")
            return

        print(f"\n{len(unscheduled)} app(s) a scheduler")

        for app in unscheduled:
            node = self.get_next_node()
            success = self.update_app_node(app['name'], node)
            if success:
                print(f"  {app['name']} -> {node}")
            else:
                print(f"  Echec pour {app['name']}")

    def run(self):
        print("SCHEDULER")
        print(f"API Server: {self.api_url}")
        print(f"Noeuds disponibles: {', '.join(self.nodes)}")
        print()

        while True:
            self.schedule()
            time.sleep(5)


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8081")
    nodes = os.getenv("NODES", "node-1,node-2,node-3").split(",")
    scheduler = Scheduler(api_url=api_url, nodes=nodes)
    scheduler.run()
