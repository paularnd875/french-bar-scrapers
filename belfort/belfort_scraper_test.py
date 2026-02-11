#!/usr/bin/env python3
"""
Script de test pour scraper les avocats du barreau de Belfort
Site: https://www.avocats-belfort.com/annuaire-avocats.htm
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
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BelfortBarScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.avocats-belfort.com"
        self.annuaire_url = "https://www.avocats-belfort.com/annuaire-avocats.htm"
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        
    def setup_driver(self):
        """Configure le driver Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def accept_cookies(self):
        """Accepte les cookies si la bannière est présente"""
        try:
            logger.info("Recherche de la bannière de cookies...")
            wait = WebDriverWait(self.driver, 10)
            
            # Chercher le bouton "ACCEPTER" pour les cookies
            accept_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ACCEPTER') or contains(text(), 'Accepter')]"))
            )
            accept_button.click()
            logger.info("Cookies acceptés avec succès")
            time.sleep(2)
            return True
            
        except TimeoutException:
            logger.info("Pas de bannière de cookies trouvée ou déjà acceptée")
            return False
        except Exception as e:
            logger.warning(f"Erreur lors de l'acceptation des cookies: {e}")
            return False
    
    def get_lawyers_list(self):
        """Récupère la liste des avocats depuis la page principale"""
        try:
            logger.info("Accès à la page d'annuaire...")
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Attendre que les profils d'avocats se chargent
            wait = WebDriverWait(self.driver, 15)
            
            # Chercher différents types de liens vers les profils
            possible_selectors = [
                "//a[contains(@href, 'annuaire/maitre-')]",
                "//a[contains(@href, 'maitre-')]",
                "//a[contains(text(), 'Voir le détail')]",
                "//a[contains(@class, 'detail') or contains(@class, 'profile')]"
            ]
            
            lawyers_info = []
            lawyer_elements = []
            
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        lawyer_elements = elements
                        logger.info(f"Trouvé {len(elements)} éléments avec le sélecteur: {selector}")
                        break
                except Exception as e:
                    logger.warning(f"Sélecteur {selector} non trouvé: {e}")
                    continue
            
            # Éliminer les doublons
            unique_urls = set()
            for element in lawyer_elements:
                try:
                    profile_url = element.get_attribute('href')
                    if profile_url and profile_url not in unique_urls:
                        if 'maitre-' in profile_url or 'detail' in profile_url.lower():
                            unique_urls.add(profile_url)
                            lawyers_info.append({
                                'profile_url': profile_url,
                                'element': element
                            })
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction d'un lien avocat: {e}")
                    continue
            
            logger.info(f"Trouvé {len(lawyers_info)} avocats uniques")
            return lawyers_info
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des avocats: {e}")
            return []
    
    def extract_lawyer_details(self, lawyer_info):
        """Extrait les détails d'un avocat depuis sa fiche individuelle"""
        try:
            profile_url = lawyer_info['profile_url']
            logger.info(f"Extraction des détails pour: {profile_url}")
            
            # Aller sur la page de profil
            self.driver.get(profile_url)
            time.sleep(2)
            
            # Initialiser les données de l'avocat
            lawyer_data = {
                'url': profile_url,
                'prenom': '',
                'nom': '',
                'nom_complet': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'titre': ''
            }
            
            # Extraire le nom complet - essayer plusieurs sélecteurs
            name_selectors = [
                "//h1",
                "//h2", 
                "//div[@class='nom'] | //div[@class='name']",
                "//span[@class='nom'] | //span[@class='name']",
                "//*[contains(@class, 'titre') or contains(@class, 'nom') or contains(@class, 'name')]",
                "//*[contains(text(), 'Maître') or contains(text(), 'Maitre')]"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.XPATH, selector)
                    name_text = name_element.text.strip()
                    if name_text and len(name_text) > 3:
                        lawyer_data['nom_complet'] = name_text
                        lawyer_data['titre'] = name_text
                        
                        # Essayer de séparer prénom et nom
                        clean_name = name_text.replace('Maître ', '').replace('Maitre ', '').strip()
                        name_parts = clean_name.split()
                        if len(name_parts) >= 2:
                            lawyer_data['prenom'] = name_parts[0]
                            lawyer_data['nom'] = ' '.join(name_parts[1:])
                        break
                except NoSuchElementException:
                    continue
                    
            if not lawyer_data['nom_complet']:
                logger.warning("Nom complet non trouvé")
            
            # Extraire l'email
            try:
                email_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'mailto:')] | //span[contains(text(), '@')] | //div[contains(text(), '@')]")
                email_text = email_element.text or email_element.get_attribute('href')
                if email_text:
                    if 'mailto:' in email_text:
                        lawyer_data['email'] = email_text.replace('mailto:', '')
                    elif '@' in email_text:
                        lawyer_data['email'] = email_text
            except NoSuchElementException:
                logger.warning("Email non trouvé")
            
            # Extraire le téléphone
            try:
                phone_element = self.driver.find_element(By.XPATH, "//span[contains(text(), '03') or contains(text(), '06') or contains(text(), '07')] | //div[contains(text(), '03') or contains(text(), '06') or contains(text(), '07')]")
                lawyer_data['telephone'] = phone_element.text.strip()
            except NoSuchElementException:
                logger.warning("Téléphone non trouvé")
            
            # Extraire l'adresse
            try:
                address_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'adresse') or contains(@class, 'address')] | //span[contains(@class, 'adresse') or contains(@class, 'address')] | //p[contains(text(), 'rue') or contains(text(), 'avenue') or contains(text(), 'boulevard')]")
                if address_elements:
                    lawyer_data['adresse'] = address_elements[0].text.strip()
            except Exception:
                logger.warning("Adresse non trouvée")
            
            # Extraire l'année d'inscription
            try:
                year_elements = self.driver.find_elements(By.XPATH, "//span[contains(text(), '20') or contains(text(), '19')] | //div[contains(text(), 'inscrit') or contains(text(), 'admission')]")
                for element in year_elements:
                    text = element.text
                    # Chercher une année entre 1950 et 2024
                    import re
                    years = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', text)
                    if years:
                        lawyer_data['annee_inscription'] = years[0]
                        break
            except Exception:
                logger.warning("Année d'inscription non trouvée")
            
            # Extraire les spécialisations
            try:
                specializations = []
                spec_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'specialisation') or contains(@class, 'domaine')] | //ul//li | //span[contains(@class, 'competence')]")
                for element in spec_elements:
                    text = element.text.strip()
                    if text and len(text) > 3:
                        specializations.append(text)
                lawyer_data['specialisations'] = specializations
            except Exception:
                logger.warning("Spécialisations non trouvées")
            
            # Extraire la structure
            try:
                structure_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cabinet') or contains(@class, 'structure')] | //span[contains(text(), 'Cabinet') or contains(text(), 'SCP') or contains(text(), 'SELARL')]")
                if structure_elements:
                    lawyer_data['structure'] = structure_elements[0].text.strip()
            except Exception:
                logger.warning("Structure non trouvée")
            
            logger.info(f"Données extraites pour {lawyer_data['nom_complet']}")
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des détails: {e}")
            return None
    
    def scrape_test(self, max_lawyers=5):
        """Scrape un nombre limité d'avocats pour test"""
        try:
            self.setup_driver()
            logger.info(f"Début du scraping test - maximum {max_lawyers} avocats")
            
            # Récupérer la liste des avocats
            lawyers_list = self.get_lawyers_list()
            
            if not lawyers_list:
                logger.error("Aucun avocat trouvé")
                return
            
            # Limiter le nombre d'avocats pour le test
            test_lawyers = lawyers_list[:max_lawyers]
            
            for i, lawyer_info in enumerate(test_lawyers, 1):
                logger.info(f"Traitement avocat {i}/{len(test_lawyers)}")
                
                lawyer_data = self.extract_lawyer_details(lawyer_info)
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                
                # Pause entre les requêtes
                time.sleep(2)
            
            # Sauvegarder les résultats
            self.save_results()
            
        except Exception as e:
            logger.error(f"Erreur lors du scraping test: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Sauvegarde les résultats en JSON et CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_filename = f"belfort_test_results_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV
        csv_filename = f"belfort_test_results_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 'annee_inscription', 'specialisations', 'structure', 'titre', 'url']
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    # Convertir les spécialisations en string
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations']) if lawyer['specialisations'] else ''
                    writer.writerow(lawyer_copy)
        
        logger.info(f"Résultats sauvegardés: {json_filename} et {csv_filename}")
        
        # Afficher un résumé
        print(f"\n=== RÉSUMÉ DU TEST ===")
        print(f"Nombre d'avocats traités: {len(self.lawyers_data)}")
        print(f"Fichiers générés: {json_filename}, {csv_filename}")
        
        if self.lawyers_data:
            print(f"\nExemple de données extraites:")
            example = self.lawyers_data[0]
            for key, value in example.items():
                if key != 'url':
                    print(f"  {key}: {value}")

if __name__ == "__main__":
    scraper = BelfortBarScraper(headless=False)  # Mode visuel pour le test
    scraper.scrape_test(max_lawyers=3)  # Test avec 3 avocats seulement