#!/bin/bash

# Script de lancement pour le scraper Barreau de Périgueux
# Usage: ./run_perigueux_scraper.sh

echo "🏛️ LANCEMENT DU SCRAPER BARREAU DE PÉRIGUEUX"
echo "=============================================="

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Installation des dépendances si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install selenium webdriver-manager beautifulsoup4 requests pandas

echo "🚀 Lancement de l'extraction..."
python3 perigueux_scraper_final.py

echo "✅ Script terminé. Vérifiez les fichiers générés."