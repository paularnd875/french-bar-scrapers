#!/bin/bash

echo "🚀 SCRAPER BARREAU DE CASTRES"
echo "============================="
echo ""
echo "Que souhaitez-vous faire ?"
echo ""
echo "1) Test rapide (5 avocats) - Mode headless"
echo "2) Extraction complète (tous les avocats) - Mode headless"
echo "3) Test visuel (5 avocats) - Mode avec fenêtres"
echo "4) Extraction complète visuelle - Mode avec fenêtres"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        echo "🔄 Lancement test rapide (5 avocats)..."
        python3 castres_scraper_final.py --limit 5
        ;;
    2)
        echo "🔄 Lancement extraction COMPLÈTE (mode headless)..."
        echo "⚠️  Cela peut prendre 10-15 minutes..."
        read -p "Continuer ? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            python3 castres_scraper_final.py
        else
            echo "Annulé."
        fi
        ;;
    3)
        echo "🔄 Lancement test visuel (5 avocats)..."
        python3 castres_scraper_final.py --visual --limit 5
        ;;
    4)
        echo "🔄 Lancement extraction complète (mode visuel)..."
        echo "⚠️  Cela peut prendre 10-15 minutes et ouvrira des fenêtres..."
        read -p "Continuer ? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            python3 castres_scraper_final.py --visual
        else
            echo "Annulé."
        fi
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac