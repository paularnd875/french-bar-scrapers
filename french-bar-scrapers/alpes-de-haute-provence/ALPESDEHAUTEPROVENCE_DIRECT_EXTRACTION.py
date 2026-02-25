#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper CORRECT pour l'annuaire des avocats du Barreau des Alpes de Haute-Provence
EXTRACTION DIRECTE depuis la page d'annuaire (pas de navigation vers pages individuelles)
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

class AlpesDeHauteProvenceDirectExtraction:
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

    def extract_all_lawyers_directly(self):
        """Extraction directe de tous les avocats depuis la page d'annuaire"""
        try:
            print("🔍 Chargement de l'annuaire...")
            self.driver.get(self.annuaire_url)
            
            # Attendre le chargement
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(8)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Sauvegarder pour debug
            with open('debug_direct_extraction.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            # Trouver toutes les fiches d'avocats
            lawyer_cards = soup.find_all('div', class_=['annuaireFicheMini', 'annuaireFicheMiniAvocat'])
            print(f"📋 {len(lawyer_cards)} fiches trouvées")
            
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
                    
                    # Extraire l'année d'inscription (prestation de serment)
                    date_serment_div = card.find('div', class_='annuaireFicheDateSerment')
                    if date_serment_div:
                        # Le texte est du type "Prestation de serment : 1972"
                        serment_text = date_serment_div.get_text(strip=True)
                        # Extraire l'année (4 chiffres consécutifs)
                        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', serment_text)
                        if year_match:
                            lawyer_data['annee_inscription'] = year_match.group(1)
                    
                    # Si on a au moins un nom valide, ajouter l'avocat
                    if full_name and len(full_name) > 3:
                        lawyers.append(lawyer_data)
                        
                        # Log les informations trouvées
                        info_found = []
                        if lawyer_data['telephone']:
                            info_found.append(f"📞 {lawyer_data['telephone']}")
                        if lawyer_data['adresse']:
                            info_found.append(f"🏠 {lawyer_data['adresse'][:50]}...")
                        if lawyer_data['annee_inscription']:
                            info_found.append(f"📅 {lawyer_data['annee_inscription']}")
                        if lawyer_data['specialisations']:
                            info_found.append(f"⚖️ {lawyer_data['specialisations']}")
                        
                        info_str = " | ".join(info_found) if info_found else "❌ Aucune info supplémentaire"
                        print(f"{i+1:2d}. {full_name:<30} → {info_str}")
                        
                except Exception as e:
                    print(f"❌ Erreur carte {i+1}: {e}")
                    continue
            
            print(f"\n✅ {len(lawyers)} avocats extraits avec succès")
            
            # Limiter en mode test
            if self.mode == "test" and len(lawyers) > 20:
                lawyers = lawyers[:20]
                print(f"🧪 Mode test: limitation à {len(lawyers)} avocats")
            elif self.mode == "production":
                print(f"📊 Mode production: extraction de tous les {len(lawyers)} avocats")
            
            return lawyers
            
        except Exception as e:
            print(f"❌ Erreur extraction: {e}")
            return []

    def save_results(self, data):
        """Sauvegarde des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_str = self.mode.upper()
        
        # CSV
        df = pd.DataFrame(data)
        csv_file = f"ALPES_DIRECT_{mode_str}_{len(data)}avocats_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # JSON
        json_file = f"ALPES_DIRECT_{mode_str}_{len(data)}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails = [l['email'] for l in data if l['email']]
        phones = [l['telephone'] for l in data if l['telephone']]
        years = [l['annee_inscription'] for l in data if l['annee_inscription']]
        
        emails_file = f"ALPES_DIRECT_{mode_str}_EMAILS_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            if emails:
                f.write("\n".join(emails))
            else:
                f.write("Aucun email trouvé")
        
        # Rapport
        report_file = f"ALPES_DIRECT_{mode_str}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT EXTRACTION DIRECTE - ALPES DE HAUTE-PROVENCE ({mode_str})\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Avocats traités: {len(data)}\n")
            f.write(f"Téléphones trouvés: {len(phones)} ({len(phones)/len(data)*100:.1f}%)\n")
            f.write(f"Adresses trouvées: {sum(1 for l in data if l['adresse'])} ({sum(1 for l in data if l['adresse'])/len(data)*100:.1f}%)\n")
            f.write(f"Années inscription: {len(years)} ({len(years)/len(data)*100:.1f}%)\n")
            f.write(f"Emails trouvés: {len(emails)} ({len(emails)/len(data)*100:.1f}%)\n\n")
            
            if phones:
                f.write("TÉLÉPHONES TROUVÉS:\n")
                for phone in phones:
                    f.write(f"- {phone}\n")
                f.write("\n")
            
            if emails:
                f.write("EMAILS TROUVÉS:\n")
                for email in emails:
                    f.write(f"- {email}\n")
            else:
                f.write("Aucun email trouvé dans l'annuaire principal\n")
                f.write("Les emails pourraient être disponibles sur les pages individuelles\n")
        
        print(f"\n📁 FICHIERS CRÉÉS:")
        print(f"   📊 {csv_file}")
        print(f"   📄 {json_file}")
        print(f"   📧 {emails_file}")
        print(f"   📋 {report_file}")

    def run(self):
        """Processus principal"""
        print("🚀 SCRAPER DIRECT - ALPES DE HAUTE-PROVENCE")
        print(f"📋 Mode: {self.mode.upper()}")
        print("=" * 55)
        
        if not self.setup_driver():
            return False
        
        try:
            # Extraire directement tous les avocats
            lawyers = self.extract_all_lawyers_directly()
            if not lawyers:
                print("❌ Aucun avocat trouvé")
                return False
            
            self.lawyers_data = lawyers
            
            # Sauvegarder
            self.save_results(self.lawyers_data)
            
            # Statistiques
            emails = sum(1 for l in self.lawyers_data if l.get('email'))
            phones = sum(1 for l in self.lawyers_data if l.get('telephone'))
            addresses = sum(1 for l in self.lawyers_data if l.get('adresse'))
            years = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
            
            print(f"\n🎉 EXTRACTION TERMINÉE!")
            print(f"📊 {len(self.lawyers_data)} avocats traités")
            print(f"📧 {emails} emails trouvés ({emails/len(self.lawyers_data)*100:.1f}%)")
            print(f"📞 {phones} téléphones trouvés ({phones/len(self.lawyers_data)*100:.1f}%)")
            print(f"🏠 {addresses} adresses trouvées ({addresses/len(self.lawyers_data)*100:.1f}%)")
            print(f"📅 {years} années inscription trouvées ({years/len(self.lawyers_data)*100:.1f}%)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("=" * 60)
    print("SCRAPER ALPES DE HAUTE-PROVENCE - EXTRACTION DIRECTE")
    print("=" * 60)
    print("Cette version extrait les informations directement")
    print("depuis la page d'annuaire sans navigation individuelle")
    print()
    
    # Choix du mode
    choice = input("Mode (test/production) [test]: ").lower().strip()
    if not choice:
        choice = "test"
    
    scraper = AlpesDeHauteProvenceDirectExtraction(mode=choice)
    success = scraper.run()
    
    if success:
        print("\n✅ SUCCÈS! Vérifiez les fichiers générés.")
    else:
        print("\n❌ ÉCHEC! Consultez les messages d'erreur.")

if __name__ == "__main__":
    main()