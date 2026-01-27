#!/usr/bin/env python3
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*TripleDES.*')

from flask import Flask, jsonify, request
import paramiko
import time
import threading
from pathlib import Path

app = Flask(__name__)

NODES = ["node-1", "node-2", "node-3"]
ETAT_DESIRE_FILE = Path("etat_desire.txt")


def ssh_exec(node, cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(node, port=22, username="root", password="root", timeout=3)
        _, stdout, _ = ssh.exec_command(cmd)
        result = stdout.read().decode().strip()
        ssh.close()
        return result
    except:
        return None


def start_app(app_name, node):
    """Démarre une app sur un noeud (écrit dans running.txt)"""
    ssh_exec(node, f"echo '{app_name}' >> /app/nodes/{node}_running.txt")
    print(f"  Démarre: {app_name} sur {node}", flush=True)


def stop_app(app_name, node):
    """Arrête une app sur un noeud (supprime du running.txt)"""
    ssh_exec(node, f"sed -i '/{app_name}/d' /app/nodes/{node}_running.txt")
    print(f"  Arrête: {app_name} sur {node}", flush=True)


def schedule(desire):
    """Assigne les apps sans noeud (écrit dans etat_desire.txt)"""
    noeuds_up = []
    for node in NODES:
        if ssh_exec(node, "echo ok") is not None:
            noeuds_up.append(node)
    
    non_assignes = [a for a in desire if not a.get('node')]
    
    if non_assignes and noeuds_up:
        compteurs = {n: 0 for n in noeuds_up}
        for a in desire:
            if a.get('node') in noeuds_up:
                compteurs[a['node']] += 1
        
        for app in non_assignes:
            noeud = min(noeuds_up, key=lambda n: compteurs[n])
            app['node'] = noeud
            compteurs[noeud] += 1
            print(f"  Schedule: {app['name']} → {noeud}", flush=True)


def observe():
    """Liste les apps qui tournent (lit les fichiers running.txt)"""
    running = []
    for node in NODES:
        result = ssh_exec(node, f"cat /app/nodes/{node}_running.txt 2>/dev/null || echo ''")
        if result:
            for app in result.split('\n'):
                if app:
                    running.append({"name": app, "node": node})
    return running


def evict():
    """Éviction: retire des noeuds down les apps de desire et running"""
    desire = etat_desire()
    
    for node in NODES:
        if ssh_exec(node, "echo ok") is None:
            print(f"  Noeud {node} down", flush=True)
            
            # Retirer de l'état désiré
            for app in desire:
                if app.get('node') == node:
                    print(f"  Eviction: {app['name']} de {node}", flush=True)
                    app['node'] = None
            
            # Nettoyer le fichier running (au cas où)
            ssh_exec(node, f"rm -f /app/nodes/{node}_running.txt")
    
    ecrit_etat_desire(desire)


def etat_desire():
    """Lit l'état désiré"""
    if not ETAT_DESIRE_FILE.exists():
        return []
    apps = []
    for line in ETAT_DESIRE_FILE.read_text().strip().split('\n'):
        if not line:
            continue
        if ':' in line:
            name, node = line.split(':')
            apps.append({"name": name, "node": node})
        else:
            apps.append({"name": line, "node": None})
    return apps


def ecrit_etat_desire(apps):
    """Écrit l'état désiré"""
    lines = [f"{a['name']}:{a['node']}" if a.get('node') else a['name'] for a in apps]
    ETAT_DESIRE_FILE.write_text('\n'.join(lines))


def reconcilie():
    """Réconcilie: evict → schedule → start/stop"""
    
    # 1. Eviction des noeuds down
    evict()
    
    # 2. Récupérer l'état
    desire = etat_desire()
    running = observe()
    
    # 3. Scheduler les apps non assignées
    schedule(desire)
    ecrit_etat_desire(desire)
    
    # 4. Comparer et agir
    running_par_noeud = {}
    for a in running:
        node = a['node']
        if node not in running_par_noeud:
            running_par_noeud[node] = set()
        running_par_noeud[node].add(a['name'])
    
    desire_par_noeud = {}
    for a in desire:
        if a.get('node'):
            node = a['node']
            if node not in desire_par_noeud:
                desire_par_noeud[node] = set()
            desire_par_noeud[node].add(a['name'])
    
    tous_noeuds = set(running_par_noeud.keys()) | set(desire_par_noeud.keys())
    
    actions = False
    for node in tous_noeuds:
        running_noeud = running_par_noeud.get(node, set())
        desire_noeud = desire_par_noeud.get(node, set())
        
        a_demarrer = desire_noeud - running_noeud
        a_stopper = running_noeud - desire_noeud
        
        for app in a_stopper:
            stop_app(app, node)
            actions = True
        
        for app in a_demarrer:
            start_app(app, node)
            actions = True
    
    if not actions:
        print("  Rien à faire", flush=True)


@app.route('/api/apps', methods=['GET'])
def get_apps():
    apps = etat_desire()
    return jsonify({"apps": apps})


@app.route('/api/apps', methods=['POST'])
def add_app():
    name = request.get_json()['name']
    apps = etat_desire()
    
    if any(a['name'] == name for a in apps):
        return jsonify({"error": "exists"}), 409
    
    apps.append({"name": name, "node": None})
    ecrit_etat_desire(apps)
    print(f"\nAjout app: {name}", flush=True)
    return jsonify({"app": {"name": name}}), 201


@app.route('/api/apps/<n>', methods=['DELETE'])
def delete_app(name):
    apps = etat_desire()
    apps = [a for a in apps if a['name'] != name]
    ecrit_etat_desire(apps)
    print(f"\nSuppression app: {name}", flush=True)
    return jsonify({"status": "deleted"})


def run_api():
    import sys
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)


if __name__ == "__main__":
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    ETAT_DESIRE_FILE.touch()
    
    print("CONTROLEUR PULL MODE", flush=True)
    print(f"Etat désiré: {ETAT_DESIRE_FILE}", flush=True)
    print(f"Noeuds: {', '.join(NODES)}", flush=True)
    print(flush=True)
    
    threading.Thread(target=run_api, daemon=True).start()
    time.sleep(1)
    
    while True:
        # Boucle de contrôle
        reconcilie()
        time.sleep(5)