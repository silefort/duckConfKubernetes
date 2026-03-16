# Démos asciinema

Ce dossier contient les scripts et enregistrements de démos pour le talk.

## Structure

```
demo/
├── scripts/              # Scripts de démo pour chaque version
│   ├── demo-version-0.sh
│   ├── demo-version-1.sh
│   └── demo-version-2.sh
├── recordings/           # Enregistrements asciinema (.cast)
├── record-demo.sh        # Script principal pour enregistrer
└── claude.md            # Documentation et contexte
```

## Utilisation

### Enregistrer une démo

```bash
cd demo
./record-demo.sh version-0
```

Le fichier `.cast` sera sauvegardé dans `recordings/` avec un timestamp.

### Rejouer une démo

```bash
asciinema play recordings/version-0-YYYYMMDD-HHMMSS.cast
```

### Rejouer avec contrôle de vitesse

```bash
# 2x plus rapide
asciinema play -s 2 recordings/version-0-*.cast

# Limiter les pauses à 2 secondes max
asciinema play -i 2 recordings/version-0-*.cast
```

## Comment ça fonctionne ?

1. **record-demo.sh** lance `asciinema rec` qui exécute le script de démo
2. Le **script de démo** (ex: `demo-version-0.sh`) :
   - Crée une session tmux
   - Envoie des commandes avec `tmux send-keys`
   - Contrôle le timing avec `sleep`
   - Attache la session tmux
3. Quand vous faites **`exit`** dans tmux, l'enregistrement s'arrête automatiquement

## Modifier une démo

Éditez le script correspondant dans `scripts/`, puis ré-enregistrez :

```bash
vim scripts/demo-version-0.sh
./record-demo.sh version-0
```

## Démos disponibles

- **version-0** : (à définir)
- **version-1** : (à définir)
- **version-2** : (à définir)
