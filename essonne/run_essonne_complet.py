#!/usr/bin/env python3
"""
Lance le scraper Essonne en mode complet (tous les avocats)
"""

from essonne_scraper_final import EssonneBarScraperFinal

def main():
    print("🚀 Lancement du scraping complet - Tous les avocats d'Essonne")
    print("="*60)
    print("⚠️  Ce processus va extraire environ 346 avocats")
    print("⏱️  Temps estimé: 15-20 minutes")
    print("💾 Sauvegardes intermédiaires toutes les 50 extractions")
    print()
    
    # Mode headless pour ne pas gêner le travail
    scraper = EssonneBarScraperFinal(headless=True)
    
    try:
        # Scraping complet
        lawyers_data = scraper.scrape_all_lawyers()
        
        if lawyers_data:
            # Sauvegarde finale
            scraper.save_results(lawyers_data, "essonne_COMPLET_FINAL")
            
            print(f"\n🎉 SCRAPING COMPLET TERMINÉ!")
            print(f"📊 {len(lawyers_data)} avocats extraits")
            
            # Statistiques détaillées
            emails_count = len([l for l in lawyers_data if l.get('email')])
            phones_count = len([l for l in lawyers_data if l.get('telephone')])
            specializations_count = len([l for l in lawyers_data if l.get('specialisations')])
            addresses_count = len([l for l in lawyers_data if l.get('adresse')])
            
            print(f"\n📈 STATISTIQUES FINALES:")
            print(f"   ✉️  Emails: {emails_count}/{len(lawyers_data)} ({emails_count/len(lawyers_data)*100:.1f}%)")
            print(f"   📞 Téléphones: {phones_count}/{len(lawyers_data)} ({phones_count/len(lawyers_data)*100:.1f}%)")
            print(f"   🎯 Spécialisations: {specializations_count}/{len(lawyers_data)} ({specializations_count/len(lawyers_data)*100:.1f}%)")
            print(f"   🏠 Adresses: {addresses_count}/{len(lawyers_data)} ({addresses_count/len(lawyers_data)*100:.1f}%)")
            
            print(f"\n📁 Les fichiers ont été sauvegardés dans le dossier courant")
            
        else:
            print("\n❌ Scraping échoué - Aucune donnée extraite")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrompu par l'utilisateur")
        print("💾 Les données partielles ont été sauvegardées")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        scraper.close()
        print("\n🔚 Scraper fermé")

if __name__ == "__main__":
    main()