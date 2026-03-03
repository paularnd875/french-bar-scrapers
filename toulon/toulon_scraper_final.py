#!/usr/bin/env python3
"""
Scraper Barreau de Toulon - Script final optimisé
Extrait tous les avocats de l'annuaire https://barreautoulon.fr/avocats/annuaire/
avec informations complètes : nom, prénom, email, téléphone, spécialisations, source URL, etc.

Usage: python3 toulon_scraper_final.py [limite]
Exemple: python3 toulon_scraper_final.py 100  # Pour limiter à 100 avocats
"""

import requests
import json
import csv
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import sys

class ToulonScraper:
    def __init__(self, limit=None):
        self.base_url = "https://barreautoulon.fr/avocats/annuaire/"
        self.limit = limit
        self.avocats = []
        self.errors = []
        
        # Session avec headers réalistes
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        print(f"🚀 SCRAPER BARREAU DE TOULON")
        print(f"🎯 Limite: {limit if limit else 'Aucune (extraction complète)'}")

    def parse_name(self, full_name):
        """Parse le nom complet en prénom et nom"""
        if not full_name:
            return "", ""
        
        name = re.sub(r'\s+', ' ', full_name.strip())
        name = re.sub(r'^(Maître|Me|M\.|Mme|Mlle)\s+', '', name, flags=re.IGNORECASE)
        
        if 'cabinet' in name.lower():
            return "", name
        
        parts = name.split()
        if len(parts) == 1:
            return "", parts[0]
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            return parts[0], " ".join(parts[1:])

    def extract_avocat_info(self, avocat_div):
        """Extrait toutes les informations d'un avocat depuis son div"""
        try:
            avocat_data = {
                'nom': '',
                'prenom': '',
                'nom_complet': '',
                'annee_inscription': '',
                'specialisations': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'email': '',
                'source_url': ''
            }
            
            text_content = avocat_div.get_text()
            
            # Nom depuis h2
            h2_element = avocat_div.find('h2')
            if h2_element:
                avocat_data['nom_complet'] = h2_element.get_text().strip()
            
            # Parse nom/prénom
            if avocat_data['nom_complet']:
                prenom, nom = self.parse_name(avocat_data['nom_complet'])
                avocat_data['prenom'] = prenom
                avocat_data['nom'] = nom
            
            # Email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_matches = re.findall(email_pattern, text_content)
            if email_matches:
                avocat_data['email'] = email_matches[0]
            
            # Téléphone
            phone_pattern = r'(\+33|0)[1-9](?:[0-9]{8})'
            phone_matches = re.findall(phone_pattern, text_content.replace(' ', '').replace('.', ''))
            if phone_matches:
                avocat_data['telephone'] = phone_matches[0]
            
            # Année d'inscription
            year_pattern = r'\b(19[0-9]{2}|20[0-3][0-9])\b'
            year_matches = re.findall(year_pattern, text_content)
            if year_matches:
                years = [int(y) for y in year_matches if 1980 <= int(y) <= 2025]
                if years:
                    avocat_data['annee_inscription'] = str(max(years))
            
            # Spécialisations depuis les classes CSS du parent
            parent_div = avocat_div.find_parent('div', class_=lambda x: x and 'fl-post-feed-post' in x)
            if parent_div and parent_div.get('class'):
                classes_str = ' '.join(parent_div.get('class', []))
                if 'specialite-' in classes_str:
                    spec_matches = re.findall(r'specialite-([^\s]+)', classes_str)
                    specializations = []
                    for match in spec_matches:
                        clean_spec = match.replace('-', ' ').replace('avocat', '').strip()
                        if len(clean_spec) > 3:
                            specializations.append(clean_spec.title())
                    if specializations:
                        avocat_data['specialisations'] = ', '.join(specializations)
            
            # Source URL depuis itemid
            if parent_div:
                itemid = parent_div.find('meta', attrs={'itemprop': 'mainEntityOfPage'})
                if itemid and itemid.get('itemid'):
                    avocat_data['source_url'] = itemid.get('itemid')
            
            # Structure (cabinet, SELAS, etc.)
            lines = text_content.split('\n')
            for line in lines:
                line = line.strip()
                if any(word in line.upper() for word in ['S.E.L.A.S', 'S.E.L.A.R.L', 'CABINET']):
                    avocat_data['structure'] = line
                    break
            
            return avocat_data
            
        except Exception as e:
            self.errors.append(f"Erreur extraction: {e}")
            return None

    def scrape_page(self, page_num):
        """Scrape une page de l'annuaire"""
        print(f"\n📄 Page {page_num}")
        
        url = f"{self.base_url}?sf_paged={page_num}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Recherche des avocats
            avocats_divs = soup.find_all('div', class_='avocat-item')
            
            if not avocats_divs:
                print("⚠️ Aucun avocat trouvé")
                return 0
            
            print(f"✅ {len(avocats_divs)} avocats trouvés")
            
            count = 0
            for avocat_div in avocats_divs:
                if self.limit and len(self.avocats) >= self.limit:
                    break
                    
                avocat_data = self.extract_avocat_info(avocat_div)
                
                if avocat_data and avocat_data['nom_complet']:
                    self.avocats.append(avocat_data)
                    count += 1
                    print(f"   📝 {len(self.avocats)}. {avocat_data['prenom']} {avocat_data['nom']}")
                    if avocat_data['email']:
                        print(f"      📧 {avocat_data['email']}")
            
            print(f"📊 {count} avocats extraits (Total: {len(self.avocats)})")
            return count
            
        except Exception as e:
            error_msg = f"Erreur page {page_num}: {e}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return 0

    def run_scraping(self):
        """Lance le scraping complet"""
        start_time = time.time()
        
        try:
            page = 1
            max_pages = 100  # Protection contre boucle infinie
            
            while page <= max_pages:
                count = self.scrape_page(page)
                if count == 0:
                    print("⚠️ Aucun avocat trouvé, arrêt du scraping")
                    break
                
                # Vérifier la limite
                if self.limit and len(self.avocats) >= self.limit:
                    print(f"🎯 Limite atteinte: {self.limit} avocats")
                    break
                    
                page += 1
                time.sleep(1)  # Pause entre pages
            
            duration = time.time() - start_time
            print(f"\n⏱️ Durée: {duration:.1f}s")
            print(f"📊 Total avocats collectés: {len(self.avocats)}")
            
            self.save_results()
            
        except Exception as e:
            print(f"❌ Erreur fatale: {e}")

    def save_results(self):
        """Sauvegarde les résultats en CSV, JSON et TXT"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_filename = f"TOULON_AVOCATS_{len(self.avocats)}_avocats_{timestamp}.csv"
        df = pd.DataFrame(self.avocats)
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"💾 CSV: {csv_filename}")
        
        # JSON
        json_filename = f"TOULON_AVOCATS_{len(self.avocats)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.avocats, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON: {json_filename}")
        
        # Emails uniquement
        emails = [a['email'] for a in self.avocats if a['email']]
        if emails:
            emails_filename = f"TOULON_AVOCATS_EMAILS_{len(emails)}emails_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as f:
                for email in emails:
                    f.write(f"{email}\n")
            print(f"📧 Emails: {emails_filename}")
        
        # Statistiques
        specs_count = len([a for a in self.avocats if a['specialisations']])
        sources_count = len([a for a in self.avocats if a['source_url']])
        years_count = len([a for a in self.avocats if a['annee_inscription']])
        phones_count = len([a for a in self.avocats if a['telephone']])
        structures_count = len([a for a in self.avocats if a['structure']])
        
        print(f"\n📊 STATISTIQUES FINALES:")
        print(f"   👥 Avocats total: {len(self.avocats)}")
        print(f"   📧 Emails: {len(emails)} ({len(emails)/len(self.avocats)*100:.1f}%)")
        print(f"   📞 Téléphones: {phones_count} ({phones_count/len(self.avocats)*100:.1f}%)")
        print(f"   📅 Années: {years_count} ({years_count/len(self.avocats)*100:.1f}%)")
        print(f"   🎯 Spécialisations: {specs_count} ({specs_count/len(self.avocats)*100:.1f}%)")
        print(f"   🏢 Structures: {structures_count} ({structures_count/len(self.avocats)*100:.1f}%)")
        print(f"   🔗 Sources: {sources_count} ({sources_count/len(self.avocats)*100:.1f}%)")
        
        if self.errors:
            print(f"\n⚠️ {len(self.errors)} erreurs détectées")

def main():
    # Gestion des arguments
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"🎯 Limite définie: {limit} avocats")
        except ValueError:
            print("⚠️ Argument invalide, scraping complet par défaut")
    
    # Lancement du scraping
    scraper = ToulonScraper(limit=limit)
    scraper.run_scraping()

if __name__ == "__main__":
    main()