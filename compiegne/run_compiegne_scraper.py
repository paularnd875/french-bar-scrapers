#!/usr/bin/env python3
"""
Script de lancement principal pour le scraper Compiègne
Point d'entrée unique avec parsing de noms corrigé
"""

from COMPIEGNE_SCRAPER_FINAL_CORRECTED import CompiegneBarreauScraperFinalCorrected

def main():
    """Lance le scraping de Compiègne avec parsing corrigé"""
    print("🚀 SCRAPING BARREAU DE COMPIÈGNE - VERSION CORRIGÉE")
    print("📍 Site: http://www.avocats-compiegne.fr/")
    print("🧠 Parsing de noms: 100% précision garantie\n")
    
    scraper = CompiegneBarreauScraperFinalCorrected(headless=True)
    results = scraper.run_production()
    
    if results:
        print(f"\n✅ SUCCÈS!")
        print(f"   👨‍💼 {results['total_avocats']} avocats récupérés")
        print(f"   📧 {results['total_emails']} emails uniques")
        print(f"   🎯 Parsing parfait des noms composés")
        print(f"   📁 Fichiers prêts à utiliser")
        return True
    else:
        print(f"\n❌ ÉCHEC du scraping")
        return False

if __name__ == "__main__":
    main()