#!/bin/bash
# Script de lancement automatique pour le scraper Barreau de Bayonne
# Usage: ./run_bayonne_scraper.sh

echo "🏛️  LANCEMENT SCRAPER BARREAU DE BAYONNE"
echo "======================================="

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérification de Selenium
python3 -c "import selenium" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installation de Selenium..."
    pip3 install -r requirements.txt
fi

# Lancement du scraper
echo "🚀 Démarrage du scraping..."
python3 bayonne_scraper_production.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Scraping terminé avec succès!"
    echo "📁 Consultez les fichiers générés dans ce répertoire"
else
    echo ""
    echo "❌ Erreur lors du scraping"
    echo "💡 Vérifiez que ChromeDriver est installé"
fi