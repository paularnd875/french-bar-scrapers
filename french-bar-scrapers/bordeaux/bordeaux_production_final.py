#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper de production final pour le Barreau de Bordeaux
Basé sur la méthode qui fonctionne à 100%
"""

import json
import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

class BordeauxProductionScraper:
    def __init__(self, max_workers=10):
        self.base_url = "https://www.barreau-bordeaux.com"
        self.results = []
        self.failed = []
        self.lock = threading.Lock()
        self.max_workers = max_workers
        self.processed = 0
        
    def extract_email(self, text):
        """Extrait un email du texte"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(pattern, text)
        for email in matches:
            if not any(x in email.lower() for x in ['example', 'domain', 'wordpress', 'wpengine']):
                return email
        return None
        
    def extract_phone(self, text):
        """Extrait un téléphone du texte"""
        pattern = r'(?:0|\+33\s?)[1-9](?:[\s.-]?\d{2}){4}'
        matches = re.findall(pattern, text)
        if matches:
            phone = re.sub(r'[^\d]', '', matches[0])
            if phone.startswith('33'):
                phone = '0' + phone[2:]
            if len(phone) == 10:
                return '.'.join([phone[i:i+2] for i in range(0, 10, 2)])
        return None
        
    def search_lawyer(self, lawyer_data):
        """Recherche un avocat"""
        nom = lawyer_data['nom']
        prenom = lawyer_data['prenom']
        
        # Session avec headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9'
        })
        
        results = {}
        
        # Recherche par nom via le formulaire
        try:
            url = self.base_url + "/avocats"
            params = {'nom': nom}
            response = session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                text = response.text
                
                # Extraire email et téléphone
                email = self.extract_email(text)
                phone = self.extract_phone(text)
                
                if email:
                    results['email'] = email
                if phone:
                    results['telephone'] = phone
                    
                # Extraire l'adresse si on a trouvé des données
                if email or phone:
                    soup = BeautifulSoup(text, 'html.parser')
                    
                    # Adresse
                    for pattern in ['33000', '33100', '33200', '33300', '33400', '33500', 'Bordeaux']:
                        if pattern in text:
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if pattern in line:
                                    address = ' '.join(lines[max(0,i-1):min(len(lines),i+2)])
                                    address = re.sub(r'\s+', ' ', address).strip()
                                    address = re.sub(r'<[^>]+>', '', address)  # Retirer les balises HTML
                                    if len(address) > 20 and len(address) < 200:
                                        results['adresse'] = address
                                        break
                            break
                            
                    # Cabinet
                    cabinet_match = re.search(r'(?:Cabinet|SCP|SELARL|SARL)\s+([A-Z][A-Za-zÀ-ÿ\s&\-\']+)', text)
                    if cabinet_match:
                        results['cabinet'] = cabinet_match.group(1).strip()
                        
                    # Spécialisations
                    specs = []
                    spec_keywords = ['Droit civil', 'Droit pénal', 'Droit commercial', 'Droit du travail',
                                   'Droit de la famille', 'Droit immobilier', 'Droit fiscal', 
                                   'Droit des affaires', 'Droit social']
                    text_lower = text.lower()
                    for spec in spec_keywords:
                        if spec.lower() in text_lower:
                            specs.append(spec)
                    if specs:
                        results['specialisations'] = ', '.join(specs[:3])
                        
        except Exception as e:
            # En cas d'erreur, essayer une méthode alternative
            try:
                patterns = [
                    "/avocat/%s-%s" % (prenom.lower(), nom.lower()),
                    "/avocats/%s-%s" % (prenom.lower(), nom.lower())
                ]
                
                for pattern in patterns:
                    url = self.base_url + pattern
                    response = session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        text = response.text
                        email = self.extract_email(text)
                        phone = self.extract_phone(text)
                        
                        if email:
                            results['email'] = email
                        if phone:
                            results['telephone'] = phone
                        if email or phone:
                            break
            except:
                pass
                
        return results
        
    def process_lawyer(self, lawyer_data):
        """Traite un avocat (pour le multi-threading)"""
        nom_complet = lawyer_data['nom_complet']
        
        try:
            # Rechercher
            info = self.search_lawyer(lawyer_data)
            
            with self.lock:
                self.processed += 1
                
                if info:
                    result = {
                        'nom': lawyer_data['nom'],
                        'prenom': lawyer_data['prenom'],
                        'nom_complet': nom_complet,
                        **info
                    }
                    self.results.append(result)
                    
                    # Affichage progression
                    if self.processed % 10 == 0:
                        print("[%d] ✓ %s - Email: %s" % 
                             (self.processed, nom_complet[:30], info.get('email', 'N/A')))
                else:
                    self.failed.append(lawyer_data)
                    
                # Sauvegarde intermédiaire tous les 100
                if self.processed % 100 == 0:
                    self.save_intermediate()
                    
        except Exception as e:
            with self.lock:
                self.failed.append(lawyer_data)
                self.processed += 1
                
        # Petite pause aléatoire
        time.sleep(random.uniform(0.3, 1.0))
        
    def save_intermediate(self):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open('bordeaux_intermediate_%s.json' % timestamp, 'w', encoding='utf-8') as f:
            json.dump({
                'processed': self.processed,
                'found': len(self.results),
                'results': self.results
            }, f, ensure_ascii=False)
            
        print(">>> Sauvegarde intermédiaire: %d traités, %d trouvés" % 
             (self.processed, len(self.results)))
             
    def save_final(self):
        """Sauvegarde finale complète"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        total = len(self.results) + len(self.failed)
        with open('bordeaux_COMPLET_%s.json' % timestamp, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'source': 'Barreau de Bordeaux',
                'total_avocats': total,
                'trouves': len(self.results),
                'non_trouves': len(self.failed),
                'taux_reussite': "%.1f%%" % (len(self.results)/total*100) if total > 0 else "0%",
                'resultats': self.results,
                'echecs': self.failed
            }, f, indent=2, ensure_ascii=False)
            
        # CSV
        with open('bordeaux_COMPLET_%s.csv' % timestamp, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone',
                         'adresse', 'cabinet', 'specialisations']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                row = {field: result.get(field, '') for field in fieldnames}
                writer.writerow(row)
                
        # Emails uniquement
        emails = [r['email'] for r in self.results if r.get('email')]
        with open('bordeaux_EMAILS_%s.txt' % timestamp, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(set(emails))))
            
        # Rapport détaillé
        with open('bordeaux_RAPPORT_%s.txt' % timestamp, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("RAPPORT FINAL D'EXTRACTION - BARREAU DE BORDEAUX\n")
            f.write("="*70 + "\n\n")
            
            f.write("Date et heure: %s\n" % timestamp)
            f.write("Site source: %s\n\n" % self.base_url)
            
            f.write("RÉSULTATS GLOBAUX:\n")
            f.write("-"*40 + "\n")
            f.write("Total d'avocats traités: %d\n" % total)
            f.write("Avocats avec données: %d\n" % len(self.results))
            f.write("Avocats sans données: %d\n" % len(self.failed))
            f.write("Taux de réussite: %.1f%%\n\n" % (len(self.results)/total*100 if total > 0 else 0))
            
            f.write("STATISTIQUES DÉTAILLÉES:\n")
            f.write("-"*40 + "\n")
            f.write("Avec email: %d (%.1f%% du total)\n" % 
                   (sum(1 for r in self.results if r.get('email')),
                    sum(1 for r in self.results if r.get('email'))/total*100 if total > 0 else 0))
            f.write("Avec téléphone: %d (%.1f%% du total)\n" % 
                   (sum(1 for r in self.results if r.get('telephone')),
                    sum(1 for r in self.results if r.get('telephone'))/total*100 if total > 0 else 0))
            f.write("Avec adresse: %d (%.1f%% du total)\n" % 
                   (sum(1 for r in self.results if r.get('adresse')),
                    sum(1 for r in self.results if r.get('adresse'))/total*100 if total > 0 else 0))
            f.write("Avec cabinet: %d (%.1f%% du total)\n" % 
                   (sum(1 for r in self.results if r.get('cabinet')),
                    sum(1 for r in self.results if r.get('cabinet'))/total*100 if total > 0 else 0))
            f.write("Avec spécialisations: %d (%.1f%% du total)\n\n" % 
                   (sum(1 for r in self.results if r.get('specialisations')),
                    sum(1 for r in self.results if r.get('specialisations'))/total*100 if total > 0 else 0))
            
            f.write("EMAILS UNIQUES EXTRAITS: %d\n" % len(set(emails)))
            
            f.write("\n" + "="*70 + "\n")
            f.write("FICHIERS GÉNÉRÉS:\n")
            f.write("- bordeaux_COMPLET_%s.json (données complètes)\n" % timestamp)
            f.write("- bordeaux_COMPLET_%s.csv (format Excel)\n" % timestamp)
            f.write("- bordeaux_EMAILS_%s.txt (liste des emails)\n" % timestamp)
            f.write("- bordeaux_RAPPORT_%s.txt (ce rapport)\n" % timestamp)
            f.write("="*70 + "\n")
            
        return timestamp
        
    def run(self, limit=None):
        """Lance l'extraction complète"""
        print("="*70)
        print("EXTRACTION COMPLÈTE - BARREAU DE BORDEAUX")
        print("="*70)
        
        start_time = time.time()
        
        # Charger les avocats
        with open('bordeaux_avocats_liste_20260210_110702.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_lawyers = data['avocats']
            
        if limit:
            all_lawyers = all_lawyers[:limit]
            print("Mode limité: %d avocats" % len(all_lawyers))
        else:
            print("Mode complet: %d avocats" % len(all_lawyers))
            
        print("Workers parallèles: %d" % self.max_workers)
        print("Démarrage...\n")
        
        # Traitement multi-thread
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_lawyer, lawyer) for lawyer in all_lawyers]
            
            # Attendre la fin
            for future in as_completed(futures):
                pass
                
        # Temps total
        duration = time.time() - start_time
        
        # Sauvegarder les résultats finaux
        timestamp = self.save_final()
        
        # Afficher le résumé
        print("\n" + "="*70)
        print("EXTRACTION TERMINÉE")
        print("="*70)
        print("Durée totale: %.1f minutes" % (duration/60))
        print("Vitesse: %.1f avocats/minute" % (len(all_lawyers)/(duration/60)))
        print("\nRÉSULTATS:")
        print("- Total traité: %d" % (len(self.results) + len(self.failed)))
        print("- Avec données: %d (%.1f%%)" % 
             (len(self.results), len(self.results)/(len(self.results)+len(self.failed))*100))
        print("- Emails trouvés: %d" % sum(1 for r in self.results if r.get('email')))
        print("- Téléphones trouvés: %d" % sum(1 for r in self.results if r.get('telephone')))
        print("\nFichiers créés: bordeaux_*_%s.*" % timestamp)
        print("="*70)

if __name__ == "__main__":
    import sys
    
    # Paramètres
    limit = None
    workers = 10
    
    if '--test' in sys.argv:
        limit = 100
        workers = 5
    elif '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
            
    # Lancer l'extraction
    scraper = BordeauxProductionScraper(max_workers=workers)
    scraper.run(limit=limit)