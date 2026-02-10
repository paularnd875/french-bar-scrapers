#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extracteur FINAL de spécialisations pour le Barreau de Bordeaux
Utilise les vrais codes de spécialisations trouvés
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import csv
from datetime import datetime

class BordeauxSpecialisationsFinalExtractor:
    def __init__(self):
        self.base_url = "https://www.barreau-bordeaux.com"
        self.search_url = self.base_url + "/avocats"
        
        # Spécialisations réelles trouvées sur le site
        self.real_specialisations = [
            {'value': '53', 'text': 'Droit bancaire et boursier'},
            {'value': '4218', 'text': 'Droit commercial'},
            {'value': '54', 'text': 'Droit commercial, des affaires et de la concurrence'},
            {'value': '57', 'text': 'Droit de l\'environnement'},
            {'value': '59', 'text': 'Droit de la famille, des personnes, et de leur patrimoine'},
            {'value': '67', 'text': 'Droit de la propriété intellectuelle'},
            {'value': '70', 'text': 'Droit de la santé'},
            {'value': '71', 'text': 'Droit de la sécurité sociale et de la protection sociale'},
            {'value': '52', 'text': 'Droit des assurances'},
            {'value': '58', 'text': 'Droit des étrangers et de la nationalité'},
            {'value': '62', 'text': 'Droit des garanties, des sûretés et des mesures d\'exécution'},
            {'value': '72', 'text': 'Droit des sociétés'},
            {'value': '55', 'text': 'Droit du crédit et de la consommation'},
            {'value': '56', 'text': 'Droit du dommage corporel'},
            {'value': '65', 'text': 'Droit du numérique et des communications'},
            {'value': '73', 'text': 'Droit du sport'},
            {'value': '75', 'text': 'Droit du travail'},
            {'value': '61', 'text': 'Droit fiscal et droit douanier'},
            {'value': '63', 'text': 'Droit immobilier'},
            {'value': '64', 'text': 'Droit international et de l\'Union européenne'},
            {'value': '66', 'text': 'Droit pénal'},
            {'value': '68', 'text': 'Droit public'},
            {'value': '69', 'text': 'Droit rural'}
        ]
        
        self.results_by_specialisation = {}
        
    def search_by_specialisation(self, specialisation_code, specialisation_name):
        """Recherche les avocats par spécialisation avec le vrai paramètre"""
        print(f"\n=== RECHERCHE: {specialisation_name} (code: {specialisation_code}) ===")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9'
        })
        
        try:
            # Utiliser le bon paramètre : specialite
            params = {'specialite': specialisation_code}
            response = session.get(self.search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Chercher les cartes d'avocats
                cards = soup.find_all('div', class_='card')
                lawyer_cards = [card for card in cards if card.find('h3', class_='card-title')]
                
                lawyers_found = []
                
                if lawyer_cards:
                    print(f"  ✅ {len(lawyer_cards)} avocats trouvés")
                    
                    for card in lawyer_cards:
                        title = card.find('h3', class_='card-title')
                        if title:
                            name_text = title.get_text().strip()
                            # Nettoyer le nom (enlever les retours à la ligne)
                            name_clean = ' '.join(name_text.split())
                            
                            lawyers_found.append({
                                'nom_complet': name_clean,
                                'specialisation': specialisation_name,
                                'code_specialisation': specialisation_code
                            })
                            
                    # Afficher quelques exemples
                    for lawyer in lawyers_found[:3]:
                        print(f"    - {lawyer['nom_complet']}")
                    if len(lawyers_found) > 3:
                        print(f"    ... et {len(lawyers_found) - 3} autres")
                else:
                    print(f"  ❌ Aucun avocat trouvé")
                    
                return lawyers_found
                
            else:
                print(f"  ❌ Erreur HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            return []
    
    def extract_all_specialisations(self):
        """Lance l'extraction complète des spécialisations"""
        print("="*70)
        print("EXTRACTION FINALE DES SPÉCIALISATIONS - BARREAU DE BORDEAUX")
        print("="*70)
        
        print(f"\n✅ {len(self.real_specialisations)} spécialisations officielles détectées")
        for spec in self.real_specialisations:
            print(f"  - {spec['text']} (code: {spec['value']})")
        
        print(f"\nÉtape: Extraction par spécialisation...")
        
        all_results = []
        
        for i, spec in enumerate(self.real_specialisations, 1):
            print(f"\n[{i}/{len(self.real_specialisations)}] {spec['text']}")
            
            lawyers = self.search_by_specialisation(spec['value'], spec['text'])
            
            if lawyers:
                self.results_by_specialisation[spec['text']] = lawyers
                all_results.extend(lawyers)
            
            # Pause pour éviter la surcharge
            time.sleep(0.5)
        
        # Sauvegarde
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON détaillé
        with open(f'bordeaux_specialisations_final_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_specialisations': len(self.real_specialisations),
                'total_relations_avocat_specialisation': len(all_results),
                'specialisations_avec_avocats': len([s for s in self.results_by_specialisation if self.results_by_specialisation[s]]),
                'specialisations_testees': [s['text'] for s in self.real_specialisations],
                'resultats_par_specialisation': self.results_by_specialisation,
                'toutes_relations': all_results
            }, f, indent=2, ensure_ascii=False)
        
        # CSV simple pour croisement
        with open(f'bordeaux_specialisations_relations_{timestamp}.csv', 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['nom_complet', 'specialisation', 'code_specialisation'])
            
            for result in all_results:
                writer.writerow([result['nom_complet'], result['specialisation'], result['code_specialisation']])
        
        # Statistiques par spécialisation
        stats = {}
        for spec_name, lawyers in self.results_by_specialisation.items():
            stats[spec_name] = len(lawyers)
        
        # Tri par nombre d'avocats
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n" + "="*70)
        print("EXTRACTION DES SPÉCIALISATIONS TERMINÉE")
        print("="*70)
        print(f"Spécialisations testées: {len(self.real_specialisations)}")
        print(f"Spécialisations avec avocats: {len([s for s in stats if stats[s] > 0])}")
        print(f"Relations avocat-spécialisation trouvées: {len(all_results)}")
        
        print(f"\nTOP 10 DES SPÉCIALISATIONS:")
        for spec_name, count in sorted_stats[:10]:
            if count > 0:
                print(f"  - {spec_name}: {count} avocats")
        
        print(f"\nFichiers créés:")
        print(f"  - bordeaux_specialisations_final_{timestamp}.json")
        print(f"  - bordeaux_specialisations_relations_{timestamp}.csv")
        
        return all_results

if __name__ == "__main__":
    extractor = BordeauxSpecialisationsFinalExtractor()
    extractor.extract_all_specialisations()