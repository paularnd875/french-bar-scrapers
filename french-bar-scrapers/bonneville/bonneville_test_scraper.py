#!/usr/bin/env python3
"""
Scraper de test pour le Barreau de Bonneville
Teste l'extraction des données d'avocats
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

class BonnevilleTestScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/"
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        
    def setup_driver(self):
        """Configure le driver Chrome avec options anti-détection"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        # Options anti-détection
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        
    def handle_cookies_and_load(self):
        """Gère les cookies et charge la page"""
        print("🔄 Chargement de la page...")
        self.driver.get(self.base_url)
        
        # Attendre que la page se charge
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Gérer les cookies
        self.accept_cookies()
        
        # Attendre un peu plus après les cookies
        time.sleep(3)
        
    def accept_cookies(self):
        """Accepte les cookies si présents"""
        print("🍪 Gestion des cookies...")
        
        cookie_buttons = [
            "//button[contains(text(), 'Tout accepter')]",
            "//button[contains(text(), 'Accepter')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'OK')]",
            "//*[@id='cookie-accept']",
            "//*[@class='cookie-accept']",
            "//button[contains(@class, 'cookie')]//button[contains(@class, 'accept')]"
        ]
        
        for xpath in cookie_buttons:
            try:
                button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button.click()
                print("✅ Cookies acceptés")
                time.sleep(2)
                return True
            except:
                continue
                
        print("ℹ️ Pas de bannière de cookies détectée")
        return False
        
    def find_lawyers_list(self):
        """Trouve la liste des avocats"""
        print("🔍 Recherche de la liste des avocats...")
        
        # D'abord, chercher s'il y a un bouton ou un lien pour afficher la liste
        display_buttons = [
            "//a[contains(text(), 'TABLEAU DE')]",
            "//a[contains(text(), 'ORDRE')]", 
            "//a[contains(text(), 'CLIQUEZ ICI')]",
            "//button[contains(text(), 'Afficher')]",
            "//button[contains(text(), 'Liste')]"
        ]
        
        for xpath in display_buttons:
            try:
                button = self.driver.find_element(By.XPATH, xpath)
                if button.is_displayed() and button.is_enabled():
                    print(f"✅ Trouvé bouton d'affichage : {button.text}")
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    break
            except:
                continue
        
        # Maintenant chercher les avocats avec différents sélecteurs
        lawyer_selectors = [
            # Sélecteurs spécifiques aux avocats
            "[class*='avocat']",
            "[class*='lawyer']", 
            "[class*='barreau']",
            "[class*='membre']",
            "[class*='attorney']",
            
            # Sélecteurs génériques
            ".et_pb_text a[href*='avocat']",
            ".et_pb_text a[href*='lawyer']",
            "a[href*='/avocat/']",
            "a[href*='/member/']",
            
            # Chercher dans les textes de liens
            "//a[contains(@href, 'avocat')]",
            "//a[text()[contains(., ' ') and string-length(normalize-space(.)) > 5]]"
        ]
        
        lawyers_found = []
        
        for selector in lawyer_selectors:
            try:
                if selector.startswith('//'):
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                # Filtrer les éléments qui ressemblent à des noms d'avocats
                for elem in elements:
                    text = elem.text.strip()
                    href = elem.get_attribute('href') if elem.tag_name == 'a' else None
                    
                    # Vérifier si c'est un nom d'avocat potentiel
                    if (text and 
                        len(text) > 3 and 
                        len(text) < 100 and 
                        ' ' in text and 
                        not text.lower() in ['accueil', 'contact', 'mentions', 'plan du site', 'le barreau']):
                        
                        lawyers_found.append({
                            'element': elem,
                            'text': text,
                            'href': href,
                            'selector': selector
                        })
                
                if lawyers_found:
                    print(f"✅ Trouvé {len(lawyers_found)} avocats potentiels avec sélecteur : {selector}")
                    return lawyers_found
                    
            except Exception as e:
                continue
        
        # Si aucun avocat trouvé, examiner toute la page pour des patterns
        print("🔍 Analyse pattern dans le texte de la page...")
        page_text = self.driver.page_source
        
        # Chercher des patterns comme "Me Nom Prénom" ou "Maître Nom"
        import re
        patterns = [
            r'M[ae]\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Maître\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Avocat[^:]*:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"✅ Trouvé {len(matches)} noms via pattern : {pattern}")
                # Créer des éléments virtuels pour ces noms
                for match in matches:
                    lawyers_found.append({
                        'element': None,
                        'text': match,
                        'href': None,
                        'selector': 'pattern_match'
                    })
                return lawyers_found
        
        print("❌ Aucun avocat trouvé")
        return []
        
    def test_single_lawyer_detail(self, lawyer):
        """Teste l'extraction des détails d'un seul avocat"""
        print(f"🔍 Test extraction pour : {lawyer['text']}")
        
        if lawyer['href'] and lawyer['element']:
            try:
                # Cliquer sur le lien
                self.driver.execute_script("arguments[0].click();", lawyer['element'])
                time.sleep(3)
                
                # Extraire les informations
                lawyer_info = self.extract_lawyer_details()
                
                # Revenir à la page précédente
                self.driver.back()
                time.sleep(2)
                
                return lawyer_info
                
            except Exception as e:
                print(f"❌ Erreur clic sur avocat : {e}")
                return None
        else:
            print("ℹ️ Pas de lien cliquable pour cet avocat")
            return None
            
    def extract_lawyer_details(self):
        """Extrait les détails d'un avocat depuis sa page"""
        print("📝 Extraction des détails...")
        
        page_source = self.driver.page_source.lower()
        
        # Informations à extraire
        details = {
            'nom': '',
            'prenom': '',
            'email': '',
            'telephone': '',
            'annee_inscription': '',
            'specialisations': '',
            'structure': '',
            'adresse': ''
        }
        
        # Extraction de l'email
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, page_source)
        if emails:
            details['email'] = emails[0]
            print(f"📧 Email trouvé : {details['email']}")
            
        # Extraction du téléphone
        phone_patterns = [
            r'(?:tél|tel|phone|téléphone)[:\s]*([0-9\s\.\-\+]{10,})',
            r'(\+33[0-9\s\.\-]{9,})',
            r'(0[1-9](?:[0-9\s\.\-]{8,}))'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, page_source)
            if phones:
                details['telephone'] = phones[0].strip()
                print(f"📞 Téléphone trouvé : {details['telephone']}")
                break
                
        # Extraction de l'année d'inscription
        year_patterns = [
            r'inscr[a-z]*[:\s]*([12][0-9]{3})',
            r'depuis[:\s]*([12][0-9]{3})',
            r'année[:\s]*([12][0-9]{3})'
        ]
        
        for pattern in year_patterns:
            years = re.findall(pattern, page_source)
            if years:
                details['annee_inscription'] = years[0]
                print(f"📅 Année inscription : {details['annee_inscription']}")
                break
                
        # Chercher les spécialisations
        spec_keywords = ['droit', 'spécial', 'compétence', 'domaine']
        text_elements = self.driver.find_elements(By.TAG_NAME, 'p')
        
        for elem in text_elements:
            text = elem.text.lower()
            if any(keyword in text for keyword in spec_keywords):
                if len(text) > 10 and len(text) < 200:
                    details['specialisations'] = elem.text
                    print(f"⚖️ Spécialisations trouvées : {details['specialisations'][:50]}...")
                    break
                    
        # Structure (cabinet, etc.)
        structure_keywords = ['cabinet', 'société', 'sarl', 'scp', 'avocats']
        for elem in text_elements:
            text = elem.text.lower()
            if any(keyword in text for keyword in structure_keywords) and len(text) < 100:
                details['structure'] = elem.text
                print(f"🏢 Structure trouvée : {details['structure']}")
                break
                
        return details
        
    def run_test(self, max_lawyers=3):
        """Lance un test sur quelques avocats"""
        try:
            self.setup_driver()
            print("🚀 Démarrage du test Bonneville")
            
            # Charger la page
            self.handle_cookies_and_load()
            
            # Trouver les avocats
            lawyers = self.find_lawyers_list()
            
            if not lawyers:
                print("❌ Aucun avocat trouvé pour le test")
                return False
                
            print(f"✅ {len(lawyers)} avocats trouvés, test sur {min(max_lawyers, len(lawyers))}")
            
            # Tester quelques avocats
            for i, lawyer in enumerate(lawyers[:max_lawyers]):
                print(f"\n--- Test avocat {i+1}/{min(max_lawyers, len(lawyers))} ---")
                
                details = self.test_single_lawyer_detail(lawyer)
                if details:
                    # Ajouter le nom depuis le lien
                    details['nom_complet'] = lawyer['text']
                    self.lawyers_data.append(details)
                    
            # Sauvegarder les résultats
            self.save_results()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale : {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                
    def save_results(self):
        """Sauvegarde les résultats du test"""
        if not self.lawyers_data:
            print("ℹ️ Aucune donnée à sauvegarder")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde CSV
        csv_filename = f"bonneville_test_results_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom_complet', 'nom', 'prenom', 'email', 'telephone', 
                         'annee_inscription', 'specialisations', 'structure', 'adresse']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in self.lawyers_data:
                writer.writerow(lawyer)
                
        # Sauvegarde JSON
        json_filename = f"bonneville_test_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
            
        print(f"✅ Résultats sauvegardés :")
        print(f"   CSV: {csv_filename}")
        print(f"   JSON: {json_filename}")
        
        # Afficher un résumé
        print(f"\n📊 RÉSUMÉ DU TEST :")
        print(f"   Avocats testés : {len(self.lawyers_data)}")
        
        emails_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('email'))
        phones_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('telephone'))
        specs_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('specialisations'))
        
        print(f"   Emails trouvés : {emails_found}")
        print(f"   Téléphones trouvés : {phones_found}")
        print(f"   Spécialisations trouvées : {specs_found}")

if __name__ == "__main__":
    # Test en mode visuel d'abord
    scraper = BonnevilleTestScraper(headless=False)
    scraper.run_test(max_lawyers=3)