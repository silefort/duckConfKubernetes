# Demo-1 — Synthèse d'architecture

## Schéma

```
                      make start_app <image>
                      ─────────────────────►  POST /app/start
                                              { "image": "nginx" }
                                                       │
┌──────────────────── HÔTE (podman) ─────────────────┼──────────────────────┐
│                                                     ▼                     │
│           ┌──────────────────────────────────────────────────┐            │
│           │               api-server  :8080                  │            │
│           │                                                  │            │
│           │   POST /app/start                                │            │
│           │     1. choisir_node()  →  round-robin            │            │
│           │            compteur % 3  →  node-{1|2|3}         │            │
│           │     2. nom  = "duckconf-{node}-app-{N}"          │            │
│           │     3. ssh(node, "docker run -d --name {nom} …") │            │
│           │     4. return { "app": nom, "node": node }       │            │
│           └───────┬──────────┬──────────┬───────────────────┘            │
│                   │          │          │                                 │
│               SSH │      SSH │      SSH │   ◄─ 1 seul par requête        │
│         (paramiko · root:root)         │      sélectionné par            │
│                   ▼          ▼         ▼      round-robin                │
│           ┌───────────┐ ┌─────────┐ ┌───────────┐                       │
│           │  node-1   │ │ node-2  │ │  node-3   │                       │
│           │           │ │         │ │           │                       │
│           │  sshd     │ │  sshd   │ │  sshd     │                       │
│           │    │      │ │    │    │ │    │      │                       │
│           │    ▼      │ │    ▼    │ │    ▼      │                       │
│           │ docker-   │ │ docker- │ │ docker-   │   ◄─ intercepte       │
│           │ wrapper   │ │ wrapper │ │ wrapper   │      "docker run"     │
│           │ +--label  │ │ +--label│ │ +--label  │      → ajoute         │
│           │ node=X    │ │ node=X  │ │ node=X    │        --label        │
│           └─────┬─────┘ └────┬────┘ └─────┬─────┘       node=node-X    │
│                 │            │            │                              │
│                 └────────────┼────────────┘                              │
│                              │                                           │
│               podman.sock (monté depuis l'hôte vers chaque node)        │
│                              │                                           │
│                              ▼                                           │
│             ┌──────────────────────────────────────┐                     │
│             │         containers (apps)            │                     │
│             │                                      │                     │
│             │  duckconf-node-1-app-1  [label: n-1] │                     │
│             │  duckconf-node-2-app-2  [label: n-2] │  ◄─ tous sur le    │
│             │  duckconf-node-3-app-3  [label: n-3] │     même hôte,    │
│             │  duckconf-node-1-app-4  [label: n-1] │     séparés       │
│             │  ...                                 │     logiquement   │
│             └──────────────────────────────────────┘     par labels    │
│                                                                         │
│  ── Autres flux ────────────────────────────────────────────────────    │
│  make ps            → docker ps --filter label=node=X                   │
│  make stop_node X   → docker pause node-X  (simule une panne de nœud)  │
│  make kill_app      → docker exec node-X  docker rm -f <app>            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Points clés

### Tout tourne sur un même hôte podman

Les `node-*` ne sont pas des VMs, ce sont des containers qui jouent le rôle de nœuds via SSH.
Le `docker run` lancé par SSH depuis `node-2` fait donc tourner le container sur le même hôte — pas "dans" node-2.

### Le `docker-wrapper.sh` — isolation logique par labels

Il intercepte chaque `docker run` sur un nœud pour coller automatiquement le label `node=node-X`.
C'est ce qui permet de savoir logiquement à quel nœud appartient chaque app.
Le même mécanisme est utilisé pour filtrer avec `docker ps --filter label=node=X`.

### Le `podman.sock` est partagé

Il est monté depuis l'hôte vers chaque container nœud.
C'est ce qui permet aux nœuds de créer des containers "frères" sur le même daemon, sans avoir besoin de leur propre runtime.

### Scheduling — round-robin naïf

Un simple `compteur % 3` détermine le nœud cible.
Pas de logique de ressource, pas d'état observé.
C'est le mode "push" au sens strict : le contrôleur décide seul où placer les charges.

### Unique endpoint exposé vers l'extérieur

`POST /app/start` est le seul endpoint HTTP.
Le reste (`ps`, `stop_node`, `kill_app`) passe directement par des commandes `docker` sur l'hôte via le Makefile — pas par l'API.

---

# Demo-2 — Synthèse d'architecture

## Schéma

```
                        make start_app <image>
                        ─────────────────────►  POST /app/start
                                                 { "image": "nginx" }
                                                          │
