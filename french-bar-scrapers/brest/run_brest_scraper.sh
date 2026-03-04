#!/bin/bash
# 🚀 Script de lancement pour le scraper Brest
# Usage: ./run_brest_scraper.sh [OPTIONS]

echo "🚀 === SCRAPER BARREAU DE BREST ==="
echo "📍 Site: https://www.avocats-brest.fr/avocats/"
echo ""

# Fonction d'aide
show_help() {
    echo "Usage: ./run_brest_scraper.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test     Mode test (3 pages seulement)"
    echo "  -v, --visual   Mode visuel (avec interface)"
    echo "  -b, --background   Lancer en arrière-plan"
    echo "  -m, --monitor      Surveiller un processus en arrière-plan"
    echo "  -h, --help     Afficher cette aide"
    echo ""
    echo "Exemples:"
    echo "  ./run_brest_scraper.sh              # Extraction complète headless"
    echo "  ./run_brest_scraper.sh --test       # Test rapide"
    echo "  ./run_brest_scraper.sh --visual     # Mode debug visuel"
    echo "  ./run_brest_scraper.sh --background # Lancer en arrière-plan"
    echo ""
}

# Variables par défaut
TEST_MODE=""
VISUAL_MODE=""
BACKGROUND_MODE=false
MONITOR_MODE=false

# Analyse des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            TEST_MODE="--test"
            shift
            ;;
        -v|--visual)
            VISUAL_MODE="--visual"
            shift
            ;;
        -b|--background)
            BACKGROUND_MODE=true
            shift
            ;;
        -m|--monitor)
            MONITOR_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Mode monitoring
if [ "$MONITOR_MODE" = true ]; then
    echo "🔍 Mode monitoring activé"
    if [ -f "monitor_brest.py" ]; then
        python3 monitor_brest.py
    else
        echo "❌ Fichier monitor_brest.py non trouvé"
    fi
    exit 0
fi

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Vérification du script principal
if [ ! -f "brest_scraper_final.py" ]; then
    echo "❌ Script brest_scraper_final.py non trouvé"
    exit 1
fi

# Construction de la commande
COMMAND="python3 brest_scraper_final.py $TEST_MODE $VISUAL_MODE"

# Affichage des paramètres
echo "⚙️  Configuration:"
if [ -n "$TEST_MODE" ]; then
    echo "   📄 Mode: Test (3 pages)"
else
    echo "   📄 Mode: Complet (15 pages, ~258 avocats)"
fi

if [ -n "$VISUAL_MODE" ]; then
    echo "   👁️  Interface: Visuelle"
else
    echo "   👁️  Interface: Headless"
fi

if [ "$BACKGROUND_MODE" = true ]; then
    echo "   🔄 Exécution: Arrière-plan"
else
    echo "   🔄 Exécution: Premier plan"
fi

echo ""

# Lancement
if [ "$BACKGROUND_MODE" = true ]; then
    echo "🚀 Lancement en arrière-plan..."
    nohup $COMMAND > brest_scraper.log 2>&1 &
    PID=$!
    echo "📋 Processus lancé avec PID: $PID"
    echo "📋 Log disponible: tail -f brest_scraper.log"
    
    # Attendre un peu puis afficher le début du log
    sleep 3
    echo ""
    echo "🔍 === Début du log ==="
    if [ -f "brest_scraper.log" ]; then
        head -20 brest_scraper.log
    fi
    echo ""
    echo "💡 Pour surveiller: ./run_brest_scraper.sh --monitor"
    echo "💡 Pour arrêter: kill $PID"
else
    echo "🚀 Lancement..."
    echo "💡 Utilisez Ctrl+C pour arrêter"
    echo ""
    $COMMAND
fi

echo ""
echo "✅ Script terminé"