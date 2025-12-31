#!/usr/bin/env python3
"""
Simulateur de Kubelet
Démontre le principe de réconciliation de Kubernetes
"""

import time
import os
import requests
from pathlib import Path


class KubeletSimulator:
    def __init__(self,
                 api_url="http://localhost:8080",
                 node_name="node-1",
                 desired_state_file=None,
                 running_containers_file=None):
        self.api_url = api_url
        self.node_name = node_name
        self.desired_state_file = Path(desired_state_file or f"nodes/{node_name}_desired.txt")
        self.running_containers_file = Path(running_containers_file or f"nodes/{node_name}_running.txt")
        self.desired_state_file.touch()
        self.running_containers_file.touch()

    def send_heartbeat(self):
        """Envoie un heartbeat à l'API"""
        try:
            requests.post(
                f"{self.api_url}/api/nodes/{self.node_name}/heartbeat",
                timeout=2
            )
        except:
            pass  # Ignore les erreurs de heartbeat

    def get_desired_state(self):
        """Récupère l'état désiré depuis l'API pour ce nœud uniquement"""
        try:
            response = requests.get(
                f"{self.api_url}/api/containers",
                params={"node": self.node_name},
                timeout=2
            )
            data = response.json()
            containers = data.get("containers", [])

            # Sauvegarder l'état désiré localement
            self.desired_state_file.write_text('\n'.join(containers))

            return set(containers)
        except:
            # Si l'API est inaccessible, utiliser l'état local
            print("⚠ API inaccessible, utilisation de l'état local")
            content = self.desired_state_file.read_text().strip()
            if not content:
                return set()
            return set(line.strip() for line in content.split('\n') if line.strip())

    def get_running_containers(self):
        """Lit les containers en cours d'exécution"""
        content = self.running_containers_file.read_text().strip()
        if not content:
            return set()
        return set(line.strip() for line in content.split('\n') if line.strip())

    def start_container(self, container_name):
        """Démarre un container"""
        running = self.get_running_containers()
        running.add(container_name)
        self.running_containers_file.write_text('\n'.join(sorted(running)))
        print(f"  ▶ START: {container_name}")

    def stop_container(self, container_name):
        """Arrête un container"""
        running = self.get_running_containers()
        running.discard(container_name)
        self.running_containers_file.write_text('\n'.join(sorted(running)))
        print(f"  ◼ STOP: {container_name}")

    def reconcile(self):
        """Réconciliation: converge vers l'état désiré"""
        desired = self.get_desired_state()
        running = self.get_running_containers()

        # Calcule les différences
        to_start = desired - running  # Containers à démarrer
        to_stop = running - desired   # Containers à arrêter

        if not to_start and not to_stop:
            print(f"✓ Convergé ({len(running)} containers)")
            return

        print(f"\n🔄 RECONCILIATION")

        # Arrêter les containers en trop
        for container in to_stop:
            self.stop_container(container)

        # Démarrer les containers manquants
        for container in to_start:
            self.start_container(container)

        print(f"✓ Terminé\n")

    def run(self):
        """Boucle de réconciliation infinie"""
        print(f"KUBELET SIMULATOR - {self.node_name}")
        print(f"API Server: {self.api_url}")
        print(f"État désiré: {self.desired_state_file}")
        print(f"État actuel: {self.running_containers_file}")

        try:
            while True:
                # Envoyer le heartbeat
                self.send_heartbeat()

                # Reconcilie l'etat observe avec l'etat desire
                self.reconcile()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\n👋 Arrêt\n")


if __name__ == "__main__":
    api_url = os.getenv("API_URL", "http://localhost:8080")
    node_name = os.getenv("NODE_NAME", "node-1")
    agent = KubeletSimulator(api_url=api_url, node_name=node_name)
    agent.run()
