#!/usr/bin/env python3
from flask import Flask, jsonify, request
from app.log_helper import create_logger

log = create_logger("api-server")

app = Flask(__name__)
compteur = 0
STATE_FILE = "/app/desired_state.csv"

@app.route('/app/start', methods=['POST'])
def demarrer_app():
    global compteur
    compteur += 1
    image = request.json['image']
    nom = f"duckconf-app-{compteur}"

    # Ajouter à l'état désiré (sans noeud)
    with open(STATE_FILE, 'a') as f:
        f.write(f"{nom},{image}\n")

    log(f"Ajout de {nom} à l'état désiré")
    return jsonify({"app": nom})

app.run(host='0.0.0.0', port=8080)
