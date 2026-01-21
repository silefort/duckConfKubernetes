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

@app.route('/app/start', methods=['POST'])
def start_app():
    """Demarre une app sur un noeud"""
    name = request.get_json()['name']
    node = selectionner_noeud()
    executer_ssh(node, f"echo '{name}' >> /app/nodes/{node}_running.txt")
    print(f"App {name} demarrée sur {node}")
    return jsonify({"status": "started", "app": name, "node": node}), 201

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
