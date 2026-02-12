#!/usr/bin/env python3
import uuid
from flask import Flask, jsonify, request
from app.utils.ssh_utils import ssh
from app.utils.log_helper import create_logger

log = create_logger("app-manager")

app = Flask(__name__)
NODES = ["node-1", "node-2", "node-3"]
compteur_node = 0

@app.route('/app/start', methods=['POST'])
def demarrer_app():
    global compteur_node
    nom = request.json['name']
    image = request.json['image']
    node = NODES[compteur_node % len(NODES)]
    compteur_node += 1

    ssh(node, f"docker run -d --name {nom} {image}")

    log(f"Démarrage de l'application {nom} sur {node}")
    return jsonify({"app": nom, "node": node})

app.run(host='0.0.0.0', port=8080)
