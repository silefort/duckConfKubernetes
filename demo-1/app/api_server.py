#!/usr/bin/env python3
from flask import Flask, jsonify, request
from app.ssh_utils import ssh

app = Flask(__name__)
NODES = ["node-1", "node-2", "node-3"]
compteur = 0

def choisir_node():
    global compteur
    node = NODES[compteur % len(NODES)]
    compteur += 1
    return node

@app.route('/app/start', methods=['POST'])
def demarrer_app():
    image = request.json['image']
    node = choisir_node()

    nom = f"duckconf-{node}-app-{compteur}"
    ssh(node, f"docker run -d --name {nom} {image}")

    print(f" démarrage de l'application {nom} sur le {node}")
    return jsonify({"app": nom, "node": node})

app.run(host='0.0.0.0', port=8080)
