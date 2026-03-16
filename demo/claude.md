# Contexte : Démos asciinema pour le talk

## Objectif
Mettre en place des enregistrements de démos avec **asciinema** pour présenter les 3 versions du projet lors d'un talk.

## Structure du projet
Le projet est organisé en 3 versions progressives :

- **version-0** : Version de base (à détailler)
- **version-1** : Version intermédiaire (à détailler)
- **version-2** : Version avancée avec node-binder (Python et Go)

Chaque version démontre une évolution du système de déploiement d'applications sur des nœuds.

## Asciinema - Qu'est-ce que c'est ?

**asciinema** est un outil qui permet d'enregistrer et de rejouer des sessions terminal. Contrairement à une vidéo classique, les enregistrements sont en mode texte, ce qui permet :
- Des fichiers très légers (texte au lieu de vidéo)
- De copier-coller le texte depuis la démo
- De mettre en pause et d'avancer/reculer facilement
- De partager facilement les démos en ligne

## Plan d'action

### Étape 1 : Installation et découverte d'asciinema ✅
- [x] Installer asciinema (v2.4.0 déjà installé ✓)
- [x] Comprendre les commandes de base
- [x] Découvrir l'interaction avec tmux

### Étape 2 : Préparer les scénarios de démo
- [ ] Définir ce qu'on veut montrer dans version-0
- [ ] Définir ce qu'on veut montrer dans version-1
- [ ] Définir ce qu'on veut montrer dans version-2

### Étape 3 : Organiser le dossier demo ✅
- [x] Créer une structure de fichiers (scripts/, recordings/)
- [x] Créer un script wrapper pour enregistrer (record-demo.sh)
- [x] Créer un premier script de test (demo-version-0.sh)

### Étape 4 : Enregistrer les démos
- [ ] Enregistrer la démo version-0
- [ ] Enregistrer la démo version-1
- [ ] Enregistrer la démo version-2

### Étape 5 : Validation et partage
- [ ] Relire et valider les démos
- [ ] Documenter comment rejouer les démos
- [ ] Configurer asciinema.org (optionnel)

## Notes techniques
- OS : Linux 6.14.0-37-generic
- Projet : Git repository avec 3 dossiers version-*/
- Makefile à la racine pour orchestrer les différentes versions

## Commandes asciinema essentielles

### Enregistrer une session
```bash
asciinema rec demo-name.cast
# Faire vos commandes...
# Ctrl+D ou taper 'exit' pour arrêter l'enregistrement
```

### Rejouer un enregistrement
```bash
asciinema play demo-name.cast
```

### Rejouer avec contrôle de vitesse
```bash
asciinema play -s 2 demo-name.cast    # 2x plus rapide
asciinema play -s 0.5 demo-name.cast  # 2x plus lent
```

### Limiter la vitesse maximale (éviter les longues pauses)
```bash
asciinema play -i 2 demo-name.cast    # max 2 secondes entre chaque commande
```

### Uploader sur asciinema.org (optionnel)
```bash
asciinema upload demo-name.cast
```

## Structure créée

```
demo/
├── scripts/              # Scripts de démo
│   └── demo-version-0.sh (test simple)
├── recordings/           # Fichiers .cast enregistrés
├── record-demo.sh        # Script principal
├── README.md            # Guide d'utilisation
└── claude.md            # Ce fichier
```

## Découverte importante : tmux + asciinema

**Problème** : On ne peut pas lancer asciinema dans un pane/window tmux et enregistrer un autre pane.

**Solution retenue** :
- Lancer `asciinema rec` qui exécute un script
- Le script crée une session tmux et envoie des commandes avec `tmux send-keys`
- Tout est enregistré car tmux tourne DANS asciinema

## Prochaines étapes
1. Tester le script de base : `cd demo && ./record-demo.sh version-0`
2. Définir le scénario de chaque version
3. Implémenter les vrais scripts de démo
