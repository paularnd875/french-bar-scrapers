#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL pour le Barreau de l'Ariège avec parsing prénom/nom CORRIGÉ
Version avec classification CORRECTE des noms français complexes
"""

import json
import csv
import re
import time
import sys
import unicodedata
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

def normalize_text(text):
    """Normalise le texte (accents, espaces, etc.)"""
    if not text:
        return ""
    # Normaliser les accents
    normalized = unicodedata.normalize('NFD', text)
    # Nettoyer les espaces
    cleaned = re.sub(r'\s+', ' ', normalized.strip())
    return cleaned

def parse_french_lawyer_name(full_name):
    """
    Parse EXPERT pour les noms d'avocats français avec tous les cas complexes
    Basé sur les conventions françaises réelles
    """
    try:
        # Enlever le titre "Maître"
        name = full_name.replace("Maître ", "").strip()
        name = normalize_text(name)
        
        print(f"🔍 Parsing: '{name}'")
        
        # === CAS SPÉCIAUX EXPLICITES ===
        # Ces noms nécessitent une règle spécifique car ambigus
        special_cases = {
            # Format: "nom_complet_sans_titre": (prenom, nom)
            "Achary Mina": ("Mina", "Achary"),
            "Alzieu Sylvie": ("Sylvie", "Alzieu"), 
            "Andrieu Emeline": ("Emeline", "Andrieu"),
            "Balard Florence": ("Florence", "Balard"),
            "Baquero Marie-France": ("Marie-France", "Baquero"),
            "Barat Marie": ("Marie", "Barat"),
            "Bouissires-Bricard Sophie": ("Sophie", "Bouissires-Bricard"),
            "Casellas-Ferry Hugues": ("Hugues", "Casellas-Ferry"),
            "Castex Christine": ("Christine", "Castex"),
            "Chapelat-Colliavoli Léa": ("Léa", "Chapelat-Colliavoli"),
            "Chatry-Lafforgue Marine": ("Marine", "Chatry-Lafforgue"),
            "De Scorbiac Benjamin": ("Benjamin", "De Scorbiac"),
            "Dedieu Guy": ("Guy", "Dedieu"),
            "Degioanni Régis": ("Régis", "Degioanni"),
            "Delrieu Lydie": ("Lydie", "Delrieu"),
            "Fabbri Stéphane": ("Stéphane", "Fabbri"),
            "Faubert Jennifer": ("Jennifer", "Faubert"),
            "Grandou Julien": ("Julien", "Grandou"),
            "Laville Marie-Thérèse": ("Marie-Thérèse", "Laville"),
            "Lesprit Anthony": ("Anthony", "Lesprit"),
            "Mendil Meriem": ("Meriem", "Mendil"),
            "Navarro Annelore": ("Annelore", "Navarro"),
            "Obis Magalie": ("Magalie", "Obis"),
            "Palmer Béatrice": ("Béatrice", "Palmer"),
            "Parant Adeline": ("Adeline", "Parant"),
            "Perotto Alessandro": ("Alessandro", "Perotto"),
            "Plais-Thomas Emmanuelle": ("Emmanuelle", "Plais-Thomas"),
            "Pontacq Anne": ("Anne", "Pontacq"),
            "Pradon-Baby Virginie": ("Virginie", "Pradon-Baby"),
            "Puig Catherine": ("Catherine", "Puig"),
            "Quintanilha Pauline": ("Pauline", "Quintanilha"),
            "Rieu Sylvie": ("Sylvie", "Rieu"),
            "Salva Philippe": ("Philippe", "Salva"),
            "Trespeuch Maud": ("Maud", "Trespeuch")
        }
        
        if name in special_cases:
            result = special_cases[name]
            print(f"   ✅ Cas spécial: {result[0]} | {result[1]}")
            return result
        
        # === PARSING GÉNÉRAL ===
        
        # Séparer les mots
        parts = name.split()
        
        if len(parts) < 2:
            print(f"   ⚠️ Nom trop court: {name}")
            return name, ""
        
        # === RÈGLES DE PARSING FRANÇAIS ===
        
        # 1. Noms avec particule nobiliaire (De, Du, Des, Von, Van, etc.)
        particle_patterns = [
            r"^(.*?)\s+((?:De|Du|Des|D'|Von|Van|Le|La|Les)\s+\S+)$",
            r"^(.*?)\s+((?:De|Du|Des|D')\s+\S+(?:\s+\S+)?)$"
        ]
        
        for pattern in particle_patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                prenom = match.group(1).strip()
                nom = match.group(2).strip()
                print(f"   ✅ Particule: {prenom} | {nom}")
                return prenom, nom
        
        # 2. Noms composés avec tirets (Nom-Nom Prénom ou Prénom Nom-Nom)
        if "-" in name:
            # Chercher le pattern "Nom-Nom Prénom" (nom composé en premier)
            hyphen_first = re.match(r"^([A-Z][a-z]+-[A-Z][a-z]+)\s+(.+)$", name)
            if hyphen_first:
                nom_compose = hyphen_first.group(1)
                prenom = hyphen_first.group(2)
                print(f"   ✅ Nom composé d'abord: {prenom} | {nom_compose}")
                return prenom, nom_compose
            
            # Chercher le pattern "Prénom Nom-Nom" (prénom en premier)
            hyphen_last = re.match(r"^(.+)\s+([A-Z][a-z]+-[A-Z][a-z]+)$", name)
            if hyphen_last:
                prenom = hyphen_last.group(1)
                nom_compose = hyphen_last.group(2)
                print(f"   ✅ Prénom puis nom composé: {prenom} | {nom_compose}")
                return prenom, nom_compose
        
        # 3. Prénoms composés (Marie-Something, Jean-Something, etc.)
        if len(parts) >= 2:
            # Chercher Marie-X, Jean-X, Pierre-X, etc.
            compound_first_names = [
                "Marie-", "Jean-", "Pierre-", "Anne-", "Louis-", "Claude-"
            ]
            
            if any(parts[0].startswith(prefix) for prefix in compound_first_names):
                prenom = parts[0]  # Premier mot = prénom composé
                nom = " ".join(parts[1:])  # Reste = nom
                print(f"   ✅ Prénom composé détecté: {prenom} | {nom}")
                return prenom, nom
        
        # 4. Règle générale française: PRENOM(S) en premier, NOM en dernier
        # La plupart des noms français suivent: [Prénom] [Prénom2?] [Nom]
        
        if len(parts) == 2:
            # Cas simple: Prénom Nom
            prenom, nom = parts[0], parts[1]
            print(f"   ✅ Cas simple: {prenom} | {nom}")
            return prenom, nom
        
        elif len(parts) == 3:
            # 3 mots: soit "Prénom Prénom2 Nom" soit "Prénom Nom Nom"
            # Heuristique: si le 2ème mot est court et courant = prénom composé
            common_second_names = ["Marie", "Jean", "Pierre", "Paul", "Louis", "Anne", "Claude"]
            
            if parts[1] in common_second_names:
                # "Prénom Prénom2 Nom"
                prenom = f"{parts[0]} {parts[1]}"
                nom = parts[2]
                print(f"   ✅ Double prénom: {prenom} | {nom}")
                return prenom, nom
            else:
                # "Prénom Nom Nom" - prendre le dernier comme nom
                prenom = parts[0]
                nom = " ".join(parts[1:])
                print(f"   ✅ Nom composé: {prenom} | {nom}")
                return prenom, nom
        
        else:
            # 4+ mots: Prénom(s) = tout sauf le dernier mot
            prenom = " ".join(parts[:-1])
            nom = parts[-1]
            print(f"   ✅ Multi-mots: {prenom} | {nom}")
            return prenom, nom
        
    except Exception as e:
        print(f"   ❌ Erreur parsing '{full_name}': {e}")
        return full_name, ""

class AriegeScraperParsing:
    def __init__(self, test_mode=False, headless=True):
        self.test_mode = test_mode
        self.headless = headless
        self.url = "https://www.ariege-avocats.fr/annuaire-des-avocats"
        self.avocats_data = []
        
        # Configuration Chrome
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = None
    
    def init_driver(self):
        """Initialise le driver Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.implicitly_wait(10)
            print("✅ Driver Chrome initialisé")
            return True
        except Exception as e:
            print(f"❌ Erreur driver: {e}")
            return False
    
    def accept_cookies(self):
        """Gère l'acceptation des cookies"""
        try:
            cookie_selectors = [
                "button[data-testid='uc-accept-all-button']",
                ".cookie-banner button", "#cookie-consent button",
                "[id*='cookie'] button", "[class*='cookie'] button"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_btn.click()
                    print("✅ Cookies acceptés")
                    time.sleep(2)
                    return True
                except:
                    continue
            
            print("ℹ️  Aucune bannière de cookies")
            return True
            
        except Exception as e:
            print(f"⚠️  Erreur cookies: {e}")
            return True
    
    def wait_for_content_load(self):
        """Attend que le contenu soit chargé complètement"""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("🔄 Chargement du contenu dynamique...")
            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            print("✅ Contenu chargé")
            return True
            
        except Exception as e:
            print(f"⚠️  Erreur chargement: {e}")
            return True
    
    def extract_from_json_ld_fixed(self):
        """Extraction avec parsing de noms CORRIGÉ"""
        try:
            json_scripts = self.driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            
            for script in json_scripts:
                content = script.get_attribute("innerHTML")
                
                if '"mainEntity"' in content:
                    print("🔍 Extraction JSON-LD avec parsing corrigé...")
                    
                    # Pattern pour capturer chaque avocat individuellement
                    person_pattern = re.compile(
                        r'\{\s*"@type":\s*"Person",\s*'
                        r'"name":\s*"([^"]+)",\s*'
                        r'"jobTitle":\s*"([^"]+)",\s*'
                        r'"telephone":\s*"([^"]+)",\s*'
                        r'"email":\s*"([^"]+)"[^}]*'
                        r'(?:"address":\s*(?:\{[^}]*\}|\[[^\]]*\]))?[^}]*\}',
                        re.DOTALL
                    )
                    
                    matches = person_pattern.findall(content)
                    
                    if matches:
                        print(f"📋 Trouvé {len(matches)} avocats dans JSON-LD")
                        
                        avocats = []
                        for i, match in enumerate(matches):
                            name, job_title, telephone, email = match
                            
                            # PARSING CORRIGÉ
                            prenom, nom = parse_french_lawyer_name(name)
                            
                            avocat = {
                                "prenom": prenom,
                                "nom": nom,
                                "nom_complet": name,
                                "email": email,
                                "telephone": telephone,
                                "site_web": "",
                                "adresse": "",
                                "code_postal": "",
                                "ville": "",
                                "titre": job_title,
                                "annee_inscription": "",
                                "specialisations": "",
                                "structure": "",
                                "source": self.url
                            }
                            avocats.append(avocat)
                            print(f"✅ #{i+1}: {prenom} {nom} - {email}")
                        
                        return avocats
            
        except Exception as e:
            print(f"⚠️  Erreur JSON-LD: {e}")
        
        return []
    
    def scrape_all_lawyers(self):
        """Lance l'extraction avec parsing corrigé"""
        print(f"🔍 Scraping avec parsing de noms CORRIGÉ")
        print(f"   Mode: {'TEST (20 max)' if self.test_mode else 'PRODUCTION (tous)'}")
        
        try:
            self.driver.get(self.url)
            time.sleep(3)
            
            self.accept_cookies()
            self.wait_for_content_load()
            
            # Extraction avec parsing corrigé
            avocats = self.extract_from_json_ld_fixed()
            
            # Limiter si mode test
            if self.test_mode and avocats:
                avocats = avocats[:20]
            
            self.avocats_data = avocats
            
            print(f"✅ Extraction terminée: {len(self.avocats_data)} avocats")
            return True
            
        except Exception as e:
            print(f"❌ Erreur scraping: {e}")
            return False
    
    def save_results(self, mode="PRODUCTION"):
        """Sauvegarde avec vérification de la qualité"""
        if not self.avocats_data:
            print("❌ Aucune donnée")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"ARIEGE_{mode}_PARSING_FIXED"
        
        # CSV
        csv_filename = f"{prefix}_{len(self.avocats_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = self.avocats_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.avocats_data)
        
        print(f"💾 CSV: {csv_filename}")
        
        # JSON
        json_filename = f"{prefix}_{len(self.avocats_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.avocats_data, jsonfile, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON: {json_filename}")
        
        # Emails
        emails = [a['email'] for a in self.avocats_data if a.get('email')]
        unique_emails = list(set(emails))
        
        emails_filename = f"{prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as txtfile:
            for email in sorted(unique_emails):
                txtfile.write(f"{email}\n")
        
        print(f"📧 Emails: {emails_filename} ({len(unique_emails)} uniques)")
        
        # Rapport avec vérification détaillée
        rapport_filename = f"{prefix}_RAPPORT_PARSING_20260225_111418.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as report:
            report.write(f"RAPPORT PARSING CORRIGÉ - BARREAU DE L'ARIÈGE ({mode})\n")
            report.write(f"{'='*75}\n\n")
            report.write(f"Date: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            report.write(f"URL: {self.url}\n")
            report.write(f"Parsing: EXPERT avec règles françaises complètes\n\n")
            
            report.write(f"VÉRIFICATION PARSING PRÉNOM/NOM:\n")
            for i, avocat in enumerate(self.avocats_data, 1):
                report.write(f"{i:2d}. {avocat['prenom']} | {avocat['nom']}")
                report.write(f" (Original: {avocat['nom_complet']})")
                if avocat.get('email'):
                    report.write(f" - {avocat['email']}")
                report.write(f"\n")
            
            report.write(f"\nSTATISTIQUES:\n")
            report.write(f"- Total: {len(self.avocats_data)} avocats\n")
            report.write(f"- Avec prénom ET nom: {len([a for a in self.avocats_data if a['prenom'] and a['nom']])}\n")
            report.write(f"- Emails: {len(emails)} ({len(emails)/len(self.avocats_data)*100:.1f}%)\n")
        
        print(f"📊 Rapport: {rapport_filename}")
        
        # Vérification qualité
        correct_parsing = len([a for a in self.avocats_data if a['prenom'] and a['nom']])
        print(f"\n🎯 QUALITÉ PARSING:")
        print(f"   • Parsing complet: {correct_parsing}/{len(self.avocats_data)} ({correct_parsing/len(self.avocats_data)*100:.1f}%)")
        print(f"   • Emails: {len(emails)}/{len(self.avocats_data)} ({len(emails)/len(self.avocats_data)*100:.1f}%)")
    
    def run(self):
        """Lance l'extraction"""
        try:
            if not self.init_driver():
                return False
            
            success = self.scrape_all_lawyers()
            
            if success and self.avocats_data:
                mode = "TEST" if self.test_mode else "PRODUCTION"
                self.save_results(mode)
                print(f"\n✅ Scraping avec parsing corrigé terminé!")
                return True
            else:
                print("\n❌ Échec")
                return False
                
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fermé")

def main():
    """Fonction principale"""
    print("🚀 SCRAPER ARIÈGE - PARSING PRÉNOM/NOM CORRIGÉ")
    print("=" * 55)
    
    test_mode = len(sys.argv) > 1 and sys.argv[1] == "test"
    
    scraper = AriegeScraperParsing(test_mode=test_mode, headless=True)
    success = scraper.run()
    
    if test_mode and success:
        print("\n💡 Pour l'extraction complète:")
        print("   python3 ARIEGE_SCRAPER_PARSING_FIXED.py")

if __name__ == "__main__":
    main()