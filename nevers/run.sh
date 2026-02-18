#!/bin/bash

# Script de lancement automatique pour le scraper Nevers
# Usage: ./run.sh

echo "🏛️  SCRAPER BARREAU DE NEVERS"
echo "=============================="

# Vérifier Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
pip3 install -r requirements.txt --quiet

# Créer le dossier de sortie avec timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")
output_dir="results_${timestamp}"
mkdir -p "$output_dir"

echo "🚀 Lancement du scraping..."
echo "📁 Sortie dans: $output_dir"

# Lancer le scraper
cd "$output_dir" || exit 1
python3 ../nevers_scraper_complete.py

echo ""
echo "✅ Scraping terminé!"
echo "📁 Résultats dans: $(pwd)"
ls -la *.csv *.txt 2>/dev/null || echo "Aucun fichier généré"