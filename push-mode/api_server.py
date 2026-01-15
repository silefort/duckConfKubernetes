#!/usr/bin/env python3
"""
API Server - Control Plane Kubernetes (Push Mode)
"""

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

from flask import Flask, jsonify, request
import paramiko
import io

app = Flask(__name__)

SSH_USER = "root"
SSH_PASSWORD = "root"
SSH_PORT = 22
AVAILABLE_NODES = ["node-1", "node-2", "node-3"]
scheduler_index = 0  # Pour round-robin


def select_node():
    """Sélectionne un nœud automatiquement (round-robin)"""
    global scheduler_index
    node = AVAILABLE_NODES[scheduler_index % len(AVAILABLE_NODES)]
    scheduler_index += 1
    return node


def get_containers_from_node_ssh(node_name):
    """Se connecte en SSH au nœud et récupère la liste des containers"""
    try:
        # Connexion SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(node_name, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        # Lire le fichier running.txt distant
        remote_file = f"/app/nodes/{node_name}_running.txt"
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_file} 2>/dev/null || echo ''")
        content = stdout.read().decode('utf-8').strip()

        # Parser les containers existants
        containers = [c.strip() for c in content.split('\n') if c.strip()]

        ssh.close()
        return containers

    except Exception as e:
        print(f"  ✗ Erreur SSH vers {node_name}: {e}")
        return []


def write_container_to_node_ssh(node_name, container_name):
    """Se connecte en SSH au nœud et modifie le fichier running.txt"""
    try:
        # Connexion SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(node_name, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        # Lire le fichier running.txt distant
        remote_file = f"/app/nodes/{node_name}_running.txt"
        stdin, stdout, stderr = ssh.exec_command(f"cat {remote_file} 2>/dev/null || echo ''")
        content = stdout.read().decode('utf-8').strip()

        # Parser les containers existants
        containers = [c.strip() for c in content.split('\n') if c.strip()]

        # Ajouter le container s'il n'existe pas déjà
        if container_name not in containers:
            containers.append(container_name)
            new_content = '\n'.join(containers)

            # Écrire le nouveau contenu
            stdin, stdout, stderr = ssh.exec_command(f"echo '{new_content}' > {remote_file}")
            stdout.channel.recv_exit_status()  # Attendre la fin de la commande

            ssh.close()
            return True
        else:
            ssh.close()
            return False

    except Exception as e:
        print(f"  ✗ Erreur SSH vers {node_name}: {e}")
        return False


@app.route('/containers', methods=['GET'])
def get_containers():
    """Récupère tous les containers du cluster"""
    result = []

    # Récupérer les containers de chaque nœud
    for node_name in AVAILABLE_NODES:
        containers = get_containers_from_node_ssh(node_name)
        for container in containers:
            result.append({
                "name": container,
                "node": node_name
            })

    return jsonify({
        "total": len(result),
        "containers": result
    })


@app.route('/container/start', methods=['POST'])
def start_container():
    """Démarre un container sur un nœud (auto-schedulé si node non spécifié)"""
    data = request.get_json()
    container_name = data.get('name')
    node_name = data.get('node')

    if not container_name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    node_name = select_node()
    print(f"  ⚙ Scheduling: {container_name} → {node_name}")

    # Se connecter en SSH au nœud pour démarrer le container
    added = write_container_to_node_ssh(node_name, container_name)

    if added:
        print(f"  → START: {container_name} sur {node_name}")
        return jsonify({
            "status": "started",
            "container": container_name,
            "node": node_name
        }), 201
    else:
        print(f"  → Already running: {container_name} sur {node_name}")
        return jsonify({
            "status": "already_running",
            "container": container_name,
            "node": node_name
        }), 200


if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("API SERVER (Push Mode)")
    print("Routes:")
    print("  POST /container/start - Démarre un container")
    print("  GET  /containers      - Liste tous les containers")
    print(f"Nœuds disponibles: {', '.join(AVAILABLE_NODES)}")
    print("Scheduling: Round-robin automatique")
    print()
    app.run(host='0.0.0.0', port=8080, debug=False)
