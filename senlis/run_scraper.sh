#!/bin/bash
# Script de lancement rapide pour le scraper Senlis

echo "🚀 Lancement du scraper Barreau de Senlis"
echo "========================================"

# Vérifier si on est en mode test
if [ "$1" = "test" ]; then
    echo "🧪 Mode TEST - Extraction de 2 pages seulement"
    python3 senlis_scraper_final_improved.py test
else
    echo "🔥 Mode PRODUCTION - Extraction complète"
    echo "⚠️  Cela va prendre environ 7-10 minutes..."
    python3 senlis_scraper_final_improved.py
fi

echo ""
echo "✅ Scraping terminé !"
echo "📁 Vérifiez les fichiers générés dans ce dossier"