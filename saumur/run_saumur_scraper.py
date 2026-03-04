#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE LANCEMENT SIMPLIFIÉ - BARREAU DE SAUMUR
Lancement rapide du scraper exhaustif
"""

import os
import sys
import subprocess

def check_dependencies():
    """Vérifier les dépendances"""
    required_packages = ['PyPDF2', 'pandas', 'requests']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.lower() if package != 'PyPDF2' else 'PyPDF2')
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Dépendances manquantes : {', '.join(missing)}")
        print(f"📦 Installez avec : pip install {' '.join(missing)}")
        return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def main():
    print("🚀 LANCEMENT SCRAPER BARREAU DE SAUMUR")
    print("=" * 50)
    
    # Vérifier les dépendances
    if not check_dependencies():
        sys.exit(1)
    
    # Lancer le scraper principal
    script_path = "SAUMUR_SCRAPER_COMPLET_FINAL.py"
    
    if not os.path.exists(script_path):
        print(f"❌ Fichier {script_path} non trouvé")
        sys.exit(1)
    
    print(f"🔄 Lancement de {script_path}...")
    print("=" * 50)
    
    try:
        # Exécuter le script principal
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print("\n✅ Extraction terminée avec succès !")
            print("📁 Consultez les fichiers générés dans ce répertoire")
        else:
            print(f"\n❌ Erreur lors de l'exécution (code: {result.returncode})")
            
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()