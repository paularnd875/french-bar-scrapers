#!/usr/bin/env python3
"""
SCRAPER PERFECT pour le barreau de Papeete
Basé sur l'analyse HTML précise:

Structure exacte observée:
<div><b>ALGAN Vaitiare</b></div>
<div>40 83 32 56</div>
<div>40 42 40 50</div>
<div>&nbsp;<a href="mailto:v.algan@fma-avocats.com">v.algan@fma-avocats.com</a></div>
<div>Rue des poilus Tahitiens, Résidence Santa Anna, Papeete</div>
<hr>
<div><b>ALLAIN-SACAULT Annick Hina</b></div>
...

Approche: parcourir séquentiellement et extraire bloc par bloc
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class PapeeteLawyerPerfectScraper:
    def __init__(self, headless=True, test_mode=False):
        self.headless = headless
        self.test_mode = test_mode
        self.base_url = "https://barreau-avocats.pf/avocats-inscrits-au-barreau-de-papeete/"
        self.lawyers_data = []
        self.setup_driver()
        
    def setup_driver(self):
        """Configuration Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 15)
        
    def accept_cookies(self):
        """Accepter les cookies"""
        try:
            time.sleep(2)
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if any(word in button.text.lower() for word in ['accepter', 'accept', 'ok']):
                    button.click()
                    time.sleep(1)
                    return True
            return True
        except:
            return True
    
    def separate_name_perfect(self, full_name):
        """
        Séparation prénom/nom CORRIGÉE pour format Polynésie:
        Format observé: "NOM-COMPOSÉ Prénom(s)" où NOM est en MAJUSCULES
        Exemples:
        - "ALLAIN-SACAULT Annick Hina" -> nom="ALLAIN-SACAULT", prénom="Annick Hina"
        - "ALGAN Vaitiare" -> nom="ALGAN", prénom="Vaitiare"
        """
        if not full_name:
            return "", ""
        
        # Nettoyer les annotations
        full_name = re.sub(r'\(ancien.*?\)', '', full_name, flags=re.IGNORECASE)
        full_name = re.sub(r'\(ex.*?\)', '', full_name, flags=re.IGNORECASE)
        full_name = re.sub(r'\([^)]*Bâtonnier[^)]*\)', '', full_name, flags=re.IGNORECASE)
        full_name = re.sub(r'\s+', ' ', full_name.strip())
        
        parts = full_name.split()
        
        if len(parts) <= 1:
            return "", full_name
        
        # Identifier les parties en MAJUSCULES (nom de famille)
        # Le nom de famille peut être composé de plusieurs mots en majuscules
        nom_parts = []
        prenom_parts = []
        
        # Parcourir les mots de gauche à droite
        for i, word in enumerate(parts):
            # Si c'est entièrement en majuscules ET length > 1, c'est probablement le nom
            if word.isupper() and len(word) > 1:
                nom_parts.append(word)
            else:
                # Dès qu'on trouve un mot pas en majuscules, tout le reste = prénom(s)
                prenom_parts = parts[len(nom_parts):]
                break
        
        # Si aucun mot en majuscules trouvé, utiliser la logique par défaut
        if not nom_parts:
            # Format "Prénom NOM" classique français
            if len(parts) == 2:
                return parts[0], parts[1]
            else:
                # Prendre le dernier mot comme nom
                return " ".join(parts[:-1]), parts[-1]
        
        nom = " ".join(nom_parts)
        prenom = " ".join(prenom_parts)
        
        return prenom, nom
    
    def parse_sequential_blocks(self, soup):
        """
        Parser séquentiel basé sur la structure exacte observée:
        <div><b>NOM</b></div> -> <div>tel</div> -> <div>tel</div> -> <div>email</div> -> <div>adresse</div> -> <hr>
        """
        lawyers = []
        
        # Récupérer tous les éléments div et hr en séquence
        elements = soup.find_all(['div', 'hr'])
        
        i = 0
        while i < len(elements):
            element = elements[i]
            
            # Chercher une div avec un nom en gras
            if element.name == 'div':
                bold_tags = element.find_all(['b', 'strong'])
                
                for bold_tag in bold_tags:
                    name_text = bold_tag.get_text(strip=True)
                    
                    # Vérifier que c'est un vrai nom d'avocat
                    if (name_text and 
                        len(name_text.split()) >= 2 and
                        not any(skip in name_text.lower() for skip in 
                               ['liste', 'alpha', 'inscrits', 'barreau', 'avocats', 'papeete', '2026'])):
                        
                        # Créer l'avocat
                        lawyer = {
                            'nom': '',
                            'prenom': '',
                            'nom_complet': name_text,
                            'email': '',
                            'telephone': '',
                            'adresse': '',
                            'specialisations': '',
                            'structure': '',
                            'annee_inscription': '',
                            'source': self.base_url
                        }
                        
                        # Séparation prénom/nom
                        prenom, nom = self.separate_name_perfect(name_text)
                        lawyer['prenom'] = prenom
                        lawyer['nom'] = nom
                        
                        # Parser les éléments suivants dans l'ordre
                        phones = []
                        email = ""
                        address = ""
                        
                        j = i + 1
                        parsed_count = 0  # Pour éviter de trop parser
                        
                        while j < len(elements) and parsed_count < 10:
                            next_element = elements[j]
                            
                            # Arrêter si on trouve un hr ou un autre nom
                            if (next_element.name == 'hr' or 
                                (next_element.name == 'div' and next_element.find_all(['b', 'strong']))):
                                break
                            
                            if next_element.name == 'div':
                                div_text = next_element.get_text(strip=True)
                                
                                # Ignorer les divs vides ou avec &nbsp;
                                if not div_text or div_text == '&nbsp;':
                                    j += 1
                                    continue
                                
                                # Email (avec lien mailto)
                                email_link = next_element.find('a', href=re.compile(r'mailto:'))
                                if email_link and not email:
                                    email_href = email_link.get('href', '')
                                    email = email_href.replace('mailto:', '').strip()
                                    j += 1
                                    parsed_count += 1
                                    continue
                                
                                # Téléphone (pattern exact XX XX XX XX)
                                if re.match(r'^\d{2}\s\d{2}\s\d{2}\s\d{2}$', div_text):
                                    phones.append(div_text)
                                    j += 1
                                    parsed_count += 1
                                    continue
                                
                                # Adresse (ligne longue sans email ni tel)
                                if (len(div_text) > 10 and 
                                    '@' not in div_text and 
                                    not re.match(r'^\d{2}\s\d{2}\s\d{2}\s\d{2}$', div_text)):
                                    if not address:  # Prendre seulement la première ligne d'adresse
                                        address = div_text
                                    j += 1
                                    parsed_count += 1
                                    continue
                            
                            j += 1
                            parsed_count += 1
                        
                        # Assigner les résultats
                        lawyer['email'] = email
                        lawyer['telephone'] = ', '.join(phones)
                        lawyer['adresse'] = address
                        
                        lawyers.append(lawyer)
                        print(f"✅ {len(lawyers):3d}. {lawyer['prenom']} {lawyer['nom']} | {lawyer['email']} | {lawyer['telephone']}")
                        
                        # Continuer à partir de j (après ce bloc)
                        i = j - 1  # -1 car on va incrémenter
                        break
            
            i += 1
        
        return lawyers
    
    def scrape_lawyers(self):
        """Scraping principal PERFECT"""
        try:
            print(f"🌐 Connexion: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(4)
            
            self.accept_cookies()
            
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            print("🔍 Extraction HTML...")
            html_content = self.driver.page_source
            
            print("📊 Parsing séquentiel perfectionné...")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Parser avec la méthode séquentielle
            self.lawyers_data = self.parse_sequential_blocks(soup)
            
            # Éliminer les doublons stricts
            unique_lawyers = []
            seen_names = set()
            
            for lawyer in self.lawyers_data:
                name_key = lawyer['nom_complet'].lower().strip()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    unique_lawyers.append(lawyer)
            
            self.lawyers_data = unique_lawyers
            
            # Limitation test
            if self.test_mode:
                self.lawyers_data = self.lawyers_data[:10]
                print(f"🧪 Test: limité à {len(self.lawyers_data)} avocats")
            
            # Statistiques
            with_email = len([l for l in self.lawyers_data if l['email']])
            with_phone = len([l for l in self.lawyers_data if l['telephone']])
            with_address = len([l for l in self.lawyers_data if l['adresse']])
            
            print(f"\n📊 RÉSULTATS PERFECT:")
            print(f"   Total: {len(self.lawyers_data)} avocats")
            print(f"   Avec email: {with_email}")
            print(f"   Avec téléphone: {with_phone}")
            print(f"   Avec adresse: {with_address}")
            
            return len(self.lawyers_data) > 0
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_results(self):
        """Sauvegarde parfaite"""
        if not self.lawyers_data:
            print("⚠️ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode = "TEST" if self.test_mode else "PRODUCTION"
        
        # CSV
        csv_file = f"/Users/paularnould/PAPEETE_{mode}_PERFECT_{len(self.lawyers_data)}_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 'specialisations', 'structure', 'annee_inscription', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        # JSON
        json_file = f"/Users/paularnould/PAPEETE_{mode}_PERFECT_{len(self.lawyers_data)}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails = [l['email'] for l in self.lawyers_data if l['email']]
        email_file = f"/Users/paularnould/PAPEETE_{mode}_EMAILS_PERFECT_{len(emails)}_{timestamp}.txt"
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        print(f"\n💾 SAUVEGARDE PERFECT:")
        print(f"   📊 CSV: {csv_file}")
        print(f"   🗂️ JSON: {json_file}")  
        print(f"   📧 Emails ({len(emails)}): {email_file}")
    
    def run(self):
        """Exécution parfaite"""
        try:
            mode = "TEST" if self.test_mode else "PRODUCTION"
            interface = "HEADLESS" if self.headless else "VISIBLE"
            
            print("🏝️ " + "="*60)
            print("    BARREAU DE PAPEETE - SCRAPER PERFECT")
            print("🏝️ " + "="*60)
            print(f"Mode: {mode} | Interface: {interface}")
            print("🎯 Approach: Sequential parsing per la structure HTML exacte")
            print("-" * 60)
            
            if self.scrape_lawyers():
                self.save_results()
                print("\n" + "="*60)
                print("✅ EXTRACTION PARFAITE RÉUSSIE!")
                print(f"🎯 {len(self.lawyers_data)} avocats extraits")
                with_email = len([l for l in self.lawyers_data if l['email']])
                print(f"📧 {with_email} emails récupérés")
                print("="*60)
                return True
            else:
                print("❌ ÉCHEC DE L'EXTRACTION")
                return False
                
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE: {e}")
            return False
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    print("🏝️ SCRAPER PAPEETE - VERSION PERFECT CORRIGÉE")
    print("🚀 MODE PRODUCTION FINAL - Tous les avocats")
    scraper = PapeeteLawyerPerfectScraper(headless=True, test_mode=False)
    
    success = scraper.run()
    
    if success:
        print("\n🎉 SCRAPER PERFECT TERMINÉ!")
        print("Données extraites avec précision maximale.")
    else:
        print("\n💥 Échec. Consultez les logs.")

if __name__ == "__main__":
    main()