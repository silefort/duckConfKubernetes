#!/usr/bin/env python3
from flask import Flask, jsonify, request
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)

etat_desire_FILE = Path("api_server/etat_desire.txt")
NODES_STATE = {}
HEARTBEAT_TIMEOUT = 15

def read_etat_desire():
    content = etat_desire_FILE.read_text().strip()
    if not content:
        return []
    result = []
    for line in content.split('\n'):
        if not (line := line.strip()):
            continue
        name, _, node = line.partition(':')
        result.append({"name": name, "node": node or None})
    return result

def write_etat_desire(apps):
    lines = [f"{a['name']}:{a['node']}" if a.get('node') else a['name'] for a in apps]
    etat_desire_FILE.write_text('\n'.join(lines))

@app.route('/api/apps', methods=['GET'])
def get_apps():
    apps = read_etat_desire()
    node_filter = request.args.get('node')
    if node_filter:
        apps = [a for a in apps if a.get('node') == node_filter]
    return jsonify({"apps": apps})

@app.route('/api/apps', methods=['POST'])
def add_app():
    data = request.get_json()
    app_name = data.get('name')
    node_name = data.get('node')

    apps = read_etat_desire()
    new_app = {"name": app_name, "node": node_name}
    apps.append(new_app)
    write_etat_desire(apps)
    print(f"  Ajout {app_name} dans l'état désiré")
    return jsonify({"app": app_name}), 201

@app.route('/api/apps/<name>', methods=['PATCH'])
def update_app(name):
    data = request.get_json()
    new_node = data.get('node')

    apps = read_etat_desire()
    for a in apps:
        if a['name'] == name:
            a['node'] = new_node
            break
    write_etat_desire(apps)
    print(f"  Scheduling: {name} sur {new_node}")
    return jsonify({"apps": apps})

@app.route('/api/nodes/<node_name>/heartbeat', methods=['POST'])
def heartbeat(node_name):
    NODES_STATE[node_name] = datetime.now()
    return jsonify({"status": "ok"})

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    now = datetime.now()
    timeout = timedelta(seconds=HEARTBEAT_TIMEOUT)
    apps = read_etat_desire()

    nodes = []
    for name, ts in NODES_STATE.items():
        node_apps = [a['name'] for a in apps if a.get('node') == name]
        nodes.append({
            "name": name,
            "status": "down" if now - ts > timeout else "up",
            "last_heartbeat": ts.isoformat(),
            "apps": node_apps
        })

    return jsonify({"nodes": nodes})

if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    etat_desire_FILE.parent.mkdir(exist_ok=True)
    etat_desire_FILE.touch()
    print("API SERVER")
    print(f"Etat: {etat_desire_FILE}")
    print()
    app.run(host='0.0.0.0', port=8081, debug=False)
