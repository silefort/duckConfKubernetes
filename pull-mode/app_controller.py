#!/usr/bin/env python3
import time
import os
import requests
from pathlib import Path

class AppController:
    def __init__(self,
                 api_url="http://localhost:8081",
                 node_name="node-1",
                 desired_state_file=None,
                 running_apps_file=None):
        self.api_url = api_url
        self.node_name = node_name
        self.desired_state_file = Path(desired_state_file or f"nodes/{node_name}_desired.txt")
        self.running_apps_file = Path(running_apps_file or f"nodes/{node_name}_running.txt")
        self.desired_state_file.touch()
        self.running_apps_file.touch()

    def send_heartbeat(self):
        try:
            requests.post(f"{self.api_url}/api/nodes/{self.node_name}/heartbeat", timeout=2)
        except:
            pass

    def get_desired_state(self):
        try:
            response = requests.get(f"{self.api_url}/api/apps", params={"node": self.node_name}, timeout=2)
            apps = response.json().get("apps", [])
            self.desired_state_file.write_text('\n'.join(apps))
            return set(apps)
        except:
            print("API inaccessible, utilisation de l'etat local")
            content = self.desired_state_file.read_text().strip()
            return set(content.split('\n')) if content else set()

    def get_running_apps(self):
        content = self.running_apps_file.read_text().strip()
        return set(content.split('\n')) if content else set()

    def start_app(self, app_name):
        running = self.get_running_apps()
        running.add(app_name)
        self.running_apps_file.write_text('\n'.join(sorted(running)))
        print(f"  START: {app_name}")

    def stop_app(self, app_name):
        running = self.get_running_apps()
        running.discard(app_name)
        self.running_apps_file.write_text('\n'.join(sorted(running)))
        print(f"  STOP: {app_name}")

    def reconcile(self):
        desired = self.get_desired_state()
        running = self.get_running_apps()
        to_start = desired - running
        to_stop = running - desired

        if not to_start and not to_stop:
            print(f"Converge ({len(running)} apps)")
            return

        print(f"\nRECONCILIATION")

        for app in to_stop:
            self.stop_app(app)

        for app in to_start:
            self.start_app(app)

        print(f"Termine\n")

    def run(self):
        print(f"APP CONTROLLER - {self.node_name}")
        print(f"Etat desire: {self.desired_state_file}")
        print(f"Etat actuel: {self.running_apps_file}")

        while True:
            self.send_heartbeat()
            self.reconcile()
            time.sleep(5)

if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8081")
    node_name = os.getenv("NODE_NAME", "node-1")
    controller = AppController(api_url=api_url, node_name=node_name)
    controller.run()
