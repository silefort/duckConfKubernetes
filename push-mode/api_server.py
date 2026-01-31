#!/usr/bin/env python3
"""
Control Plane Mode Imperatif et simple
"""

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*TripleDES.*')
from flask import Flask, jsonify, request
import paramiko

app = Flask(__name__)
NODES = ["node-1", "node-2", "node-3"]
scheduler_index = 0

@app.route('/container/start', methods=['POST'])
def start_container():
    """Demarre un container sur un noeud"""
    data = request.get_json()
    image = data.get('image', 'nginx:alpine')
    name = data.get('name', f"app-{scheduler_index}")

    node = selectionner_noeud()

    # Prefixe duckconf-{node}- pour identifier les containers et leur node
    container_name = f"duckconf-{node}-{name}"
    cmd = f"docker run -d --name {container_name} {image}"

    result = executer_ssh(node, cmd)
    container_id = result[:12] if result else "error"

    print(f"Container {name} ({image}) demarre sur {node}")
    return jsonify({
        "status": "started",
        "container": name,
        "image": image,
        "node": node,
        "container_id": container_id
    }), 201


def parse_container_name(full_name):
    """Parse duckconf-node-1-app-0 -> (node-1, app-0)"""
    # Enleve le prefixe duckconf-
    without_prefix = full_name.replace('duckconf-', '')  # node-1-app-0
    # Le node est toujours node-X (7 caracteres)
    node = without_prefix[:6]  # node-1
    name = without_prefix[7:]  # app-0
    return node, name


@app.route('/container/list', methods=['GET'])
def list_containers():
    """Liste les containers (depuis node-1, tous partagent le meme daemon)"""
    containers = []

    try:
        result = executer_ssh("node-1", "docker ps --filter 'name=duckconf-' --format '{{.Names}}\t{{.Image}}\t{{.Status}}'")
        for line in result.split('\n'):
            if line:
                parts = line.split('\t')
                full_name = parts[0]  # duckconf-node-1-app-0
                node, name = parse_container_name(full_name)
                containers.append({
                    "name": name,
                    "image": parts[1] if len(parts) > 1 else "",
                    "status": parts[2] if len(parts) > 2 else "",
                    "node": node
                })
    except Exception as e:
        print(f"Erreur: {e}")

    return jsonify({"containers": containers})


@app.route('/container/stop', methods=['POST'])
def stop_container():
    """Arrete un container par son nom (cherche le container duckconf-*-{name})"""
    name = request.get_json()['name']

    try:
        # Cherche le container qui finit par -{name}
        result = executer_ssh("node-1", f"docker ps --filter 'name=duckconf-' --format '{{{{.Names}}}}' | grep '\\-{name}$'")
        if result:
            container_name = result.split('\n')[0]  # Premier match
            node, _ = parse_container_name(container_name)
            executer_ssh("node-1", f"docker stop {container_name} && docker rm {container_name}")
            print(f"Container {name} arrete (etait sur {node})")
            return jsonify({"status": "stopped", "container": name, "node": node})
    except Exception as e:
        print(f"Erreur: {e}")

    return jsonify({"status": "not_found", "container": name}), 404


def executer_ssh(node, cmd):
    """Se connecte a un noeud en ssh et execute une commande"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, port=22, username="root", password="root", timeout=5)
    _, stdout, _ = ssh.exec_command(cmd)
    result = stdout.read().decode().strip()
    ssh.close()
    return result


def selectionner_noeud():
    """Selectionne un noeud (round-robin)"""
    global scheduler_index
    node = NODES[scheduler_index % len(NODES)]
    scheduler_index += 1
    return node


if __name__ == "__main__":
    print()
    app.run(host='0.0.0.0', port=8080, debug=False)
