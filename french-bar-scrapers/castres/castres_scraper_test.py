#!/usr/bin/env python3
"""
Script de test pour scraper le barreau de Castres
Phase 1: Test avec gestion des cookies et extraction d'un avocat
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CastresScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.lawyers = []
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent pour éviter la détection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
        
    def accept_cookies(self):
        """Gestion de l'acceptation des cookies"""
        print("🍪 Recherche du bandeau de cookies...")
        
        try:
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Rechercher différents sélecteurs possibles pour les cookies
            cookie_selectors = [
                '[id*="cookie"]',
                '[class*="cookie"]',
                '[id*="consent"]',
                '[class*="consent"]',
                '[id*="tarteaucitron"]',
                '[class*="tarteaucitron"]',
                'button[class*="accept"]',
                'button[id*="accept"]',
                'a[class*="accept"]'
            ]
            
            cookie_found = False
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Trouvé élément cookie avec sélecteur: {selector}")
                        for element in elements:
                            if element.is_displayed():
                                print(f"   Texte: {element.text[:100]}")
                                # Chercher un bouton d'acceptation
                                if any(word in element.text.lower() for word in ['accept', 'accepter', 'ok', 'valider']):
                                    try:
                                        element.click()
                                        print("✅ Cookies acceptés!")
                                        cookie_found = True
                                        time.sleep(2)
                                        break
                                    except Exception as e:
                                        print(f"   Erreur clic: {e}")
                        if cookie_found:
                            break
                except Exception as e:
                    continue
            
            if not cookie_found:
                print("ℹ️  Aucun bandeau de cookies trouvé ou déjà accepté")
                
        except Exception as e:
            print(f"❌ Erreur gestion cookies: {e}")
            
        time.sleep(3)
        
    def get_lawyer_links(self):
        """Récupération des liens vers les fiches d'avocats"""
        print("📋 Récupération des liens d'avocats...")
        
        lawyer_links = []
        
        try:
            # Attendre que les éléments soient chargés
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Différents sélecteurs pour trouver les liens des avocats
            selectors = [
                'a[href*="avocat"]',
                'a[href*="profil"]', 
                'a[href*="fiche"]',
                '.lawyer-card a',
                '.avocat-card a',
                '.profile-card a'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Trouvé {len(elements)} liens avec sélecteur: {selector}")
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and 'avocat' in href.lower():
                                lawyer_links.append(href)
                        break
                except Exception as e:
                    continue
            
            # Si pas de liens spécifiques, chercher tous les liens de la page
            if not lawyer_links:
                print("🔍 Recherche de tous les liens de la page...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and any(word in href.lower() for word in ['avocat', 'profil', 'fiche']):
                        lawyer_links.append(href)
            
            # Nettoyer et dédupliquer
            lawyer_links = list(set([link for link in lawyer_links if link]))
            
            print(f"📊 Total de {len(lawyer_links)} liens d'avocats trouvés")
            
            return lawyer_links[:3]  # Pour le test, on prend seulement les 3 premiers
            
        except Exception as e:
            print(f"❌ Erreur récupération liens: {e}")
            return []
    
    def extract_lawyer_info(self, url):
        """Extraction des informations d'un avocat"""
        print(f"👤 Extraction des infos de: {url}")
        
        lawyer_info = {
            'url': url,
            'nom': '',
            'prenom': '',
            'email': '',
            'annee_inscription': '',
            'specialisations': [],
            'structure': '',
            'adresse': '',
            'telephone': ''
        }
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Sauvegarder le HTML pour debug
            page_source = self.driver.page_source
            with open(f'castres_lawyer_debug_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            # Extraction du nom/prénom
            name_selectors = [
                'h1', 'h2', 'h3',
                '[class*="name"]', '[class*="nom"]', 
                '[class*="title"]', '[class*="titre"]',
                '.lawyer-name', '.avocat-nom'
            ]
            
            for selector in name_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.text.strip():
                        full_name = element.text.strip()
                        print(f"   Nom trouvé: {full_name}")
                        # Essayer de séparer prénom/nom
                        name_parts = full_name.split()
                        if len(name_parts) >= 2:
                            lawyer_info['prenom'] = name_parts[0]
                            lawyer_info['nom'] = ' '.join(name_parts[1:])
                        else:
                            lawyer_info['nom'] = full_name
                        break
                except:
                    continue
            
            # Extraction email
            email_selectors = [
                'a[href^="mailto:"]',
                '[class*="email"]', '[class*="mail"]',
                'input[type="email"]'
            ]
            
            for selector in email_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if selector == 'a[href^="mailto:"]':
                            email = element.get_attribute('href').replace('mailto:', '')
                        else:
                            email = element.text.strip() or element.get_attribute('value', '')
                        
                        if email and '@' in email:
                            lawyer_info['email'] = email
                            print(f"   Email trouvé: {email}")
                            break
                    if lawyer_info['email']:
                        break
                except:
                    continue
            
            # Recherche spécialisations
            specialization_keywords = ['spécialisation', 'spécialité', 'domaine', 'pratique']
            text_content = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for keyword in specialization_keywords:
                if keyword in text_content:
                    # Récupérer le texte autour du mot-clé
                    lines = text_content.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line:
                            # Prendre cette ligne et les 2 suivantes
                            spec_text = ' '.join(lines[i:i+3])
                            lawyer_info['specialisations'].append(spec_text[:200])
                            print(f"   Spécialisation trouvée: {spec_text[:100]}")
                            break
            
            # Recherche année d'inscription
            import re
            year_pattern = r'\b(19|20)\d{2}\b'
            matches = re.findall(year_pattern, page_source)
            if matches:
                # Prendre l'année la plus récente qui semble être une inscription
                years = [int(match[0] + match[1:]) for match in matches if int(match[0] + match[1:]) > 1970]
                if years:
                    lawyer_info['annee_inscription'] = str(max(years))
                    print(f"   Année d'inscription: {lawyer_info['annee_inscription']}")
            
            print(f"✅ Extraction terminée pour {lawyer_info.get('nom', 'Inconnu')}")
            
        except Exception as e:
            print(f"❌ Erreur extraction {url}: {e}")
        
        return lawyer_info
    
    def run_test(self):
        """Exécution du test"""
        print("🚀 Démarrage du test scraper Castres")
        print("=" * 50)
        
        try:
            # Configuration
            self.setup_driver()
            print("✅ Driver configuré")
            
            # Accès à la page
            print("🌐 Accès à la page d'annuaire...")
            self.driver.get("https://avocats-castres.fr/annuaire-avocats/")
            time.sleep(5)
            
            # Gestion cookies
            self.accept_cookies()
            
            # Récupération des liens
            lawyer_links = self.get_lawyer_links()
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                return
            
            print(f"📋 Test sur {len(lawyer_links)} avocats")
            
            # Test extraction
            for i, link in enumerate(lawyer_links, 1):
                print(f"\n--- Test {i}/{len(lawyer_links)} ---")
                lawyer_info = self.extract_lawyer_info(link)
                self.lawyers.append(lawyer_info)
                time.sleep(2)  # Pause entre les requêtes
            
            # Sauvegarde résultats
            self.save_results()
            
            print("\n" + "=" * 50)
            print("✅ Test terminé avec succès!")
            print(f"📊 {len(self.lawyers)} avocats traités")
            
        except Exception as e:
            print(f"❌ Erreur durant le test: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fermé")
    
    def save_results(self):
        """Sauvegarde des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f'castres_test_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_file = f'castres_test_{timestamp}.csv'
        if self.lawyers:
            fieldnames = self.lawyers[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in self.lawyers:
                    # Convertir les listes en string pour CSV
                    row = lawyer.copy()
                    row['specialisations'] = '; '.join(row['specialisations']) if row['specialisations'] else ''
                    writer.writerow(row)
        
        print(f"💾 Résultats sauvegardés: {json_file} et {csv_file}")

if __name__ == "__main__":
    # Test en mode visuel d'abord
    scraper = CastresScraper(headless=False)
    scraper.run_test()