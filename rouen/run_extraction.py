#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LANCEUR D'EXTRACTION POUR BARREAU DE ROUEN
==========================================

Script simple pour lancer l'extraction complète des avocats du Barreau de Rouen.
Utilise le scraper principal avec toutes les corrections de noms composés.
"""

import sys
import os
from rouen_scraper import RouenBarScraper

def main():
    """Lancer l'extraction complète"""
    print("🚀 LANCEMENT DE L'EXTRACTION BARREAU DE ROUEN")
    print("=" * 60)
    
    # Créer le scraper
    scraper = RouenBarScraper()
    
    # Lancer l'extraction complète (tous les avocats)
    print("📊 Extraction en cours... Cela peut prendre 30-60 minutes.")
    results = scraper.run_extraction(headless=True)
    
    if results:
        print(f"✅ SUCCÈS: {len(results)} avocats extraits!")
        print("\n📁 Fichiers générés:")
        print("- CSV: données complètes")
        print("- JSON: format structuré") 
        print("- TXT: emails uniquement")
        print("- Rapport détaillé")
        
        # Afficher quelques exemples de noms corrigés
        print("\n🔧 Exemples de correction des noms:")
        examples = [
            ("ABDOU Sophia", "Sophia", "ABDOU"),
            ("ALVES DA COSTA David", "David", "ALVES DA COSTA"),
            ("CHAILLÉ DE NÉRÉ Dixie", "Dixie", "CHAILLÉ DE NÉRÉ")
        ]
        
        for nom_complet, prenom, nom in examples:
            print(f"  '{nom_complet}' -> prénom='{prenom}', nom='{nom}'")
            
    else:
        print("❌ ÉCHEC: Aucun avocat extrait")
        return 1
    
    print(f"\n🎉 Extraction terminée avec succès!")
    return 0

if __name__ == "__main__":
    sys.exit(main())