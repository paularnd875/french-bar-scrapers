#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test rapide pour le scraper Saint-Denis
Teste l'extraction sur quelques avocats seulement
"""

from saint_denis_scraper import SaintDenisScraper

def test_extraction():
    """Test rapide avec quelques URLs"""
    print("🧪 Test d'extraction Saint-Denis...")
    
    scraper = SaintDenisScraper()
    
    # Test avec URLs hardcodées (plus rapide)
    files = scraper.run_extraction(collect_urls=False)
    
    if files:
        csv_file, json_file, emails_file, rapport_file = files
        print(f"\n✅ Test réussi !")
        print(f"📁 Fichiers de test générés :")
        print(f"   - CSV : {csv_file}")
        print(f"   - JSON: {json_file}")
        print(f"   - Emails: {emails_file}")
        print(f"   - Rapport: {rapport_file}")
    else:
        print("❌ Test échoué")

if __name__ == "__main__":
    test_extraction()