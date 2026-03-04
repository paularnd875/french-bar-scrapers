#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT COMPLET - EXTRACTION MEAUX
Lance automatiquement l'extraction complète + post-traitement

UTILISATION:
python3 run_complete_extraction.py

RÉSULTAT:
- Extraction de ~185 avocats
- Post-traitement automatique des cabinets  
- Fichiers finaux optimisés

DÉVELOPPÉ POUR: https://github.com/paularnd875/french-bar-scrapers
"""

import subprocess
import sys
import glob
import os
import time
from datetime import datetime

def run_command(command, description):
    """Exécute une commande avec gestion d'erreur"""
    print(f"\n🔄 {description}...")
    print(f"💻 Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} terminé avec succès")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Erreur lors de {description}")
            if result.stderr:
                print(f"Erreur: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception lors de {description}: {e}")
        return False

def find_latest_json():
    """Trouve le fichier JSON le plus récent généré"""
    pattern = "MEAUX_AVOCATS_*avocats_*.json"
    files = glob.glob(pattern)
    
    if not files:
        return None
        
    # Trier par date de modification
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def main():
    print("=" * 70)
    print("🏛️  EXTRACTION COMPLÈTE - BARREAU DE MEAUX")
    print("=" * 70)
    print("🎯 Objectif: Extraction complète avec post-traitement automatique")
    print(f"⏰ Démarrage: {datetime.now().strftime('%H:%M:%S')}")
    
    start_time = time.time()
    
    # Étape 1: Extraction principale
    success = run_command(
        "python3 meaux_scraper_main.py",
        "Extraction principale des avocats"
    )
    
    if not success:
        print("❌ Échec de l'extraction principale")
        return 1
    
    # Étape 2: Trouver le fichier généré
    print("\n🔍 Recherche du fichier JSON généré...")
    json_file = find_latest_json()
    
    if not json_file:
        print("❌ Aucun fichier JSON trouvé")
        return 1
        
    print(f"📁 Fichier trouvé: {json_file}")
    
    # Étape 3: Post-traitement des cabinets
    success = run_command(
        f"python3 meaux_cabinet_enhancer.py {json_file}",
        "Post-traitement des cabinets"
    )
    
    if not success:
        print("⚠️  Post-traitement échoué, mais extraction principale réussie")
        print(f"📁 Fichier principal disponible: {json_file}")
    
    # Résumé final
    end_time = time.time()
    duration = (end_time - start_time) / 60
    
    print("\n" + "=" * 70)
    print("🎉 EXTRACTION COMPLÈTE TERMINÉE")
    print("=" * 70)
    print(f"⏱️  Durée totale: {duration:.1f} minutes")
    print(f"📅 Terminé à: {datetime.now().strftime('%H:%M:%S')}")
    
    # Lister tous les fichiers générés
    print("\n📁 FICHIERS GÉNÉRÉS:")
    
    patterns = [
        "MEAUX_AVOCATS_*.csv",
        "MEAUX_AVOCATS_*.json", 
        "MEAUX_EMAILS_*.txt",
        "MEAUX_ENHANCED_*.csv",
        "MEAUX_ENHANCED_*.json"
    ]
    
    all_files = []
    for pattern in patterns:
        all_files.extend(glob.glob(pattern))
    
    # Trier par date de modification (plus récents en premier)
    all_files.sort(key=os.path.getmtime, reverse=True)
    
    for i, file in enumerate(all_files[:10], 1):  # Afficher les 10 plus récents
        size = os.path.getsize(file) / 1024  # Taille en KB
        mod_time = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%H:%M:%S')
        print(f"  {i:2d}. {file} ({size:.1f} KB) - {mod_time}")
    
    if len(all_files) > 10:
        print(f"  ... et {len(all_files) - 10} autres fichiers")
    
    print(f"\n✨ Mission accomplie! {len(all_files)} fichiers générés")
    return 0

if __name__ == "__main__":
    sys.exit(main())