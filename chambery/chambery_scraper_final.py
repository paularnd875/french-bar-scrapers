#!/usr/bin/env python3
"""
SCRIPT DE PRODUCTION FINAL - BARREAU DE CHAMBÉRY
Extraction complète de tous les avocats en mode headless
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from datetime import datetime
import time
import sys

class ChamberyProductionScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-chambery.fr/annuaire/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.lawyers = []
        
    def normalize_name(self, name):
        """
        Normalise les noms (première lettre majuscule, reste minuscule)
        """
        if not name:
            return ""
        
        # Cas particuliers
        particles = ['de', 'du', 'des', 'de la', 'van', 'von', 'le', 'la', 'd\'']
        
        words = name.split()
        normalized_words = []
        
        for word in words:
            if word.lower() in particles:
                normalized_words.append(word.lower())
            else:
                # Première lettre majuscule, reste minuscule sauf pour les noms composés avec tiret
                if '-' in word:
                    parts = word.split('-')
                    normalized_parts = [part.capitalize() for part in parts]
                    normalized_words.append('-'.join(normalized_parts))
                else:
                    normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def clean_name_and_firm(self, name_cell):
        """
        Nettoie et sépare le nom de l'avocat de sa structure
        """
        html_content = str(name_cell)
        
        # Gérer les différentes variantes de <br>
        if '<br>' in html_content or '<br/>' in html_content:
            html_content = re.sub(r'<br\s*/?>', '||SEPARATOR||', html_content, flags=re.IGNORECASE)
            parts = html_content.split('||SEPARATOR||')
            
            if len(parts) >= 2:
                lawyer_raw = BeautifulSoup(parts[0], 'html.parser').get_text().strip()
                firm_raw = BeautifulSoup(parts[1], 'html.parser').get_text().strip()
            else:
                lawyer_raw = name_cell.get_text().strip()
                firm_raw = ""
        else:
            # Pas de séparation, tout est le nom
            lawyer_raw = name_cell.get_text().strip()
            firm_raw = ""
        
        return lawyer_raw, firm_raw
    
    def separate_first_last_name(self, full_name):
        """
        Sépare prénom et nom avec gestion des cas complexes
        """
        full_name = re.sub(r'\s+', ' ', full_name.strip())
        
        if not full_name:
            return "", ""
            
        words = full_name.split()
        
        if len(words) == 1:
            return "", words[0]  # Seulement un nom
        elif len(words) == 2:
            # Format standard "NOM Prénom"
            return self.normalize_name(words[1]), self.normalize_name(words[0])
        else:
            # Plus de 2 mots - analyser
            
            # Particules qui font partie du nom de famille
            particles = ['de', 'du', 'des', 'de la', 'van', 'von', 'le', 'la', 'd\'', 'di', 'da']
            
            # Stratégie: le premier mot est le nom de famille
            # Chercher s'il y a des particules qui suivent
            lastname_parts = [words[0]]
            firstname_start_idx = 1
            
            # Vérifier les particules
            while firstname_start_idx < len(words) and words[firstname_start_idx].lower() in particles:
                lastname_parts.append(words[firstname_start_idx])
                firstname_start_idx += 1
            
            # Le reste constitue le prénom
            if firstname_start_idx < len(words):
                firstname_parts = words[firstname_start_idx:]
            else:
                firstname_parts = []
            
            lastname = self.normalize_name(' '.join(lastname_parts))
            firstname = self.normalize_name(' '.join(firstname_parts))
            
            return firstname, lastname
    
    def extract_specializations(self, spec_cell):
        """
        Extrait les spécialisations avec nettoyage
        """
        specializations = []
        
        # Chercher les listes à puces
        ul_elements = spec_cell.find_all('ul')
        for ul in ul_elements:
            for li in ul.find_all('li'):
                spec_text = li.get_text().strip()
                if spec_text and spec_text != '-':
                    specializations.append(spec_text)
        
        # Si pas de liste, traiter le texte brut
        if not specializations:
            spec_text = spec_cell.get_text().strip()
            if spec_text and spec_text not in ['-', '', 'Aucune']:
                # Gérer les séparateurs multiples
                for separator in [';', ',', '|', '\n', '•']:
                    if separator in spec_text:
                        parts = spec_text.split(separator)
                        for part in parts:
                            part = part.strip()
                            if part and part not in ['-', '']:
                                specializations.append(part)
                        break
                else:
                    # Pas de séparateur trouvé, prendre tel quel
                    specializations.append(spec_text)
        
        # Nettoyer et déduplicater
        clean_specs = []
        for spec in specializations:
            spec = spec.strip()
            if spec and spec not in ['-', '', 'Aucune'] and spec not in clean_specs:
                clean_specs.append(spec)
        
        return clean_specs
    
    def scrape_all_lawyers(self):
        """
        Extrait tous les avocats du barreau
        """
        print("🚀 EXTRACTION COMPLÈTE - BARREAU DE CHAMBÉRY")
        print("=" * 60)
        print(f"📡 URL: {self.base_url}")
        print("⏱️  Démarrage de l'extraction...")
        
        start_time = time.time()
        
        try:
            # Récupérer la page
            print("📥 Téléchargement de la page...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            print("🔍 Analyse de la structure HTML...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Trouver le tableau
            table = soup.find('table', {'id': 'data_table'})
            if not table:
                print("❌ ERREUR: Tableau des avocats non trouvé")
                return False
                
            tbody = table.find('tbody')
            if not tbody:
                print("❌ ERREUR: Corps du tableau non trouvé")
                return False
                
            rows = tbody.find_all('tr')
            total_lawyers = len(rows)
            print(f"📊 {total_lawyers} avocats détectés")
            print("🔄 Extraction en cours...")
            
            # Progress tracking
            progress_step = max(1, total_lawyers // 20)  # 20 points de progression
            
            # Extraire chaque avocat
            for i, row in enumerate(rows):
                try:
                    # Affichage du progrès
                    if i % progress_step == 0 or i == total_lawyers - 1:
                        percentage = (i + 1) / total_lawyers * 100
                        print(f"📈 Progression: {i+1}/{total_lawyers} ({percentage:.1f}%)")
                    
                    cells = row.find_all('td')
                    if len(cells) < 7:
                        print(f"⚠️  Ligne {i+1}: Cellules insuffisantes ({len(cells)})")
                        continue
                        
                    # Extraction des données
                    lawyer_name, firm = self.clean_name_and_firm(cells[0])
                    prenom, nom = self.separate_first_last_name(lawyer_name)
                    
                    specializations = self.extract_specializations(cells[1])
                    address = cells[2].get_text().strip()
                    city = cells[3].get_text().strip()
                    phone = cells[4].get_text().strip()
                    email = cells[5].get_text().strip()
                    oath_year = cells[6].get_text().strip()
                    
                    # Activités dominantes (optionnel)
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
                    
                except Exception as e:
                    print(f"❌ Erreur ligne {i+1}: {e}")
                    continue
            
            extraction_time = time.time() - start_time
            
            print(f"\n✅ EXTRACTION TERMINÉE!")
            print(f"⏱️  Temps d'exécution: {extraction_time:.2f} secondes")
            print(f"📊 Résultats: {len(self.lawyers)}/{total_lawyers} avocats extraits")
            
            return True
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE: {e}")
            return False
    
    def save_production_results(self):
        """
        Sauvegarde complète des résultats de production
        """
        if not self.lawyers:
            print("❌ Aucune donnée à sauvegarder")
            return
            
        print("\n💾 Sauvegarde des résultats...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV principal
        csv_filename = f"CHAMBERY_PRODUCTION_FINAL_{len(self.lawyers)}avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['numero', 'prenom', 'nom', 'nom_complet', 'structure', 
                         'specialisations_str', 'activites_dominantes', 'adresse', 
                         'ville', 'telephone', 'email', 'annee_serment', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers:
                row = {k: v for k, v in lawyer.items() if k != 'specialisations'}
                writer.writerow(row)
        
        # JSON complet
        json_filename = f"CHAMBERY_PRODUCTION_FINAL_{len(self.lawyers)}avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails = [lawyer['email'] for lawyer in self.lawyers if lawyer['email'] and lawyer['email'].strip()]
        unique_emails = sorted(set(emails))
        email_filename = f"CHAMBERY_EMAILS_FINAUX_{len(unique_emails)}uniques_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as emailfile:
            for email in unique_emails:
                emailfile.write(f"{email}\n")
        
        # Rapport de production détaillé
        report_filename = f"CHAMBERY_RAPPORT_PRODUCTION_FINAL_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write("RAPPORT DE PRODUCTION - BARREAU DE CHAMBÉRY\n")
            reportfile.write("=" * 60 + "\n\n")
            reportfile.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"URL source: {self.base_url}\n")
            reportfile.write(f"Total avocats extraits: {len(self.lawyers)}\n")
            reportfile.write(f"Emails uniques récupérés: {len(unique_emails)}\n")
            
            # Statistiques
            with_structures = sum(1 for l in self.lawyers if l['structure'])
            with_specs = sum(1 for l in self.lawyers if l['specialisations'])
            with_phones = sum(1 for l in self.lawyers if l['telephone'] and l['telephone'].strip())
            with_addresses = sum(1 for l in self.lawyers if l['adresse'] and l['adresse'].strip())
            
            reportfile.write(f"Avocats avec structure: {with_structures} ({with_structures/len(self.lawyers)*100:.1f}%)\n")
            reportfile.write(f"Avocats avec spécialisations: {with_specs} ({with_specs/len(self.lawyers)*100:.1f}%)\n")
            reportfile.write(f"Avocats avec téléphone: {with_phones} ({with_phones/len(self.lawyers)*100:.1f}%)\n")
            reportfile.write(f"Avocats avec adresse: {with_addresses} ({with_addresses/len(self.lawyers)*100:.1f}%)\n\n")
            
            # Top spécialisations
            all_specs = []
            for lawyer in self.lawyers:
                all_specs.extend(lawyer.get('specialisations', []))
            
            from collections import Counter
            spec_counts = Counter(all_specs)
            
            reportfile.write(f"SPÉCIALISATIONS DÉTECTÉES ({len(spec_counts)} types):\n")
            reportfile.write("-" * 50 + "\n")
            for spec, count in spec_counts.most_common(15):
                reportfile.write(f"• {spec}: {count} avocat(s)\n")
            
            # Top structures
            structures = [l['structure'] for l in self.lawyers if l['structure']]
            struct_counts = Counter(structures)
            
            reportfile.write(f"\nSTRUCTURES LES PLUS FRÉQUENTES ({len(struct_counts)} types):\n")
            reportfile.write("-" * 50 + "\n")
            for struct, count in struct_counts.most_common(10):
                reportfile.write(f"• {struct}: {count} avocat(s)\n")
            
            # Années de serment
            oath_years = [l['annee_serment'] for l in self.lawyers if l['annee_serment'] and l['annee_serment'].isdigit()]
            if oath_years:
                oath_years = sorted([int(y) for y in oath_years])
                reportfile.write(f"\nANNÉES DE SERMENT:\n")
                reportfile.write("-" * 20 + "\n")
                reportfile.write(f"Plus ancienne: {min(oath_years)}\n")
                reportfile.write(f"Plus récente: {max(oath_years)}\n")
                reportfile.write(f"Médiane: {oath_years[len(oath_years)//2]}\n")
            
            reportfile.write(f"\nFICHIERS GÉNÉRÉS:\n")
            reportfile.write("-" * 20 + "\n")
            reportfile.write(f"• CSV: {csv_filename}\n")
            reportfile.write(f"• JSON: {json_filename}\n")
            reportfile.write(f"• Emails: {email_filename}\n")
            reportfile.write(f"• Rapport: {report_filename}\n")
        
        print("✅ Sauvegarde terminée!")
        print(f"📄 CSV: {csv_filename}")
        print(f"📋 JSON: {json_filename}")
        print(f"📧 Emails: {email_filename} ({len(unique_emails)} uniques)")
        print(f"📊 Rapport: {report_filename}")

def main():
    """
    Fonction principale de production
    """
    scraper = ChamberyProductionScraper()
    
    # Lancer l'extraction complète
    success = scraper.scrape_all_lawyers()
    
    if success and scraper.lawyers:
        # Statistiques finales
        emails = sum(1 for l in scraper.lawyers if l['email'] and l['email'].strip())
        specs = sum(1 for l in scraper.lawyers if l['specialisations'])
        structures = sum(1 for l in scraper.lawyers if l['structure'])
        
        print(f"\n📈 STATISTIQUES FINALES:")
        print(f"   👥 Total avocats: {len(scraper.lawyers)}")
        print(f"   📧 Avec email: {emails}")
        print(f"   🎯 Avec spécialisations: {specs}")
        print(f"   🏢 Avec structures: {structures}")
        
        # Sauvegarder
        scraper.save_production_results()
        
        print("\n🎉 MISSION ACCOMPLIE!")
        print("Toutes les données du barreau de Chambéry ont été extraites avec succès.")
        
    else:
        print("\n❌ ÉCHEC DE L'EXTRACTION")
        sys.exit(1)

if __name__ == "__main__":
    main()