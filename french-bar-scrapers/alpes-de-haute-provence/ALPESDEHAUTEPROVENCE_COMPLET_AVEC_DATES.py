#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper COMPLET avec ANNÉES D'INSCRIPTION pour les Alpes de Haute-Provence
Version hybride qui extrait les infos de base depuis l'annuaire 
puis visite les pages individuelles pour récupérer les années d'inscription
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from datetime import datetime
import os

class AlpesDeHauteProvenceCompletAvecDates:
    def __init__(self, mode="test"):
        self.base_url = "https://www.avocats04.fr"
        self.annuaire_url = "https://www.avocats04.fr/le-barreau/annuaire-des-avocats.htm"
        self.lawyers_data = []
        self.driver = None
        self.mode = mode
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Driver Chrome configuré")
            return True
        except Exception as e:
            print(f"❌ Erreur driver: {e}")
            return False

    def extract_lawyers_from_listing(self):
        """Phase 1: Extraction rapide depuis l'annuaire principal"""
        try:
            print("🔍 Phase 1: Extraction depuis l'annuaire principal...")
            self.driver.get(self.annuaire_url)
            
            # Attendre le chargement
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(8)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Sauvegarder pour debug
            with open('debug_complet_avec_dates.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Trouver toutes les fiches d'avocats
            lawyer_cards = soup.find_all('div', class_=['annuaireFicheMini', 'annuaireFicheMiniAvocat'])
            print(f"📋 {len(lawyer_cards)} fiches trouvées dans l'annuaire")
            
            lawyers = []
            for i, card in enumerate(lawyer_cards):
                try:
                    # Extraire le nom depuis l'en-tête
                    name_link = card.find('h4')
                    if not name_link:
                        continue
                    
                    link_elem = name_link.find('a')
                    if not link_elem:
                        continue
                    
                    # Extraire les composants du nom
                    civilite_elem = link_elem.find('span', class_='anfiche_civ')
                    prenom_elem = link_elem.find('span', class_='anfiche_prenom') 
                    nom_elem = link_elem.find('span', class_='anfiche_nom')
                    
                    civilite = civilite_elem.get_text(strip=True) if civilite_elem else ""
                    prenom = prenom_elem.get_text(strip=True) if prenom_elem else ""
                    nom = nom_elem.get_text(strip=True) if nom_elem else ""
                    
                    full_name = f"{civilite} {prenom} {nom}".strip()
                    
                    # URL du profil
                    profile_url = link_elem.get('href', '')
                    if profile_url and not profile_url.startswith('http'):
                        profile_url = f"{self.base_url}/{profile_url.lstrip('/')}"
                    
                    # Extraire les coordonnées directement de la carte
                    coordonnees = card.find('div', class_='coordonnees')
                    
                    # Initialiser les données
                    lawyer_data = {
                        'prenom': prenom,
                        'nom': nom, 
                        'nom_complet': full_name,
                        'annee_inscription': '',
                        'specialisations': '',
                        'competences': '',
                        'activites_dominantes': '',
                        'structure': '',
                        'adresse': '',
                        'telephone': '',
                        'email': '',
                        'fax': '',
                        'source_url': profile_url
                    }
                    
                    if coordonnees:
                        # Extraire l'adresse
                        adresse_parts = []
                        adresse_divs = coordonnees.find_all('div', class_='adresse')
                        for adresse_div in adresse_divs:
                            adresse_text = adresse_div.get_text(strip=True)
                            if adresse_text:
                                adresse_parts.append(adresse_text)
                        
                        # Ajouter ville/code postal
                        cpville_div = coordonnees.find('div', class_='cpville')
                        if cpville_div:
                            cpville = cpville_div.get_text(strip=True)
                            if cpville:
                                adresse_parts.append(cpville)
                        
                        lawyer_data['adresse'] = ', '.join(adresse_parts)
                        
                        # Extraire le téléphone
                        tel_divs = coordonnees.find_all('div', class_='tel')
                        for tel_div in tel_divs:
                            tel_text = tel_div.get_text(strip=True)
                            if tel_text and 'Tél' in tel_text:
                                # Extraire le numéro de téléphone
                                phone_match = re.search(r'[\+\d\s\(\)\.]{10,}', tel_text)
                                if phone_match:
                                    phone = re.sub(r'[^\d\+]', '', phone_match.group())
                                    if len(phone) >= 10:
                                        lawyer_data['telephone'] = phone_match.group().strip()
                                        break
                    
                    # Extraire les spécialités/fonction s'il y en a
                    fonction_div = card.find('div', class_='fonction')
                    if fonction_div:
                        lawyer_data['specialisations'] = fonction_div.get_text(strip=True)
                    
                    # Si on a au moins un nom valide, ajouter l'avocat
                    if full_name and len(full_name) > 3:
                        lawyers.append(lawyer_data)
                        
                except Exception as e:
                    print(f"❌ Erreur carte {i+1}: {e}")
                    continue
            
            print(f"✅ Phase 1 terminée: {len(lawyers)} avocats extraits")
            
            # Limiter en mode test
            if self.mode == "test" and len(lawyers) > 15:
                lawyers = lawyers[:15]
                print(f"🧪 Mode test: limitation à {len(lawyers)} avocats pour les dates")
            elif self.mode == "production":
                print(f"📊 Mode production: enrichissement de tous les {len(lawyers)} avocats")
            
            return lawyers
            
        except Exception as e:
            print(f"❌ Erreur extraction listing: {e}")
            return []

    def extract_inscription_date(self, lawyer):
        """Phase 2: Extraire l'année d'inscription depuis la page individuelle"""
        try:
            if not lawyer['source_url']:
                return lawyer
            
            self.driver.get(lawyer['source_url'])
            time.sleep(random.uniform(1, 2))
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Chercher spécifiquement la div annuaireFicheDateSerment
            date_serment_div = soup.find('div', class_='annuaireFicheDateSerment')
            if date_serment_div:
                # Le texte est du type "Prestation de serment : 1972"
                serment_text = date_serment_div.get_text(strip=True)
                # Extraire l'année (4 chiffres consécutifs)
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', serment_text)
                if year_match:
                    lawyer['annee_inscription'] = year_match.group(1)
                    return lawyer
            
            # Si pas trouvé avec la div spécifique, chercher dans tout le texte
            full_text = soup.get_text()
            year_patterns = [
                r'(?:prestation\\s+de\\s+serment|serment)\\s*:?\\s*(\\d{4})',
                r'(?:admis|inscrit).*?(\\d{4})',
                r'(\\d{4}).*?(?:serment|inscription)'
            ]
            
            for pattern in year_patterns:
                year_matches = re.findall(pattern, full_text, re.IGNORECASE)
                for year in year_matches:
                    if 1950 <= int(year) <= 2025:
                        lawyer['annee_inscription'] = year
                        return lawyer
            
            return lawyer
            
        except Exception as e:
            print(f"   ❌ Erreur page {lawyer['nom_complet']}: {e}")
            return lawyer

    def save_results(self, data):
        """Sauvegarde complète avec années d'inscription"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_str = self.mode.upper()
        
        # CSV
        df = pd.DataFrame(data)
        csv_file = f"ALPES_COMPLET_DATES_{mode_str}_{len(data)}avocats_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # JSON
        json_file = f"ALPES_COMPLET_DATES_{mode_str}_{len(data)}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Rapport détaillé
        emails = [l['email'] for l in data if l['email']]
        phones = [l['telephone'] for l in data if l['telephone']]
        years = [l['annee_inscription'] for l in data if l['annee_inscription']]
        addresses = [l['adresse'] for l in data if l['adresse']]
        
        report_file = f"ALPES_COMPLET_DATES_{mode_str}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT COMPLET AVEC DATES - ALPES DE HAUTE-PROVENCE ({mode_str})\\n")
            f.write("=" * 70 + "\\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\\n")
            f.write(f"URL source: {self.annuaire_url}\\n")
            f.write(f"Avocats traités: {len(data)}\\n")
            f.write(f"Téléphones: {len(phones)} ({len(phones)/len(data)*100:.1f}%)\\n")
            f.write(f"Adresses: {len(addresses)} ({len(addresses)/len(data)*100:.1f}%)\\n")
            f.write(f"Années inscription: {len(years)} ({len(years)/len(data)*100:.1f}%)\\n")
            f.write(f"Emails: {len(emails)} ({len(emails)/len(data)*100:.1f}%)\\n\\n")
            
            if years:
                f.write("ANNÉES D'INSCRIPTION TROUVÉES:\\n")
                f.write("-" * 40 + "\\n")
                for lawyer in data:
                    if lawyer['annee_inscription']:
                        f.write(f"- {lawyer['nom_complet']}: {lawyer['annee_inscription']}\\n")
                f.write("\\n")
            
            if phones:
                f.write("EXEMPLE D'AVOCATS AVEC COORDONNÉES COMPLÈTES:\\n")
                f.write("-" * 50 + "\\n")
                complete_lawyers = [l for l in data if l['telephone'] and l['adresse']]
                for i, lawyer in enumerate(complete_lawyers[:10], 1):
                    f.write(f"{i:2d}. {lawyer['nom_complet']}\\n")
                    f.write(f"    📞 {lawyer['telephone']}\\n")
                    f.write(f"    🏠 {lawyer['adresse']}\\n")
                    if lawyer['annee_inscription']:
                        f.write(f"    📅 Inscription: {lawyer['annee_inscription']}\\n")
                    if lawyer['specialisations']:
                        f.write(f"    ⚖️ {lawyer['specialisations']}\\n")
                    f.write("\\n")
        
        print(f"\\n📁 FICHIERS CRÉÉS:")
        print(f"   📊 {csv_file}")
        print(f"   📄 {json_file}")
        print(f"   📋 {report_file}")

    def run(self):
        """Processus principal hybride"""
        print("🚀 SCRAPER COMPLET AVEC DATES - ALPES DE HAUTE-PROVENCE")
        print(f"📋 Mode: {self.mode.upper()}")
        print("=" * 65)
        print("Phase 1: Extraction rapide depuis l'annuaire principal")
        print("Phase 2: Récupération des années d'inscription individuelles")
        print("=" * 65)
        
        if not self.setup_driver():
            return False
        
        try:
            # Phase 1: Extraction depuis l'annuaire
            lawyers = self.extract_lawyers_from_listing()
            if not lawyers:
                print("❌ Aucun avocat trouvé dans l'annuaire")
                return False
            
            print(f"\\n🔍 Phase 2: Enrichissement avec dates d'inscription...")
            print(f"📋 {len(lawyers)} avocats à traiter")
            
            # Phase 2: Enrichissement avec dates d'inscription
            for i, lawyer in enumerate(lawyers, 1):
                print(f"[{i}/{len(lawyers)}] {lawyer['nom_complet']:<35}", end="")
                
                enriched_lawyer = self.extract_inscription_date(lawyer)
                self.lawyers_data.append(enriched_lawyer)
                
                # Log du résultat
                if enriched_lawyer['annee_inscription']:
                    print(f" ✅ 📅 {enriched_lawyer['annee_inscription']}")
                else:
                    print(f" ❌ Pas de date")
                
                # Pause entre les requêtes
                if i < len(lawyers):
                    time.sleep(random.uniform(0.8, 1.5))
            
            # Sauvegarder
            self.save_results(self.lawyers_data)
            
            # Statistiques finales
            emails = sum(1 for l in self.lawyers_data if l.get('email'))
            phones = sum(1 for l in self.lawyers_data if l.get('telephone'))
            addresses = sum(1 for l in self.lawyers_data if l.get('adresse'))
            years = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
            
            print(f"\\n🎉 EXTRACTION COMPLÈTE TERMINÉE!")
            print(f"📊 {len(self.lawyers_data)} avocats traités")
            print(f"📞 {phones} téléphones ({phones/len(self.lawyers_data)*100:.1f}%)")
            print(f"🏠 {addresses} adresses ({addresses/len(self.lawyers_data)*100:.1f}%)")
            print(f"📅 {years} années inscription ({years/len(self.lawyers_data)*100:.1f}%)")
            print(f"📧 {emails} emails ({emails/len(self.lawyers_data)*100:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("=" * 70)
    print("SCRAPER ALPES DE HAUTE-PROVENCE - VERSION COMPLÈTE AVEC DATES")
    print("=" * 70)
    print("Cette version extrait TOUTES les informations disponibles:")
    print("✅ Noms (prénoms et noms séparés)")
    print("✅ Téléphones et adresses (extraction directe)")  
    print("✅ Années d'inscription (pages individuelles)")
    print("✅ Spécialités quand disponibles")
    print("❌ Emails (non disponibles publiquement)")
    print()
    
    # Mode production par défaut pour l'execution complète
    choice = "production"
    
    scraper = AlpesDeHauteProvenceCompletAvecDates(mode=choice)
    success = scraper.run()
    
    if success:
        print("\\n✅ SUCCÈS! Extraction complète terminée avec dates d'inscription.")
        print("📋 Toutes les informations disponibles ont été récupérées.")
    else:
        print("\\n❌ ÉCHEC! Consultez les messages d'erreur.")

if __name__ == "__main__":
    main()