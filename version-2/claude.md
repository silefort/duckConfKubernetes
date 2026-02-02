# duckConfKubernetes - Demo 3

## Description du projet

Démo d'orchestrateur de containers style Kubernetes pour un talk de conférence (DuckConf).

Le code est volontairement simple et lisible, conçu à des fins pédagogiques. Il n'y a pas de gestion d'edge cases - l'objectif est de montrer les concepts fondamentaux d'un orchestrateur.

## Architecture

Le projet suit une architecture inspirée de Kubernetes avec les composants suivants :

### Composants principaux

- **API Server** (`app/api_server.py`) : Source de vérité centrale qui expose des endpoints REST pour gérer l'état désiré du cluster
- **App Controller** (`app/app_controller.py`) : Boucle de contrôle exécutée sur chaque nœud pour réconcilier l'état observé avec l'état désiré
- **Scheduler** (`app/scheduler.py`) : Service responsable de l'assignation des applications aux nœuds (stratégie round-robin)
- **apps.json** : Fichier de stockage de l'état désiré (équivalent simplifié d'etcd dans Kubernetes)

### Fichiers utilitaires

- `app/shell_utils.py` : Fonctions pour l'exécution de commandes shell
- `app/http_utils.py` : Fonctions pour les requêtes HTTP
- `app/log_helper.py` : Utilitaires de logging avec préfixes pour faciliter le débogage

## Boucle de contrôle

Le système suit le pattern de boucle de contrôle de Kubernetes :

```
Observer (docker ps) → Comparer (désiré vs observé) → Agir (docker run/rm)
```

1. **Observer** : Récupération de l'état actuel des containers via `docker ps`
2. **Comparer** : Comparaison entre l'état observé et l'état désiré récupéré de l'API Server
3. **Agir** : Exécution des actions nécessaires (`docker run` pour créer, `docker rm` pour supprimer)

Cette boucle s'exécute en continu sur chaque nœud pour maintenir le cluster dans l'état désiré.

## Commandes principales

```bash
# Construire les images Docker
make build

# Démarrer le cluster
make cluster_start

# Arrêter le cluster
make cluster_stop
```

## Notes

Ce projet est une démo simplifiée à des fins d'illustration. Pour un orchestrateur en production, de nombreux aspects devraient être ajoutés (gestion d'erreurs robuste, sécurité, haute disponibilité, etc.).
