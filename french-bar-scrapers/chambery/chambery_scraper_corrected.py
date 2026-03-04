#!/usr/bin/env python3
"""
Script corrigé pour scrapper les avocats du barreau de Chambéry
Correction de la séparation nom/prénom/structure
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time

class ChamberyCorrectScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-chambery.fr/annuaire/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.lawyers = []
        
    def clean_name_and_firm(self, name_cell):
        """
        Nettoie et sépare correctement le nom de l'avocat de sa structure
        """
        html_content = str(name_cell)
        
        # Séparer par <br> ou <br/>
        if '<br>' in html_content or '<br/>' in html_content:
            # Remplacer les variantes de <br>
            html_content = re.sub(r'<br\s*/?>', '||BREAK||', html_content)
            parts = html_content.split('||BREAK||')
            
            if len(parts) >= 2:
                # Premier partie = nom avocat, deuxième = cabinet
                lawyer_raw = BeautifulSoup(parts[0], 'html.parser').get_text().strip()
                firm_raw = BeautifulSoup(parts[1], 'html.parser').get_text().strip()
            else:
                lawyer_raw = name_cell.get_text().strip()
                firm_raw = ""
        else:
            # Pas de séparation claire, tout est le nom de l'avocat
            lawyer_raw = name_cell.get_text().strip()
            firm_raw = ""
        
        return lawyer_raw, firm_raw
    
    def separate_first_last_name(self, full_name):
        """
        Sépare prénom et nom avec attention aux noms composés
        """
        # Nettoyer
        full_name = re.sub(r'\s+', ' ', full_name.strip())
        
        # Convertir en format normal (Première lettre majuscule)
        words = full_name.split()
        if not words:
            return "", ""
        
        # Cas spéciaux de particules
        particles = ['de', 'du', 'des', 'de la', 'van', 'von', 'le', 'la', 'd\'', 'di', 'da']
        
        if len(words) == 1:
            return words[0], ""
        elif len(words) == 2:
            return words[1], words[0]  # Format "NOM Prénom"
        else:
            # Plus de 2 mots - analysons la structure
            # Le format semble être "NOM Prénom(s)" 
            
            # Chercher les indices de prénoms composés
            potential_first_names = []
            potential_last_names = []
            
            # Assumer que le premier mot est le nom de famille
            potential_last_names.append(words[0])
            
            # Le reste pourrait être le prénom
            remaining_words = words[1:]
            
            # Vérifier si il y a des particules
            i = 1
            while i < len(words) and words[i].lower() in particles:
                potential_last_names.append(words[i])
                i += 1
            
            # Le reste est le prénom
            if i < len(words):
                potential_first_names = words[i:]
            
            last_name = " ".join(potential_last_names)
            first_name = " ".join(potential_first_names)
            
            return first_name.strip(), last_name.strip()
    
    def extract_specializations(self, spec_cell):
        """
        Extrait les spécialisations
        """
        specializations = []
        
        # Chercher les listes
        ul_elements = spec_cell.find_all('ul')
        for ul in ul_elements:
            for li in ul.find_all('li'):
                spec_text = li.get_text().strip()
                if spec_text and spec_text != '-':
                    specializations.append(spec_text)
        
        # Si pas de liste, chercher le texte direct
        if not specializations:
            spec_text = spec_cell.get_text().strip()
            if spec_text and spec_text not in ['-', '']:
                # Diviser par des délimiteurs potentiels
                for delimiter in [';', ',', '|', '\n']:
                    if delimiter in spec_text:
                        specs = [s.strip() for s in spec_text.split(delimiter)]
                        specializations.extend([s for s in specs if s and s != '-'])
                        break
                else:
                    specializations.append(spec_text)
                
        return [s for s in specializations if s.strip() and s.strip() != '-']
    
    def scrape_lawyers(self, max_lawyers=None):
        """
        Scrape les données des avocats
        """
        total_text = "tous les" if max_lawyers is None else str(max_lawyers)
        print(f"🔍 Extraction de {total_text} avocats du barreau de Chambéry...")
        print(f"📡 URL: {self.base_url}")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver le tableau
            table = soup.find('table', {'id': 'data_table'})
            if not table:
                print("❌ Tableau des avocats non trouvé")
                return False
                
            tbody = table.find('tbody')
            if not tbody:
                print("❌ Corps du tableau non trouvé")
                return False
                
            rows = tbody.find_all('tr')
            total_found = len(rows)
            print(f"📊 {total_found} avocats trouvés au total")
            
            # Déterminer combien extraire
            if max_lawyers is None:
                rows_to_process = rows
                print(f"🎯 Extraction de tous les avocats...")
            else:
                rows_to_process = rows[:max_lawyers]
                print(f"🎯 Extraction des {len(rows_to_process)} premiers...")
            
            # Extraire
            for i, row in enumerate(rows_to_process):
                try:
                    cells = row.find_all('td')
                    if len(cells) < 7:
                        print(f"⚠️  Ligne {i+1}: Nombre de cellules insuffisant ({len(cells)})")
                        continue
                        
                    # Extraction propre du nom et cabinet
                    lawyer_name, firm = self.clean_name_and_firm(cells[0])
                    prenom, nom = self.separate_first_last_name(lawyer_name)
                    
                    # Autres données
                    specializations = self.extract_specializations(cells[1])
                    address = cells[2].get_text().strip()
                    city = cells[3].get_text().strip()
                    phone = cells[4].get_text().strip()
                    email = cells[5].get_text().strip()
                    oath_year = cells[6].get_text().strip()
                    
                    activities = ""
                    if len(cells) > 7:
                        activities = cells[7].get_text().strip()
                    
                    lawyer_data = {
                        "numero": i + 1,
                        "nom_complet": lawyer_name,
                        "prenom": prenom,
                        "nom": nom,
                        "structure": firm,
                        "specialisations": specializations,
                        "specialisations_str": " | ".join(specializations) if specializations else "",
                        "activites_dominantes": activities,
                        "adresse": address,
                        "ville": city,
                        "telephone": phone,
                        "email": email,
                        "annee_serment": oath_year,
                        "source": self.base_url
                    }
                    
                    self.lawyers.append(lawyer_data)
                    
                    # Affichage propre
                    structure_display = f" - {firm}" if firm else ""
                    specs_display = f" ({', '.join(specializations[:2])})" if specializations else ""
                    print(f"✅ {i+1:3d}. {prenom} {nom}{structure_display}{specs_display}")
                    
                except Exception as e:
                    print(f"❌ Erreur ligne {i+1}: {e}")
                    continue
                    
            return True
            
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            return False
    
    def save_results(self, prefix="CHAMBERY_CORRECTED"):
        """
        Sauvegarde les résultats
        """
        if not self.lawyers:
            print("❌ Aucun avocat à sauvegarder")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_filename = f"{prefix}_{len(self.lawyers)}avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['numero', 'prenom', 'nom', 'nom_complet', 'structure', 
                         'specialisations_str', 'activites_dominantes', 'adresse', 
                         'ville', 'telephone', 'email', 'annee_serment', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers:
                row = {k: v for k, v in lawyer.items() if k != 'specialisations'}
                writer.writerow(row)
        
        # JSON
        json_filename = f"{prefix}_{len(self.lawyers)}avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails
        emails = [lawyer['email'] for lawyer in self.lawyers if lawyer['email'] and lawyer['email'].strip()]
        unique_emails = sorted(set(emails))
        email_filename = f"{prefix}_EMAILS_{len(unique_emails)}uniques_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as emailfile:
            for email in unique_emails:
                emailfile.write(f"{email}\n")
        
        # Rapport détaillé
        report_filename = f"{prefix}_RAPPORT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"RAPPORT CORRIGÉ - BARREAU DE CHAMBÉRY\n")
            reportfile.write(f"{'='*50}\n\n")
            reportfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"Source: {self.base_url}\n")
            reportfile.write(f"Avocats extraits: {len(self.lawyers)}\n")
            reportfile.write(f"Emails uniques: {len(unique_emails)}\n")
            reportfile.write(f"Avec structures: {sum(1 for l in self.lawyers if l['structure'])}\n")
            reportfile.write(f"Avec spécialisations: {sum(1 for l in self.lawyers if l['specialisations'])}\n\n")
            
            # Top spécialisations
            all_specs = []
            for lawyer in self.lawyers:
                all_specs.extend(lawyer.get('specialisations', []))
            
            from collections import Counter
            spec_counts = Counter(all_specs)
            
            reportfile.write(f"SPÉCIALISATIONS ({len(spec_counts)} types):\n")
            reportfile.write(f"{'-'*40}\n")
            for spec, count in spec_counts.most_common(10):
                reportfile.write(f"• {spec}: {count}\n")
            
            # Structures les plus fréquentes
            structures = [l['structure'] for l in self.lawyers if l['structure']]
            struct_counts = Counter(structures)
            
            reportfile.write(f"\nSTRUCTURES PRINCIPALES ({len(struct_counts)} types):\n")
            reportfile.write(f"{'-'*40}\n")
            for struct, count in struct_counts.most_common(10):
                reportfile.write(f"• {struct}: {count}\n")
            
            reportfile.write(f"\nÉCHANTILLON:\n")
            reportfile.write(f"{'-'*20}\n")
            for lawyer in self.lawyers[:10]:
                reportfile.write(f"• {lawyer['prenom']} {lawyer['nom']}")
                if lawyer['structure']:
                    reportfile.write(f" ({lawyer['structure']})")
                reportfile.write(f" - {lawyer['email']}\n")
        
        print(f"\n✅ Fichiers générés:")
        print(f"   📄 CSV: {csv_filename}")
        print(f"   📋 JSON: {json_filename}")
        print(f"   📧 Emails: {email_filename}")
        print(f"   📊 Rapport: {report_filename}")

def main():
    print("🚀 SCRAPER CORRIGÉ - BARREAU DE CHAMBÉRY")
    print("="*50)
    
    scraper = ChamberyCorrectScraper()
    
    # Test d'abord avec 20 avocats
    print("Phase 1: Test avec 20 avocats")
    success = scraper.scrape_lawyers(max_lawyers=20)
    
    if success and scraper.lawyers:
        print(f"\n✅ Test réussi - {len(scraper.lawyers)} avocats")
        scraper.save_results(prefix="CHAMBERY_TEST_CORRECTED")
        
        print("\nAperçu du résultat:")
        for i, lawyer in enumerate(scraper.lawyers[:5]):
            print(f"{i+1}. {lawyer['prenom']} {lawyer['nom']} - {lawyer['structure']} - {lawyer['email']}")
        
        # Demander confirmation pour extraction complète
        print(f"\n" + "="*50)
        print("Test terminé avec succès!")
        print("Pour extraire tous les avocats, relancez avec max_lawyers=None")
    else:
        print("❌ Test échoué")

if __name__ == "__main__":
    main()