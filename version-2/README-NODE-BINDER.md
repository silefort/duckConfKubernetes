# Node Binder - Python vs Go

Ce projet propose deux implémentations du node-binder :
- **node-binder-python** : Implémentation originale en Python
- **node-binder-go** : Implémentation en Go

## Utilisation

### Via le Makefile (recommandé)

Depuis la racine du repository :

**Utiliser le node-binder Python (par défaut) :**
```bash
make cluster_start VERSION=2
# ou explicitement :
make cluster_start VERSION=2 SCHEDULER=python
```

**Utiliser le node-binder Go :**
```bash
make cluster_start VERSION=2 SCHEDULER=go
```

### Via docker-compose directement

Depuis le répertoire `version-2/` :

**Utiliser le node-binder Python :**
```bash
docker-compose --profile python up
```

**Utiliser le node-binder Go :**
```bash
docker-compose --profile go up
```

### Définir un profil par défaut

Vous pouvez créer un fichier `.env` à la racine de version-2 avec :

```bash
# Pour utiliser Python par défaut
COMPOSE_PROFILES=python

# Ou pour utiliser Go par défaut
COMPOSE_PROFILES=go
```

Ensuite, lancez simplement :
```bash
docker-compose up
```

### Différences entre les deux implémentations

Les deux implémentations ont le même comportement fonctionnel :
1. Récupèrent les applications sans nœud assigné depuis l'API server
2. Assignent ces applications aux nœuds de manière round-robin
3. Tournent en boucle toutes les 10 secondes

**Python :**
- Plus simple et facile à modifier
- Démarrage rapide
- Utilise le même Dockerfile que les autres services

**Go :**
- Plus performant
- Binaire compilé, démarrage très rapide
- Image Docker plus légère (multi-stage build)
- Typage statique

## Structure des fichiers

```
version-2/
├── app/
│   └── node-binder.py          # Node Binder Python
├── go/
│   ├── main.go               # Node Binder Go
│   ├── go.mod
│   └── Dockerfile            # Dockerfile spécifique pour Go
└── docker-compose.yml        # Configuration avec les deux profils
```
