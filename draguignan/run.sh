#!/bin/bash

# Script de lancement facile pour le scraper Draguignan
# Usage: ./run.sh [test|production] [--headless]

echo "🚀 Lancement du scraper Barreau de Draguignan"
echo "=============================================="

# Installation des dépendances si nécessaire
if ! pip3 show selenium >/dev/null 2>&1; then
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt
fi

# Mode par défaut
MODE="test"
HEADLESS=""

# Parse des arguments
if [ "$1" == "production" ]; then
    MODE="production"
    echo "⚡ Mode PRODUCTION - Extraction complète (toutes lettres A-Z)"
elif [ "$1" == "test" ]; then
    echo "🧪 Mode TEST - Extraction partielle (lettres A-B)"
fi

if [ "$2" == "--headless" ] || [ "$1" == "--headless" ]; then
    HEADLESS="--headless"
    echo "👤 Mode headless activé"
fi

echo ""
echo "▶️  Démarrage du scraping..."

# Lancement du script
python3 draguignan_scraper.py $MODE $HEADLESS

echo ""
echo "✅ Scraping terminé ! Vérifiez les fichiers générés."
echo "📁 Fichiers CSV, JSON, emails et rapport créés automatiquement."