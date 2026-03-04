#!/usr/bin/env python3
"""
Script principal pour lancer le scraper du Barreau de Bonneville
Usage: python3 run_scraper.py
"""

import sys
import os
from bonneville_scraper_final_optimise import BonnevilleFinalOptimizedScraper
from bonneville_email_verifier import BonnevilleEmailVerifier

def main():
    print("🏛️  SCRAPER BARREAU DE BONNEVILLE")
    print("=" * 40)
    print("1. Extraction complète")
    print("2. Vérification des emails")
    print("=" * 40)
    
    choice = input("Choisissez une option (1-2): ").strip()
    
    if choice == "1":
        print("\n🚀 Lancement de l'extraction complète...")
        scraper = BonnevilleFinalOptimizedScraper()
        success = scraper.run_complete_extraction()
        
        if success:
            print("\n✅ Extraction terminée avec succès !")
            
            # Proposer la vérification
            verify = input("\nVoulez-vous vérifier les emails ? (o/n): ").strip().lower()
            if verify in ['o', 'oui', 'y', 'yes']:
                print("\n🔍 Vérification des emails...")
                verifier = BonnevilleEmailVerifier()
                
                # Trouver le dernier fichier JSON généré
                import glob
                json_files = glob.glob("bonneville_COMPLET_*_avocats_*.json")
                if json_files:
                    latest_file = max(json_files, key=os.path.getctime)
                    verifier.run_verification(latest_file)
        else:
            print("\n❌ Échec de l'extraction")
            
    elif choice == "2":
        print("\n🔍 Vérification des emails...")
        verifier = BonnevilleEmailVerifier()
        
        # Chercher un fichier JSON
        import glob
        json_files = glob.glob("bonneville_*.json")
        if json_files:
            latest_file = max(json_files, key=os.path.getctime)
            print(f"Utilisation du fichier : {latest_file}")
            verifier.run_verification(latest_file)
        else:
            print("❌ Aucun fichier de données trouvé. Lancez d'abord l'extraction (option 1).")
    else:
        print("❌ Option invalide")
        sys.exit(1)

if __name__ == "__main__":
    main()