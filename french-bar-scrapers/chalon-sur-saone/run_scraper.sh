#!/bin/bash
# Script de lancement pour le scraper Chalon-sur-Saône

echo "🏛️  LANCEMENT DU SCRAPER CHALON-SUR-SAÔNE"
echo "========================================="

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérifier Selenium
if ! python3 -c "import selenium" &> /dev/null; then
    echo "📦 Installation de Selenium..."
    pip3 install selenium
fi

echo "✅ Dépendances OK"
echo ""

# Demander le mode
read -p "Mode headless (sans fenêtre) ? [O/n]: " choice
case "$choice" in
    n|N ) 
        echo "🖥️  Lancement en mode VISUEL..."
        python3 chalon_sur_saone_scraper.py --visual
        ;;
    * ) 
        echo "🤖 Lancement en mode HEADLESS..."
        python3 chalon_sur_saone_scraper.py
        ;;
esac

echo ""
echo "🎉 Scraping terminé ! Vérifiez les fichiers générés."