┌────────────────── HÔTE (podman) ────────────────────────┼─────────────┐
│                                                          ▼             │
│  ┌──────────── container api-server (2 processus) ────────────────┐   │
│  │                                                                  │   │
│  │  ┌────────────┐  écrit  ┌──────────────┐  lit  ┌────────────┐  │   │
│  │  │ Flask:8080 │ ──────► │ desired_     │ ────► │ boucle_de  │  │   │
│  │  │            │         │ state.csv    │       │ contrôle   │  │   │
│  │  │ POST /app/ │         │              │       │ (loop 10s) │  │   │
│  │  │ start      │         │ app-1,nginx  │       │            │  │   │
│  │  │  nom=app-{N│         │ app-2,nginx  │       │ ① CAPTEUR  │  │   │
│  │  │  ret {app} │         │ ...          │       │ ② CONSIGNE │  │   │
│  │  └────────────┘         └──────────────┘       │ ③ COMPARER │  │   │
│  │                                                │ ④ AGIR     │  │   │
│  │                                                └─────┬──────┘  │   │
│  └──────────────────────────────────────────────────────┼─────────┘   │
│                                                         │             │
│                     SSH (paramiko · root:root)           │             │
│                ┌──────────┬──────────┬───────────────────┘             │
│                ▼          ▼          ▼                                 │
│         ┌──────────┐ ┌─────────┐ ┌──────────┐                        │
│         │  node-1  │ │ node-2  │ │  node-3  │                        │
│         │  sshd    │ │  sshd   │ │  sshd    │                        │
│         │  docker  │ │  docker │ │  docker  │                        │
│         │  wrapper │ │  wrapper│ │  wrapper │                        │
│         └────┬─────┘ └────┬────┘ └────┬─────┘                        │
│              │            │           │                                │
│              └────────────┼───────────┘  podman.sock                  │
│                           ▼                                            │
│              ┌──────────────────────────────────┐                      │
│              │       containers (apps)          │                      │
│              │  duckconf-app-1  [label: n-1]    │                      │
│              │  duckconf-app-2  [label: n-2]    │                      │
│              │  duckconf-app-3  [label: n-3]    │                      │
│              │  ...                             │                      │
│              └──────────────────────────────────┘                      │
│                                                                        │
│  ── Boucle de contrôle (détail) ──────────────────────────────────    │
│  ① CAPTEUR     → SSH vers chaque nœud → docker ps → état observé     │
│  ② CONSIGNE    → lire desired_state.csv → état désiré                │
│  ③ COMPARATEUR → à_demarrer = désiré − observé                       │
│                   à_arrêter  = observé − désiré                       │
│  ④ ACTIONNEUR  → SSH vers nœud (round-robin) → docker run / stop    │
│  ─── puis sleep(10s) → retour à ① ────────────────────────────────   │
│                                                                        │
│  ── Autres flux ──────────────────────────────────────────────────    │
│  make ps          → docker ps --filter label=node=X                    │
│  make stop_node X → docker pause node-X  (simule panne de nœud)       │
│  make kill_app    → docker exec node-X  docker rm -f <app>             │
└────────────────────────────────────────────────────────────────────────┘
```

## Ce qui change par rapport à demo-1

### Découpage déclaratif via le CSV

L'API ne fait plus de SSH elle-même.
Elle écrit juste l'intent dans `desired_state.csv`.
C'est la `boucle_de_controle` qui décide quand et où agir — de manière asynchrone.
Le CSV est le seul canal de communication entre les deux processus.

### Auto-guérison

Si un container claque (`make kill_app`), la prochaine itération de la boucle le détecte :
le capteur observe qu'il est absent, le comparateur constate l'écart avec l'état désiré,
l'actionneur le relance.
Demo-1 n'avait pas ça.

### Le docker-wrapper est plus malin

Il fait un `docker rm -f` du container existant avant de relancer un `docker run` avec le même nom.
Ça permet à la boucle d'être idempotente : elle peut appeler `docker run` même si un container zombie existe.

### Deux processus, un seul container

`api_server` et `boucle_de_controle` tournent dans le même container via un `&` dans la commande du docker-compose.
Le fichier CSV est monté sur le même volume — pas besoin de réseau entre eux.

---

# Demo-3 — Synthèse d'architecture

## Schéma

```
                        make app_start <name> <image>
                        ─────────────────────────────►  POST /app/start
                                                        {"name":"…","image":"…"}
                                                                 │
┌─────────────────── HÔTE (podman) ──────────────────────────────┼──────┐
│                                                                 ▼      │
│  ┌─────────────────── CONTROL PLANE ──────────────────────────────┐   │
│  │                                                                  │   │
│  │            ┌────────────────────────────────┐                   │   │
│  │            │        api-server :8080        │                   │   │
│  │            │                                │                   │   │
│  │            │  POST /app/start               │                   │   │
│  │            │  GET  /apps?nodeName=X         │                   │   │
│  │            │  PUT  /app/<name>              │                   │   │
│  │            │  PUT  /node/<name>/heartbeat   │                   │   │
│  │            │  GET  /nodes                   │                   │   │
│  │            │  [state.csv]  [nodes.json]     │                   │   │
│  │            └──────┬──────────────┬─────────┘                   │   │
│  │                   │              │                               │   │
│  │              HTTP │        HTTP  │  ◄─ tous les composants      │   │
│  │                   ▼              ▼     pollent api-server       │   │
│  │    ┌──────────────┐   ┌────────────────────┐                   │   │
│  │    │  scheduler   │   │  node-controller   │                   │   │
│  │    │              │   │                    │                   │   │
│  │    │  GET /apps   │   │  GET /nodes        │                   │   │
│  │    │  ?nodeName=  │   │  GET /apps?nodeName│                   │   │
│  │    │  PUT /app/N  │   │  PUT /app/N {:""}  │                   │   │
│  │    │   {node: X}  │   │  timeout: 20s      │                   │   │
│  │    │  (loop 10s)  │   │  (loop 10s)        │                   │   │
│  │    └──────────────┘   └────────────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────── DATA PLANE ─────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                 │    │
│  │  │  node-1  │    │  node-2  │    │  node-3  │                 │    │
│  │  │          │    │          │    │          │                 │    │
│  │  │ app-ctrl │    │ app-ctrl │    │ app-ctrl │                 │    │
│  │  │ (loop 10s│    │ (loop 10s│    │ (loop 10s│                 │    │
│  │  │          │    │          │    │          │                 │    │
│  │  │ ┌──────┐ │    │ ┌──────┐ │    │ ┌──────┐ │                 │    │
│  │  │ │ apps │ │    │ │ apps │ │    │ │ apps │ │                 │    │
│  │  │ └──────┘ │    │ └──────┘ │    │ └──────┘ │                 │    │
│  │  └──────────┘    └──────────┘    └──────────┘                 │    │
│  │  (containers via podman.sock partagé)                           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ── app-controller (sur chaque nœud, loop 10s) ──────────────────── │
│  ① PUT /node/{name}/heartbeat    → signaler liveness                  │
│  ② docker ps  (local)            → observer l'état                    │
│  ③ GET /apps?nodeName=<self>     → lire l'état désiré                │
│  ④ docker run / rm  (local)      → réconciler                        │
│                                                                         │
│  ── Auto-guérison (panne de nœud) ──────────────────────────────── │
│  node-X muet → timeout 20s                                              │
│    → node-controller : PUT /app/N {node:""}  (unschedule)              │
│    → scheduler : PUT /app/N {node: Y}        (reschedule)              │
│    → app-ctrl sur Y : docker run                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Ce qui change par rapport à demo-2

### Plus de SSH

Les app-controllers tournent directement sur les nœuds, ils font `docker ps` en local via subprocess.
Toute la communication entre composants est HTTP.

### Séparation des responsabilités

Trois boucles de contrôle distinctes au lieu d'une seule :
le `scheduler` assigne, le `node-controller` surveille la santé, l'`app-controller` réconcilie.
Chacun fait une chose.

### Topologie étoile centrée sur api-server

Aucun composant ne parle à un autre directement.
Tout passe par l'api-server — exactement comme dans Kubernetes avec etcd.

### Deux fichiers d'état

`state.csv` pour les apps (quelle image, sur quel nœud), `nodes.json` pour les heartbeats.
Les deux gérés exclusivement par l'api-server.

### Le scheduling est découpé de l'action

L'utilisateur soumet une app sans nœud.
Le scheduler l'assigne.
L'app-controller la lance.
Trois étapes, trois composants, trois loops à 10s.

### Auto-guérison via heartbeats

Les nœuds signalent leur liveness régulièrement.
Si un nœud disparaît, le node-controller le détecte après 20s, unschedule ses apps,
et le scheduler les réassigne ailleurs.
Demo-2 n'avait rien de tel.
