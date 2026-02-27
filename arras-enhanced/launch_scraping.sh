#!/bin/bash
# Lanceur principal pour le scraping Arras Enhanced
# Usage: ./launch_scraping.sh

echo "🚀 LANCEMENT SCRAPER ARRAS ENHANCED"
echo "=================================="

# Vérification de Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérification des dépendances
echo "🔍 Vérification des dépendances..."
python3 -c "import requests, bs4" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚙️ Installation des dépendances..."
    pip3 install requests beautifulsoup4
fi

# Lancement du scraping
echo "🚀 Démarrage du scraping automatique..."
python3 run_arras_scraping.py

echo "✅ Script terminé. Vérifiez les fichiers générés."