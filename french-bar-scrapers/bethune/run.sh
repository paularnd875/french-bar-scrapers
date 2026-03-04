#!/bin/bash

# Script de lancement rapide pour le scraper Béthune
# Usage: ./run.sh

echo "🚀 LANCEMENT DU SCRAPER BARREAU DE BÉTHUNE"
echo "=========================================="

# Vérifier les dépendances
echo "📦 Vérification des dépendances..."
pip3 install -r requirements.txt

# Lancer le scraper
echo "🎯 Lancement de l'extraction..."
python3 bethune_scraper_final_propre.py

echo "✅ Extraction terminée !"
echo "📁 Vérifiez les fichiers BETHUNE_FINAL_PROPRE_*.csv et *.json"