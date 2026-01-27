# 🦆 DuckConf Kubernetes - Démonstration Push vs Pull

## 🎯 Objectif du projet

Ce projet est une démonstration visant à être jouée lors d'une conférence pour démontrer l'intérêt de l'archiecture "PULL" de Kubernetes.

1. **Mode Push (impératif)** : Un cerveau central qui envoie des commandes
2. **Mode Pull (déclaratif)** : Des agents autonomes qui convergent vers un état désiré

## 🏗️ Architectures

### Mode Push : Centralisé & Impératif

```
     ┌─────────────┐
     │ API Server  │ ← Décide et exécute TOUT
     │   (Push)    │
     └──────┬──────┘
            │ SSH (commandes)
     ┌──────┼──────┐
     ▼      ▼      ▼
  [Node1] [Node2] [Node3]
   Passifs - attendent
```

### Mode Pull : Distribué & Déclaratif

```
     ┌──────────────┐
     │  API Server  │ ← Stocke l'état désiré
     │   + State    │
     └──────┬───────┘
            ⬆           
            │ HTTP GET (polling)
     ┌──────┼────────┬─────────┐
  [Sched] [Ctrl] [Kubelet1] [Kubelet2]
  Autonomes - décident localement
```

## Utilisation

### Push Mode

```bash
cd push-mode
docker-compose up -d

# Démarrer un container
curl -X POST http://localhost:8080/container/start \
  -H "Content-Type: application/json" \
  -d '{"name": "nginx"}'

# Démarrer x containers
for i in {1..9}; do 
  curl -X POST http://localhost:8080/container/start \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"nginx$i\"}"; 
done

# Lister
curl http://localhost:8080/containers
```

### Pull Mode

```bash
cd pull-mode
docker-compose up -d

# Ajouter un container (déclaration)
curl -X POST http://localhost:8081/api/containers \
  -H "Content-Type: application/json" \
  -d '{"name": "nginx"}'

# Ajouter x containers
for i in {1..9}; do 
  curl -X POST http://localhost:8081/api/containers \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"nginx$i\"}"; 
done

# Le système va :
# 1. Scheduler l'assigne à un nœud (5s)
# 2. Kubelet le démarre (5s)

# Lister
curl http://localhost:8081/api/containers
```

## 📁 Structure du projet

```
.
├── push-mode/
│   ├── api_server.py      # Contrôleur central (fait tout)
│   ├── node_agent.py      # Agent passif (attend SSH)
│   └── docker-compose.yml # 1 API + 3 nodes
│
└── pull-mode/
    ├── api_server.py      # Stockage d'état (passif)
    ├── agent.py           # Kubelet (réconciliation)
    ├── scheduler.py       # Placement des containers
    ├── node_controller.py # Gestion des noeuds
    └── docker-compose.yml # 1 API + 3 nodes
```
## 🔥 Démonstrations clés

### 1️⃣ Réconciliation automatique

**Push Mode** :
```bash
# Corrompre l'état
docker exec push-mode-node-1-1 sh -c "echo 'fake' >> /app/node-1_running.txt"

# ❌ Rien ne se passe, l'état reste corrompu
curl http://localhost:8080/containers
# fake-container apparaît, personne ne le corrige
```

**Pull Mode** :
```bash
# Corrompre l'état
docker exec pull-mode-node-1-1 sh -c "echo 'fake' >> /app/node-1_running.txt"

# ✅ 5 secondes plus tard : auto-correction
docker-compose logs node-1
# 🔄 RECONCILIATION
# ◼ STOP: fake-container
```

### 2️⃣ Résilience aux pannes

**Push Mode** :
```bash
# Arrêter l'API
docker stop push-mode-api-1

# ❌ Plus rien ne fonctionne
# Impossible de lister, démarrer ou gérer quoi que ce soit
```

**Pull Mode** :
```bash
# Arrêter l'API
docker stop pull-mode-api-1

# ✅ Les kubelets continuent de tourner avec leur cache local
docker-compose logs node-1
# ⚠️ API inaccessible, utilisation de l'état local
# ✓ Convergé (2 containers)

# Redémarrer l'API
docker start pull-mode-api-1
# Les kubelets se re-synchronisent automatiquement
```

### 3️⃣ Auto-guérison (node failure)

**Push Mode** :
```bash
# Arrêter un nœud
docker stop push-mode-node-1-1

# ❌ Les containers sont perdus
# Aucun re-scheduling automatique
# Intervention manuelle requise
```

**Pull Mode** :
```bash
# Arrêter un nœud
docker stop pull-mode-node-1-1

# ✅ Auto-récupération complète :
# 1. Node Controller détecte la panne (15s)
# 2. Marque les containers comme non-assignés
# 3. Scheduler les réassigne automatiquement
# 4. Kubelets des nœuds sains les démarrent
# Total : ~25 secondes pour récupération complète
```
