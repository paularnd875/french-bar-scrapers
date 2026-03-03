#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANCEUR PRODUCTION - BARREAU VILLEFRANCHE-SUR-SAÔNE
Script principal pour l'extraction complète
"""

import subprocess
import sys
import os
from datetime import datetime

def main():
    """Fonction principale de lancement"""
    
    print("🚀 LANCEUR PRODUCTION - BARREAU VILLEFRANCHE-SUR-SAÔNE")
    print("=" * 70)
    print("📅 Date:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("📂 Répertoire de travail:", os.getcwd())
    print("=" * 70)
    
    # Vérifier que le script principal existe
    script_path = "VILLEFRANCHE_SCRAPER_PRODUCTION.py"
    if not os.path.exists(script_path):
        print(f"❌ ERREUR: Le fichier {script_path} n'existe pas!")
        return
    
    print("✅ Script principal trouvé")
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette opération va extraire TOUS les avocats du barreau.")
    print("   Cela peut prendre plusieurs minutes.")
    print("   Les fichiers seront sauvegardés dans le répertoire actuel.")
    
    choice = input("\n🤔 Voulez-vous continuer? (o/N): ").strip().lower()
    
    if choice not in ['o', 'oui', 'y', 'yes']:
        print("❌ Opération annulée par l'utilisateur")
        return
    
    print("\n🚀 DÉMARRAGE DE L'EXTRACTION COMPLÈTE...")
    print("⏳ Veuillez patienter, l'extraction est en cours...")
    print("💾 Des sauvegardes intermédiaires seront effectuées tous les 25 avocats")
    print("-" * 70)
    
    try:
        # Lancer le script principal
        result = subprocess.run([
            sys.executable, 
            script_path
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print("=" * 70)
            print("📁 Les fichiers suivants ont été générés:")
            print("   • CSV avec toutes les données")
            print("   • JSON pour traitement automatique") 
            print("   • TXT avec uniquement les emails")
            print("   • Rapport détaillé avec statistiques")
            print("=" * 70)
        else:
            print(f"❌ ERREUR: Le script s'est terminé avec le code {result.returncode}")
            
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrompue par l'utilisateur")
        print("💾 Les sauvegardes intermédiaires sont conservées")
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")

if __name__ == "__main__":
    main()