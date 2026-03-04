#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST UNITAIRE - SCRAPER AVEYRON
==============================
Script de test rapide pour valider le scraper Aveyron
"""

import os
import sys
from aveyron_scraper import scraper_aveyron_complet, mapping_noms_corriges_complet, corriger_nom_depuis_url

def test_mapping_noms():
    """Test du mapping des noms avec accents"""
    print("🧪 Test du mapping des noms...")
    
    mapping = mapping_noms_corriges_complet()
    
    # Tests de cas connus
    test_cases = [
        ('archimbaud-th%', 'Archimbaud Théophile'),
        ('berger-fran%', 'Berger François-Xavier'),
        ('bessi%', 'Bessière Maxime')
    ]
    
    for url_nom, expected in test_cases:
        full_url = f"https://www.avocats12.com/liste-des-avocats/{url_nom}"
        result = corriger_nom_depuis_url(full_url)
        
        if result['nom_complet_corrige'] == expected:
            print(f"   ✅ {url_nom} → {expected}")
        else:
            print(f"   ❌ {url_nom} → {result['nom_complet_corrige']} (attendu: {expected})")
            return False
    
    print(f"✅ Mapping validé - {len(mapping)} corrections disponibles")
    return True

def test_scraper_echantillon():
    """Test du scraper sur un petit échantillon"""
    print("\n🧪 Test du scraper sur 3 avocats...")
    
    # Mode silencieux pour les tests
    os.environ['SILENT_MODE'] = '1'
    
    try:
        resultats = scraper_aveyron_complet(mode="test", limite_test=3)
        
        if resultats['success']:
            print(f"✅ Extraction réussie: {resultats['total_avocats']} avocats")
            print(f"   📅 Années: {resultats['annees_trouvees']}/{resultats['total_avocats']}")
            print(f"   📞 Tél: {resultats.get('phones', 0)}/{resultats['total_avocats']}")
            print(f"   🏠 Adresses: {resultats['adresses_completes']}/{resultats['total_avocats']}")
            print(f"   🏆 Score qualité: {resultats['score_qualite']:.1f}%")
            
            # Validation des critères de réussite
            if (resultats['annees_trouvees'] >= 2 and 
                resultats['adresses_completes'] >= 2 and
                resultats['score_qualite'] >= 60):
                print("✅ Test scraper réussi")
                return True
            else:
                print("❌ Test scraper échoué - Qualité insuffisante")
                return False
        else:
            print(f"❌ Erreur scraper: {resultats['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Exception durant le test: {str(e)}")
        return False
    finally:
        # Nettoyage
        if 'SILENT_MODE' in os.environ:
            del os.environ['SILENT_MODE']

def nettoyer_fichiers_test():
    """Supprime les fichiers de test générés"""
    import glob
    
    patterns = [
        'AVEYRON_TEST_*.csv',
        'AVEYRON_TEST_*.json', 
        'AVEYRON_TEST_*.txt',
        'AVEYRON_BACKUP_*.json'
    ]
    
    fichiers_supprimes = 0
    for pattern in patterns:
        for fichier in glob.glob(pattern):
            try:
                os.remove(fichier)
                fichiers_supprimes += 1
            except:
                pass
    
    if fichiers_supprimes > 0:
        print(f"🧹 {fichiers_supprimes} fichiers de test nettoyés")

def main():
    """Fonction principale de test"""
    print("🧪 TESTS UNITAIRES - SCRAPER AVEYRON")
    print("=" * 50)
    
    # Test 1: Mapping des noms
    if not test_mapping_noms():
        print("\n❌ ÉCHEC - Test mapping")
        sys.exit(1)
    
    # Test 2: Scraper sur échantillon
    if not test_scraper_echantillon():
        print("\n❌ ÉCHEC - Test scraper")
        sys.exit(1)
    
    # Nettoyage
    nettoyer_fichiers_test()
    
    print("\n" + "=" * 50)
    print("🎉 TOUS LES TESTS RÉUSSIS !")
    print("✅ Le scraper Aveyron est prêt pour la production")
    print("=" * 50)

if __name__ == "__main__":
    main()