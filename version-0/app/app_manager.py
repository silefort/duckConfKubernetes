#!/usr/bin/env python3
from flask import Flask, jsonify, request
from app.utils.ssh_utils import ssh
from app.utils.log_helper import create_logger

log = create_logger("app-manager")

app = Flask(__name__)
NODES = ["node-1", "node-2", "node-3"]
compteur_node = 0

@app.route('/app/<nom>', methods=['PUT'])
def demarrer_app(nom):
    global compteur_node
    image = request.json['image']
    node = NODES[compteur_node % len(NODES)]
    compteur_node += 1

    ssh(node, f"docker run -d --name {nom} {image}")

    log(f"Démarrage de l'application {nom} sur {node}")
    return jsonify({"app": nom, "node": node})

app.run(host='0.0.0.0', port=8080)
