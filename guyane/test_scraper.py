#!/usr/bin/env python3
"""
Script de test pour le scraper Barreau de Guyane
Test sur 5 avocats pour validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from guyane_scraper_production import GuyaneBarScraperProduction

def test_guyane_scraper():
    """Test le scraper sur 5 avocats"""
    
    print("🧪 TEST SCRAPER BARREAU DE GUYANE")
    print("="*50)
    
    try:
        # Test avec limite de 5 avocats, mode headless
        scraper = GuyaneBarScraperProduction(headless=True, max_pages=1)
        
        # Modifier temporairement pour tester seulement 5 avocats
        print("📋 Test sur les 5 premiers avocats...")
        
        # Navigation vers le site
        scraper.driver.get(scraper.base_url)
        scraper.accept_cookies()
        
        # Récupérer 5 premiers avocats
        lawyer_cards = scraper.driver.find_elements("class name", "annuaireFicheMini")
        test_lawyers = []
        
        for i, card in enumerate(lawyer_cards[:5]):
            try:
                name_link = card.find_element("xpath", ".//h4/a")
                lawyer = {
                    'nom_complet': name_link.text.strip(),
                    'detail_url': name_link.get_attribute('href'),
                    'page_origine': 1
                }
                test_lawyers.append(lawyer)
            except:
                continue
        
        print(f"👥 {len(test_lawyers)} avocats à tester")
        
        # Extraction détaillée
        results = []
        for lawyer in test_lawyers:
            detailed = scraper.extract_enhanced_details(lawyer)
            results.append(detailed)
        
        # Statistiques
        emails_count = len([r for r in results if r.get('email')])
        phones_count = len([r for r in results if r.get('telephone')])
        structures_count = len([r for r in results if r.get('structure') and r['structure'] != 'INDIVIDUEL'])
        specs_count = len([r for r in results if r.get('specialisations')])
        
        print(f"\n📊 RÉSULTATS DU TEST:")
        print(f"✅ Avocats testés: {len(results)}")
        print(f"✅ Emails trouvés: {emails_count}/{len(results)}")
        print(f"✅ Téléphones trouvés: {phones_count}/{len(results)}")
        print(f"✅ Structures détectées: {structures_count}/{len(results)}")
        print(f"✅ Spécialisations trouvées: {specs_count}/{len(results)}")
        
        # Exemples
        print(f"\n🎯 EXEMPLES:")
        for i, r in enumerate(results[:3], 1):
            print(f"[{i}] {r.get('nom_complet', 'N/A')}")
            print(f"    📧 {r.get('email', 'Non trouvé')}")
            print(f"    🏢 {r.get('structure', 'Non trouvé')}")
        
        # Validation
        success_rate = (emails_count + phones_count) / (len(results) * 2) * 100
        
        if success_rate >= 70:
            print(f"\n🎉 TEST RÉUSSI ! Taux de succès: {success_rate:.1f}%")
            return True
        else:
            print(f"\n⚠️ Test partiel. Taux: {success_rate:.1f}%")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False
    
    finally:
        try:
            scraper.driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_guyane_scraper()