#!/bin/bash
# Script pour enregistrer une démo avec asciinema

set -e

# Vérifier qu'un argument (version) est fourni
if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Exemple: $0 version-0"
    echo ""
    echo "Versions disponibles:"
    ls -1 scripts/demo-*.sh 2>/dev/null | sed 's/scripts\/demo-/  - /' | sed 's/\.sh//' || echo "  Aucune démo disponible"
    exit 1
fi

VERSION=$1
SCRIPT="scripts/demo-${VERSION}.sh"
OUTPUT="recordings/${VERSION}-$(date +%Y%m%d-%H%M%S).cast"

# Vérifier que le script existe
if [ ! -f "$SCRIPT" ]; then
    echo "❌ Erreur: Le script $SCRIPT n'existe pas"
    exit 1
fi

echo "🎬 Démarrage de l'enregistrement de la démo: $VERSION"
echo "📹 Fichier de sortie: $OUTPUT"
echo ""
echo "ℹ️  Pour arrêter l'enregistrement: tapez 'exit' dans tmux"
echo ""
sleep 2

# Lancer l'enregistrement asciinema qui exécute le script
asciinema rec "$OUTPUT" -c "./$SCRIPT"

echo ""
echo "✅ Enregistrement terminé !"
echo "📁 Fichier sauvegardé: $OUTPUT"
echo ""
echo "Pour rejouer:"
echo "  asciinema play $OUTPUT"
