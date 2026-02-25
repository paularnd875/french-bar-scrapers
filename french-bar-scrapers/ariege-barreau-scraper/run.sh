#!/bin/bash

# Script de lancement pour le scraper Barreau de l'Ariège

echo "🚀 SCRAPER BARREAU DE L'ARIÈGE"
echo "============================="

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Installation des dépendances..."
pip3 install -r requirements.txt

# Demander le mode d'exécution
echo ""
echo "Choisissez le mode d'exécution :"
echo "1) Test (20 premiers avocats)"
echo "2) Production (tous les avocats)"
echo ""
read -p "Votre choix (1 ou 2) : " choice

case $choice in
    1)
        echo "🔍 Mode TEST - Extraction de 20 avocats..."
        python3 ariege_scraper.py test
        ;;
    2)
        echo "🔍 Mode PRODUCTION - Extraction complète..."
        python3 ariege_scraper.py
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "✅ Extraction terminée ! Vérifiez les fichiers générés."