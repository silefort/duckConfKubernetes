#!/usr/bin/env python3
import json
from flask import Flask, jsonify, request
from app.utils.log_helper import create_logger

log = create_logger("api-server")

app = Flask(__name__)
APPS_FILE = "/app/apps.json"

@app.route('/app/<name>', methods=['PUT'])
def update_app(name):
    image = request.json['image']

    with open(APPS_FILE, 'r') as f:
        apps = json.load(f)
    apps[name] = {"image": image}
    with open(APPS_FILE, 'w') as f:
        json.dump(apps, f, indent=2)

    log(f"{name} mis à jour dans l'état désiré")
    return jsonify({"app": name})

app.run(host='0.0.0.0', port=8080)
