#!/usr/bin/env python3
"""
Lance le scraper Essonne en mode test automatique
"""

from essonne_scraper_final import EssonneBarScraperFinal

def main():
    print("🚀 Lancement automatique du test Essonne")
    
    # Mode test avec fenêtre visible pour voir le fonctionnement
    scraper = EssonneBarScraperFinal(headless=False)
    
    try:
        # Test sur 3 avocats
        lawyers_data = scraper.test_improved_extraction(3)
        scraper.save_results(lawyers_data, "essonne_test_auto")
        
        if lawyers_data:
            print(f"\n✅ Test automatique réussi! {len(lawyers_data)} avocats extraits")
            
            # Résumé des données extraites
            emails_count = len([l for l in lawyers_data if l.get('email')])
            phones_count = len([l for l in lawyers_data if l.get('telephone')])
            specializations_count = len([l for l in lawyers_data if l.get('specialisations')])
            
            print(f"📊 Résumé:")
            print(f"   ✉️  Emails trouvés: {emails_count}/{len(lawyers_data)}")
            print(f"   📞 Téléphones: {phones_count}/{len(lawyers_data)}")
            print(f"   🎯 Spécialisations: {specializations_count}/{len(lawyers_data)}")
            
            print(f"\n🎯 Si le test est satisfaisant, tu peux lancer le scraping complet en modifiant ce script")
        else:
            print("\n❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()