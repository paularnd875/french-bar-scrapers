#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test rapide pour le Barreau de Périgueux
Teste l'extraction sur 3 profils pour validation rapide
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Import des fonctions du script principal
from perigueux_scraper_final import setup_driver, extract_lawyer_complete_avec_serment

# 3 URLs de test représentatives
TEST_URLS = [
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/77/dalonso.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/160/ALVES%20AMANDINE.html", 
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/116/famblard.html"
]

def test_perigueux_scraper():
    """Test rapide sur 3 profils"""
    print("🧪 TEST RAPIDE - SCRAPER BARREAU DE PÉRIGUEUX")
    print("=" * 50)
    print(f"📋 Test sur {len(TEST_URLS)} profils représentatifs")
    
    driver = setup_driver()
    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        for i, url in enumerate(TEST_URLS, 1):
            url_name = url.split('/')[-1]
            print(f"\n👤 {i}/{len(TEST_URLS)}: {url_name}")
            
            lawyer = extract_lawyer_complete_avec_serment(driver, url)
            if lawyer:
                results.append(lawyer)
                print(f"    ✅ {lawyer['prenom']} {lawyer['nom']}")
                
                if lawyer['email']:
                    print(f"       📧 {lawyer['email']}")
                if lawyer['telephone']:
                    print(f"       📞 {lawyer['telephone']}")
                if lawyer['annee_serment']:
                    print(f"       ⚖️ Serment: {lawyer['annee_serment']}")
            else:
                print(f"      ❌ Échec d'extraction")
        
        # Résultats du test
        print(f"\n📊 RÉSULTATS DU TEST:")
        print(f"  ✅ Profils extraits: {len(results)}/{len(TEST_URLS)}")
        
        emails_found = len([r for r in results if r['email']])
        phones_found = len([r for r in results if r['telephone']])
        serments_found = len([r for r in results if r['annee_serment']])
        
        print(f"  📧 Emails trouvés: {emails_found}/{len(results)}")
        print(f"  📞 Téléphones trouvés: {phones_found}/{len(results)}")
        print(f"  ⚖️ Dates serment: {serments_found}/{len(results)}")
        
        # Sauvegarde des résultats de test
        test_file = f"test_perigueux_{len(results)}profils_{timestamp}.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés: {test_file}")
        
        if len(results) == len(TEST_URLS) and emails_found >= 2:
            print(f"\n🎉 TEST RÉUSSI!")
            print(f"✅ Le scraper fonctionne correctement")
        else:
            print(f"\n⚠️ TEST PARTIEL")
            print(f"🔧 Vérifiez la configuration")
        
        return len(results)
        
    except Exception as e:
        print(f"❌ Erreur pendant le test: {e}")
        return 0
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🚀 Lancement du test rapide...")
    total = test_perigueux_scraper()
    print(f"\n🏁 TEST TERMINÉ: {total} profils testés")