#!/bin/bash

# Script de lancement du scraper Barreau de Vannes
# Usage: ./run_scraper.sh

echo "🚀 Lancement du scraper Barreau de Vannes"
echo "========================================"

# Vérifier que Python3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Erreur: python3 n'est pas installé"
    exit 1
fi

# Vérifier que pip est installé  
if ! command -v pip3 &> /dev/null; then
    echo "❌ Erreur: pip3 n'est pas installé"
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Installation des dépendances..."
pip3 install -r requirements.txt

# Vérifier que ChromeDriver est disponible
if ! command -v chromedriver &> /dev/null; then
    echo "⚠️  ChromeDriver non trouvé dans PATH"
    echo "💡 Installation recommandée:"
    echo "   - macOS: brew install chromedriver"
    echo "   - Linux: sudo apt install chromium-chromedriver"
    echo "   - Ou télécharger depuis: https://chromedriver.chromium.org/"
    echo ""
    echo "⏳ Tentative d'exécution quand même..."
fi

# Créer un dossier pour les résultats avec timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="results_$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"

echo "📂 Répertoire de sortie: $OUTPUT_DIR"
echo ""

# Lancer le scraper
echo "🔄 Démarrage de l'extraction..."
cd "$OUTPUT_DIR"
python3 ../vannes_scraper_final.py

# Vérifier le résultat
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Extraction terminée avec succès!"
    echo "📁 Fichiers générés dans: $OUTPUT_DIR"
    echo ""
    ls -la VANNES_FINAL_* 2>/dev/null || echo "Aucun fichier final trouvé"
else
    echo ""
    echo "❌ Erreur lors de l'extraction"
    exit 1
fi