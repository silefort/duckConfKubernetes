#!/usr/bin/env python3
from flask import Flask, jsonify, request
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)

DESIRED_STATE_FILE = Path("desired_state.txt")
NODES_STATE = {}
HEARTBEAT_TIMEOUT = 15


def read_desired_state():
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
            result.append({"name": line.strip(), "node": None})
    return result

def write_desired_state(apps):
    lines = [f"{a['name']}:{a['node']}" if a.get('node') else a['name'] for a in apps]
    DESIRED_STATE_FILE.write_text('\n'.join(lines))

@app.route('/api/apps', methods=['GET'])
def get_apps():
    apps = read_desired_state()
    node_filter = request.args.get('node')
    if node_filter:
        apps = [a['name'] for a in apps if a.get('node') == node_filter]
        return jsonify({"apps": apps})

    return jsonify({"apps": apps})


@app.route('/api/apps', methods=['POST'])
def add_app():
    data = request.get_json()
    app_name = data.get('name')
    node_name = data.get('node')

    apps = read_desired_state()
    apps.append({"name": app_name, "node": node_name})
    write_desired_state(apps)
    print(f"  Ajout: {app_name}")
    return jsonify({"apps": apps}), 201


@app.route('/api/apps/<name>', methods=['PATCH'])
def update_app(name):
    data = request.get_json()
    new_node = data.get('node')

    apps = read_desired_state()
    for a in apps:
        if a['name'] == name:
            a['node'] = new_node
            break
    write_desired_state(apps)
    print(f"  Scheduling: {name} sur {new_node}")
    return jsonify({"apps": apps})


@app.route('/api/apps/<name>', methods=['DELETE'])
def delete_app(name):
    apps = read_desired_state()
    apps = [a for a in apps if a['name'] != name]
    write_desired_state(apps)
    print(f"  Suppression: {name}")
    return jsonify({"apps": apps})


@app.route('/api/nodes/<node_name>/heartbeat', methods=['POST'])
def heartbeat(node_name):
    NODES_STATE[node_name] = datetime.now()
    return jsonify({"status": "ok"})


@app.route('/api/nodes', methods=['GET'])
def get_nodes():
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
    print(f"Etat: {DESIRED_STATE_FILE}")
    print()
    app.run(host='0.0.0.0', port=8081, debug=False)
