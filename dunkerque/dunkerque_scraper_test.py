#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DunkerqueBarScraperTest:
    def __init__(self):
        self.base_url = "https://barreau-dunkerque.fr"
        self.search_url = "https://barreau-dunkerque.fr/search-result/?directory_type=general"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Configuration Selenium
        self.chrome_options = Options()
        # Mode visuel pour les tests
        # self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        self.lawyers_data = []
    
    def start_browser(self):
        """Démarre le navigateur Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Navigateur Chrome démarré avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du navigateur: {e}")
            return False
    
    def accept_cookies(self):
        """Gère l'acceptation des cookies si nécessaire"""
        try:
            # Recherche du bouton d'acceptation des cookies
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[id*='cookie']",
                "button[class*='cookie']",
                ".cookie-accept",
                "#cookie-accept",
                ".accept-cookies",
                "#accept-cookies"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    logger.info(f"Cookies acceptés via le sélecteur: {selector}")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
            logger.info("Aucun bouton de cookies trouvé - continuons")
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'acceptation des cookies: {e}")
            return True  # On continue même si on ne peut pas accepter les cookies
    
    def get_lawyers_list(self, max_lawyers=5):
        """Récupère la liste des avocats depuis la page principale (test limité)"""
        try:
            logger.info(f"Accès à la page principale: {self.search_url}")
            self.driver.get(self.search_url)
            time.sleep(3)
            
            # Accepter les cookies
            self.accept_cookies()
            time.sleep(2)
            
            # Attendre que la page soit complètement chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".directorist-listing-single"))
            )
            
            # Récupérer les liens vers les fiches d'avocats
            lawyer_cards = self.driver.find_elements(By.CSS_SELECTOR, ".directorist-listing-single")
            logger.info(f"Nombre de fiches d'avocats trouvées: {len(lawyer_cards)}")
            
            lawyers_urls = []
            count = 0
            
            for card in lawyer_cards:
                if count >= max_lawyers:
                    break
                    
                try:
                    # Chercher le lien vers la fiche détaillée
                    link_element = card.find_element(By.CSS_SELECTOR, "a[href*='/directory/']")
                    lawyer_url = link_element.get_attribute('href')
                    
                    # Récupérer le nom depuis le titre ou l'alt de l'image
                    try:
                        name_element = card.find_element(By.CSS_SELECTOR, ".directorist-listing-title a")
                        lawyer_name = name_element.text.strip()
                    except:
                        try:
                            img_element = card.find_element(By.CSS_SELECTOR, "img")
                            lawyer_name = img_element.get_attribute('alt')
                        except:
                            lawyer_name = "Nom non trouvé"
                    
                    lawyers_urls.append({
                        'name': lawyer_name,
                        'url': lawyer_url
                    })
                    
                    logger.info(f"Avocat trouvé: {lawyer_name} - {lawyer_url}")
                    count += 1
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction d'une fiche: {e}")
                    continue
            
            return lawyers_urls
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des avocats: {e}")
            return []
    
    def extract_lawyer_details(self, lawyer_info):
        """Extrait les détails d'un avocat depuis sa fiche individuelle"""
        try:
            logger.info(f"Extraction des détails pour: {lawyer_info['name']}")
            self.driver.get(lawyer_info['url'])
            time.sleep(3)
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # Initialiser les données de l'avocat
            lawyer_data = {
                'nom_complet': lawyer_info['name'],
                'url_fiche': lawyer_info['url'],
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'autres_infos': {}
            }
            
            # Extraction du nom et prénom
            try:
                name_parts = lawyer_info['name'].replace('Maître ', '').strip().split()
                if len(name_parts) >= 2:
                    lawyer_data['prenom'] = name_parts[0]
                    lawyer_data['nom'] = ' '.join(name_parts[1:])
            except:
                pass
            
            # Recherche de l'email
            try:
                email_selectors = [
                    "a[href^='mailto:']",
                    ".email",
                    ".directorist-contact-email",
                    ".contact-email"
                ]
                
                for selector in email_selectors:
                    try:
                        email_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector == "a[href^='mailto:']":
                            lawyer_data['email'] = email_element.get_attribute('href').replace('mailto:', '')
                        else:
                            lawyer_data['email'] = email_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche du téléphone
            try:
                phone_selectors = [
                    "a[href^='tel:']",
                    ".phone",
                    ".telephone",
                    ".directorist-contact-phone"
                ]
                
                for selector in phone_selectors:
                    try:
                        phone_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector == "a[href^='tel:']":
                            lawyer_data['telephone'] = phone_element.get_attribute('href').replace('tel:', '')
                        else:
                            lawyer_data['telephone'] = phone_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche de l'adresse
            try:
                address_selectors = [
                    ".directorist-contact-address",
                    ".address",
                    ".adresse",
                    ".contact-address"
                ]
                
                for selector in address_selectors:
                    try:
                        address_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        lawyer_data['adresse'] = address_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche des spécialisations/domaines de compétences
            try:
                # Méthode 1: Chercher les checkbox cochées pour les domaines de compétences
                speciality_selectors = [
                    "input[type='checkbox']:checked",
                    ".custom-checkbox input:checked",
                    ".directorist-checkbox-field input:checked",
                    "input[field_key='custom-checkbox']:checked"
                ]
                
                for selector in speciality_selectors:
                    try:
                        checkbox_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in checkbox_elements:
                            # Récupérer la valeur ou le texte associé
                            spec_value = elem.get_attribute('value')
                            if spec_value and spec_value not in lawyer_data['specialisations']:
                                lawyer_data['specialisations'].append(spec_value)
                            
                            # Essayer aussi le label associé
                            try:
                                label = elem.find_element(By.XPATH, "../label")
                                label_text = label.text.strip()
                                if label_text and label_text not in lawyer_data['specialisations']:
                                    lawyer_data['specialisations'].append(label_text)
                            except:
                                pass
                    except:
                        continue
                
                # Méthode 2: Chercher dans les div de spécialisations
                if not lawyer_data['specialisations']:
                    other_selectors = [
                        ".directorist-listing-category",
                        ".specialisation", 
                        ".category",
                        ".speciality",
                        ".domaines-competence",
                        ".competences",
                        "[class*='competence']",
                        "[class*='specialisation']"
                    ]
                    
                    for selector in other_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                spec_text = elem.text.strip()
                                if spec_text and len(spec_text) > 3 and spec_text not in lawyer_data['specialisations']:
                                    lawyer_data['specialisations'].append(spec_text)
                        except:
                            continue
                
                # Méthode 3: Recherche dans le HTML via JavaScript si disponible
                if not lawyer_data['specialisations']:
                    try:
                        js_script = """
                        var specialisations = [];
                        var checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
                        for(var i = 0; i < checkboxes.length; i++) {
                            if(checkboxes[i].value && checkboxes[i].value.length > 3) {
                                specialisations.push(checkboxes[i].value);
                            }
                        }
                        return specialisations;
                        """
                        js_specialisations = self.driver.execute_script(js_script)
                        if js_specialisations:
                            lawyer_data['specialisations'].extend(js_specialisations)
                    except:
                        pass
                        
                # Nettoyer les spécialisations (enlever les doublons et textes trop courts)
                lawyer_data['specialisations'] = list(set([
                    spec.strip() for spec in lawyer_data['specialisations'] 
                    if spec.strip() and len(spec.strip()) > 3
                ]))
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction des spécialisations: {e}")
                pass
            
            # Recherche de l'année d'inscription et autres infos
            try:
                # Récupérer tout le texte de la page pour chercher des patterns
                page_text = self.driver.find_element(By.CSS_SELECTOR, "body").text
                
                # Chercher l'année d'inscription (pattern: année entre 1950-2024)
                import re
                year_pattern = r'\b(19[5-9]\d|20[0-2]\d)\b'
                years = re.findall(year_pattern, page_text)
                if years:
                    lawyer_data['annee_inscription'] = years[0]  # Prendre la première année trouvée
                
            except:
                pass
            
            logger.info(f"Détails extraits pour {lawyer_data['nom_complet']}: Email={lawyer_data['email']}, Tél={lawyer_data['telephone']}")
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des détails pour {lawyer_info['name']}: {e}")
            return None
    
    def save_results(self, filename_prefix="dunkerque_test"):
        """Sauvegarde les résultats en JSON et CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if self.lawyers_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                            'annee_inscription', 'specialisations', 'structure', 'url_fiche', 'autres_infos']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    # Convertir la liste des spécialisations en string
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations'])
                    lawyer_copy['autres_infos'] = str(lawyer.get('autres_infos', ''))
                    writer.writerow(lawyer_copy)
        
        # Rapport textuel
        report_filename = f"{filename_prefix}_rapport_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT D'EXTRACTION DUNKERQUE - TEST ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre d'avocats extraits: {len(self.lawyers_data)}\n\n")
            
            for lawyer in self.lawyers_data:
                f.write(f"Nom: {lawyer['nom_complet']}\n")
                f.write(f"Email: {lawyer['email']}\n")
                f.write(f"Téléphone: {lawyer['telephone']}\n")
                f.write(f"Adresse: {lawyer['adresse']}\n")
                f.write(f"Spécialisations: {', '.join(lawyer['specialisations'])}\n")
                f.write(f"URL: {lawyer['url_fiche']}\n")
                f.write("-" * 50 + "\n")
        
        logger.info(f"Résultats sauvegardés: {json_filename}, {csv_filename}, {report_filename}")
        return json_filename, csv_filename, report_filename
    
    def run_test(self):
        """Lance le test de scraping sur quelques avocats"""
        try:
            logger.info("=== DÉBUT DU TEST DE SCRAPING DUNKERQUE ===")
            
            if not self.start_browser():
                return False
            
            # Étape 1: Récupérer la liste des avocats (5 pour le test)
            lawyers_urls = self.get_lawyers_list(max_lawyers=5)
            
            if not lawyers_urls:
                logger.error("Aucun avocat trouvé")
                return False
            
            logger.info(f"Test avec {len(lawyers_urls)} avocats")
            
            # Étape 2: Extraire les détails de chaque avocat
            for lawyer_info in lawyers_urls:
                lawyer_data = self.extract_lawyer_details(lawyer_info)
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                
                # Pause entre les requêtes
                time.sleep(2)
            
            # Étape 3: Sauvegarder les résultats
            json_file, csv_file, report_file = self.save_results()
            
            logger.info(f"=== TEST TERMINÉ ===")
            logger.info(f"Avocats extraits avec succès: {len(self.lawyers_data)}")
            logger.info(f"Fichiers créés: {json_file}, {csv_file}, {report_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur durant le test: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Navigateur fermé")

def main():
    scraper = DunkerqueBarScraperTest()
    success = scraper.run_test()
    
    if success:
        print("✅ Test de scraping réussi!")
        print("Vérifiez les fichiers générés pour voir les résultats.")
    else:
        print("❌ Échec du test de scraping")

if __name__ == "__main__":
    main()