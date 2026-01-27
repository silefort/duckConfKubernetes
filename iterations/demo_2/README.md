# Pull Mode - Contrôleur Monolithique

## 🎯 Objectif

Version simplifiée du pull-mode où **toute la logique est dans un seul fichier** pour illustrer clairement la boucle de contrôle et les patterns Kubernetes.

## 📝 Architecture

```
┌──────────────────────────────────────────────────┐
│         app_controller.py                        │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  API REST (Flask)                          │  │
│  │  POST /api/containers                      │  │
│  │  GET /api/containers                       │  │
│  │  DELETE /api/containers/<n>               │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  BOUCLE DE CONTRÔLE (while True)           │  │
│  │                                            │  │
│  │  1. get_current_state()                    │  │
│  │     → SSH sur chaque noeud                 │  │
│  │     → Récupère les containers en cours     │  │
│  │     → Détecte les noeuds down              │  │
│  │                                            │  │
│  │  2. get_desired_state()                    │  │
│  │     → Lit desired_state.txt                │  │
│  │                                            │  │
│  │  3. cleanup_dead_nodes()                   │  │
│  │     → Retire assignations des noeuds down  │  │
│  │                                            │  │
│  │  4. schedule()                             │  │
│  │     → Assigne containers aux noeuds        │  │
│  │                                            │  │
│  │  5. reconcile()                            │  │
│  │     → Compare current vs desired           │  │
│  │     → SSH pour start/stop containers       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
                       │
                       │ SSH
            ───────────┼───────────
            │          │          │
        ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
        │node-1 │  │node-2 │  │node-3 │
        └───────┘  └───────┘  └───────┘
```

## 🚀 Utilisation

### Démarrer le système

```bash
# Démarrer avec docker-compose
docker-compose up -d

# Ou directement
python app_controller.py
```

### Ajouter un container

```bash
curl -X POST http://localhost:8080/api/containers \
  -H "Content-Type: application/json" \
  -d '{"name": "nginx"}'
```

### Lister les containers

```bash
curl http://localhost:8080/api/containers
```

### Supprimer un container

```bash
curl -X DELETE http://localhost:8080/api/containers/nginx
```

## 🔬 Observer la boucle de contrôle

Les logs montrent clairement les 5 étapes à chaque tick (5 secondes) :

```
======================================================================
TICK - 14:23:15
======================================================================

1️⃣  OBSERVER l'état actuel (SSH sur les noeuds)
  ✓ node-1: nginx
  ✓ node-2: redis
  - node-3: vide
   → 2 containers tournent sur 3 noeuds

2️⃣  RÉCUPÉRER l'état désiré
   → 3 containers déclarés

3️⃣  CLEANUP des noeuds morts

4️⃣  SCHEDULER les containers non assignés
  📍 SCHEDULE: mysql → node-3

5️⃣  RÉCONCILIER (diff + actions)
  ▶ START: mysql sur node-3

✅ Convergé
```

## 💡 Démonstrations

### Auto-réparation

```bash
# 1. Ajouter un container
curl -X POST http://localhost:8080/api/containers \
  -H "Content-Type: application/json" \
  -d '{"name": "nginx"}'

# 2. Corrompre l'état sur un noeud
docker exec pull-mode-node-1-1 sh -c "echo 'intruder' >> /app/nodes/node-1_running.txt"

# 3. Observer les logs (dans les 5 secondes)
# ◼ STOP: intruder sur node-1
```

### Gestion de panne de noeud

```bash
# 1. Démarrer quelques containers
for i in {1..6}; do 
  curl -X POST http://localhost:8080/api/containers \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"app$i\"}"; 
done

# 2. Arrêter un noeud
docker stop pull-mode-node-1-1

# 3. Observer les logs
# ⚠️  node-1: indisponible
# 💀 CLEANUP: app1 (node node-1 down)
# 💀 CLEANUP: app4 (node node-1 down)
# 📍 SCHEDULE: app1 → node-2
# 📍 SCHEDULE: app4 → node-3
# ▶ START: app1 sur node-2
# ▶ START: app4 sur node-3
```

## 🔍 Code Structure

### Fonctions principales

```python
get_current_state()
  → SSH sur chaque noeud
  → Retourne (containers_actuels, noeuds_disponibles)

get_desired_state()
  → Lit desired_state.txt
  → Retourne liste de containers

cleanup_dead_nodes(containers, available_nodes)
  → Retire assignations des noeuds down

schedule(containers, available_nodes)
  → Assigne containers non assignés (round-robin)

reconcile(current, desired)
  → Compare état actuel vs désiré
  → SSH pour start/stop
```

### Boucle de contrôle

```python
while True:
    # 1. Observer
    current, available_nodes = get_current_state()
    
    # 2. Récupérer désiré
    desired = get_desired_state()
    
    # 3. Cleanup
    cleanup_dead_nodes(desired, available_nodes)
    
    # 4. Scheduler
    schedule(desired, available_nodes)
    
    # 5. Réconcilier
    reconcile(current, desired)
    
    time.sleep(5)
```

## ✅ Avantages de cette approche monolithique

1. **Pédagogique** : Tout le code au même endroit
2. **Clair** : La boucle de contrôle est évidente
3. **Simple** : Pas de communication inter-processus
4. **Fonctionnel** : Démontre tous les patterns

## 🆚 Différences avec le pull-mode distribué

| Aspect | Pull-Mode Distribué | Ce contrôleur |
|--------|---------------------|---------------|
| Processus | 4+ (api, scheduler, agents) | 1 seul |
| Communication | HTTP entre agents | Fonctions internes |
| Complexité | Production-ready | Pédagogique |
| Scalabilité | ✅ Excellent | ⚠️ Limité |
| Clarté pédagogique | ⚠️ Dispersé | ✅ Tout visible |

## 🎓 Patterns illustrés

✅ **Boucle de contrôle** : `while True` visible  
✅ **Déclaratif** : `desired_state.txt`  
✅ **Level trigger** : Observe état complet à chaque tick  
✅ **Auto-réparation** : Détection et correction automatiques  
✅ **Scheduler** : Fonction `schedule()`  
✅ **Réconciliation** : Fonction `reconcile()`

## 🔧 Configuration

### Docker Compose

Utilise le même `docker-compose.yml` que le pull-mode classique mais avec un seul contrôleur.

### Variables

```python
NODES = ["node-1", "node-2", "node-3"]  # Noeuds disponibles
DESIRED_STATE_FILE = "desired_state.txt"  # État désiré
```

## 📊 Flux d'exécution

```
Utilisateur
    │
    │ POST /api/containers {"name": "nginx"}
    ▼
┌──────────────┐
│ Flask API    │
│ (thread)     │
└──────┬───────┘
       │ Écrit desired_state.txt
       │
┌──────▼──────────────────────────────────┐
│ Control Loop (thread)                   │
│                                         │
│ while True:                             │
│   current = SSH tous les noeuds         │
│   desired = lit fichier                 │
│   cleanup noeuds down                   │
│   schedule non assignés                 │
│   reconcile (SSH start/stop)            │
│   sleep(5)                              │
└─────────────────────────────────────────┘
```

## 💡 Cas d'usage pédagogique

Utilisez ce code pour :
- Expliquer la boucle de contrôle sans la complexité distribuée
- Montrer comment un seul processus peut gérer tout
- Illustrer le level-triggering
- Démontrer l'auto-réparation simplement

Puis passez au pull-mode distribué pour montrer la scalabilité !
