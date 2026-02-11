#!/usr/bin/env python3
"""
🔍 Outil de monitoring pour le scraper Brest
Surveille le progrès du scraping en temps réel

Usage:
    python3 monitor_brest.py
"""

import time
import subprocess
import os
import re
from datetime import datetime

def check_scraper_status():
    """Vérifie si le scraper est en cours d'exécution"""
    try:
        result = subprocess.run(['pgrep', '-f', 'brest_scraper_final.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            return True, pid
        else:
            return False, None
    except:
        return False, None

def get_progress_from_log():
    """Extrait le progrès depuis le fichier de log"""
    try:
        log_files = ['brest_scraper.log', '../brest_scraper.log']
        log_content = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.readlines()
                break
        
        if not log_content:
            return "Log non trouvé"
        
        # Chercher les dernières informations pertinentes
        last_page = None
        total_lawyers = 0
        current_page = None
        max_pages = None
        
        for line in reversed(log_content):
            # Chercher le format "PAGE X/Y"
            page_match = re.search(r'=== PAGE (\d+)/(\d+) ===', line)
            if page_match and not current_page:
                current_page = int(page_match.group(1))
                max_pages = int(page_match.group(2))
                last_page = f"Page {current_page}/{max_pages}"
            
            # Chercher le total cumulé
            total_match = re.search(r'Total cumulé: (\d+) avocats', line)
            if total_match and total_lawyers == 0:
                total_lawyers = int(total_match.group(1))
        
        # Vérifier si terminé
        for line in reversed(log_content[-50:]):
            if "SCRAPING TERMINÉ" in line or "SCRAPING RÉUSSI" in line:
                return f"✅ TERMINÉ - {total_lawyers} avocats extraits"
        
        # Calculer le pourcentage si on a les infos
        if current_page and max_pages:
            percentage = (current_page / max_pages) * 100
            return f"🔄 {last_page} ({percentage:.1f}%) - {total_lawyers} avocats extraits"
        elif last_page:
            return f"🔄 {last_page} - {total_lawyers} avocats extraits"
        else:
            return "🔄 Démarrage en cours..."
    
    except Exception as e:
        return f"❌ Erreur lecture log: {e}"

def check_results_files():
    """Vérifie si des fichiers de résultats ont été créés"""
    files = []
    patterns = ['brest_complet_*.json', 'brest_complet_*.csv', 'brest_test_*.json']
    
    for pattern in patterns:
        # Recherche simple sans glob
        for filename in os.listdir('.'):
            if (filename.startswith('brest_complet_') or filename.startswith('brest_test_')) and \
               any(filename.endswith(ext) for ext in ['.json', '.csv', '.txt']):
                files.append(filename)
    
    return sorted(set(files))

def get_estimated_time_remaining(current_page, max_pages, start_time_str=None):
    """Estime le temps restant"""
    if not current_page or not max_pages or current_page >= max_pages:
        return None
    
    # Estimation basée sur ~1.7 minutes par page (observé)
    remaining_pages = max_pages - current_page
    estimated_minutes = remaining_pages * 1.7
    
    if estimated_minutes < 1:
        return "< 1 minute"
    elif estimated_minutes < 60:
        return f"~{estimated_minutes:.0f} minutes"
    else:
        hours = estimated_minutes / 60
        return f"~{hours:.1f} heures"

def main():
    """Fonction principale de monitoring"""
    print("🔍 === MONITORING SCRAPER BREST ===")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Statut du processus
    is_running, pid = check_scraper_status()
    
    if is_running:
        print(f"✅ Scraper actif (PID: {pid})")
    else:
        print("❌ Scraper arrêté")
    
    # Progrès depuis le log
    progress = get_progress_from_log()
    print(f"📊 Progrès: {progress}")
    
    # Estimation du temps restant
    if "Page" in progress and "/" in progress:
        try:
            page_info = re.search(r'Page (\d+)/(\d+)', progress)
            if page_info:
                current = int(page_info.group(1))
                total = int(page_info.group(2))
                time_est = get_estimated_time_remaining(current, total)
                if time_est:
                    print(f"⏱️  Temps estimé restant: {time_est}")
        except:
            pass
    
    # Fichiers de résultats
    result_files = check_results_files()
    if result_files:
        print(f"📁 Fichiers créés: {len(result_files)}")
        for file in result_files[:5]:  # Limiter l'affichage
            file_size = os.path.getsize(file) if os.path.exists(file) else 0
            size_str = f"({file_size/1024:.1f} KB)" if file_size > 0 else ""
            print(f"   - {file} {size_str}")
        if len(result_files) > 5:
            print(f"   ... et {len(result_files) - 5} autres")
    else:
        print("📁 Aucun fichier de résultat encore créé")
    
    print("\n" + "=" * 50)
    
    # Conseils selon le statut
    if is_running:
        print("🎯 Le scraper continue en arrière-plan")
        print("💡 Commandes utiles:")
        print("   - python3 monitor_brest.py     # Surveiller à nouveau")
        print("   - tail -f brest_scraper.log    # Voir le log en temps réel")
        print(f"   - kill {pid}                   # Arrêter le processus")
    elif result_files:
        print("✅ Le scraper s'est terminé avec succès")
        print("📋 Vérifiez les fichiers de résultats ci-dessus")
    else:
        print("⚠️  Le scraper s'est arrêté sans créer de fichiers")
        print("💡 Vérifiez les logs: tail -20 brest_scraper.log")
        print("💡 Pour relancer: ./run_brest_scraper.sh")

if __name__ == "__main__":
    main()