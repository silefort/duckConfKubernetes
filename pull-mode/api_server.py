#!/usr/bin/env python3
"""
API Server - Control Plane Kubernetes
"""

from flask import Flask, jsonify, request
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)

DESIRED_STATE_FILE = Path("desired_state.txt")
NODES_STATE = {}  # {node_name: last_heartbeat_timestamp}
HEARTBEAT_TIMEOUT = 15  # secondes


def read_desired_state():
    """Lit l'état désiré au format name:node"""
    content = DESIRED_STATE_FILE.read_text().strip()
    if not content:
        return []
    result = []
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            name, node = line.split(':', 1)
            result.append({"name": name.strip(), "node": node.strip() or None})
        else:
            # Container sans nœud assigné
            result.append({"name": line.strip(), "node": None})
    return result

def write_desired_state(containers):
    """Écrit l'état désiré au format name:node"""
    lines = []
    for c in containers:
        if c.get('node'):
            lines.append(f"{c['name']}:{c['node']}")
        else:
            lines.append(c['name'])
    DESIRED_STATE_FILE.write_text('\n'.join(lines))

@app.route('/api/containers', methods=['GET'])
def get_containers():
    containers = read_desired_state()

    # Filtrer par nœud si le paramètre est fourni
    node_filter = request.args.get('node')
    if node_filter:
        containers = [c['name'] for c in containers if c.get('node') == node_filter]
        return jsonify({"containers": containers})

    return jsonify({"containers": containers})


@app.route('/api/containers', methods=['POST'])
def add_container():
    data = request.get_json()
    container_name = data.get('name')
    node_name = data.get('node')  # Peut être None

    containers = read_desired_state()
    # Vérifier si le container existe déjà
    exists = any(c['name'] == container_name for c in containers)
    if not exists:
        containers.append({"name": container_name, "node": node_name})
        write_desired_state(containers)
        if node_name:
            print(f"  + Ajout: {container_name} sur {node_name}")
        else:
            print(f"  + Ajout: {container_name} (non schedulé)")

    return jsonify({"containers": containers}), 201


@app.route('/api/containers/<name>', methods=['PATCH'])
def update_container(name):
    """Met à jour un container (ex: assigner un nœud)"""
    data = request.get_json()
    new_node = data.get('node')

    containers = read_desired_state()
    for container in containers:
        if container['name'] == name:
            container['node'] = new_node
            write_desired_state(containers)
            print(f"  → Scheduling: {name} sur {new_node}")
            return jsonify({"containers": containers})

    return jsonify({"error": "Container not found"}), 404


@app.route('/api/containers/<name>', methods=['DELETE'])
def delete_container(name):
    containers = read_desired_state()
    # Trouver et supprimer le container par son nom
    containers = [c for c in containers if c['name'] != name]
    write_desired_state(containers)
    print(f"  - Suppression: {name}")
    return jsonify({"containers": containers})


@app.route('/api/nodes/<node_name>/heartbeat', methods=['POST'])
def heartbeat(node_name):
    """Reçoit le heartbeat d'un nœud"""
    NODES_STATE[node_name] = datetime.now()
    return jsonify({"status": "ok"})


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """Liste tous les nœuds avec leur état"""
    now = datetime.now()
    nodes = []

    for node_name, last_heartbeat in NODES_STATE.items():
        if now - last_heartbeat > timedelta(seconds=HEARTBEAT_TIMEOUT):
            status = "down"
        else:
            status = "up"

        nodes.append({
            "name": node_name,
            "status": status,
            "last_heartbeat": last_heartbeat.isoformat()
        })

    return jsonify({"nodes": nodes})

if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    DESIRED_STATE_FILE.touch()
    print("API SERVER")
    print(f"État: {DESIRED_STATE_FILE}")
    print()
    app.run(host='0.0.0.0', port=8081, debug=False)
