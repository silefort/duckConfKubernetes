#!/usr/bin/env python3
from flask import Flask, jsonify, request
from pathlib import Path
from datetime import datetime, timedelta

app = Flask(__name__)

etat_desire_FILE = Path("api_server/etat_desire.txt")

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
