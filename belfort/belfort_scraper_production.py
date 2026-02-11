#!/usr/bin/env python3
"""
Script de production pour scraper TOUS les avocats du barreau de Belfort
Site: https://www.avocats-belfort.com/annuaire-avocats.htm
Version améliorée avec extraction précise et mode headless
"""

import time
import json
import csv
import re
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

class BelfortBarProductionScraper:
    def __init__(self, headless=True, max_lawyers=None):
        self.base_url = "https://www.avocats-belfort.com"
        self.annuaire_url = "https://www.avocats-belfort.com/annuaire-avocats.htm"
        self.headless = headless
        self.max_lawyers = max_lawyers
        self.driver = None
        self.lawyers_data = []
        
        # Mots-clés à filtrer des spécialisations
        self.navigation_keywords = {
            'ACCUEIL', 'CONTACTS', 'ANNUAIRE', 'INFORMATIONS PRATIQUES', 
            'ESPACE AVOCATS', 'PLAN DU SITE', 'MENTIONS LÉGALES', 'ARTICLES',
            'Honoraires et protection juridique', 'Aide juridictionnelle',
            'Consultations gratuites', "Commission d'office", 'Permanences',
            'Lutte contre le blanchiment', 'Protection des données', 'Adresses utiles'
        }
        
    def setup_driver(self):
        """Configure le driver Chrome en mode headless optimisé"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def accept_cookies(self):
        """Accepte les cookies si la bannière est présente"""
        try:
            logger.info("Recherche de la bannière de cookies...")
            wait = WebDriverWait(self.driver, 5)
            
            accept_selectors = [
                "//button[contains(text(), 'ACCEPTER') or contains(text(), 'Accepter')]",
                "//a[contains(text(), 'ACCEPTER') or contains(text(), 'Accepter')]",
                "//*[@id='cookie-accept' or @class='cookie-accept']"
            ]
            
            for selector in accept_selectors:
                try:
                    accept_button = self.driver.find_element(By.XPATH, selector)
                    if accept_button.is_displayed():
                        accept_button.click()
                        logger.info("Cookies acceptés avec succès")
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
                    
            logger.info("Pas de bannière de cookies trouvée")
            return False
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'acceptation des cookies: {e}")
            return False
    
    def get_all_lawyers_urls(self):
        """Récupère toutes les URLs des profils d'avocats"""
        try:
            logger.info("Accès à la page d'annuaire...")
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            self.accept_cookies()
            
            # Attendre le chargement complet
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Chercher tous les liens vers les profils
            profile_links = set()
            
            # Chercher différents types de liens
            link_selectors = [
                "//a[contains(@href, 'maitre-') and contains(@href, '.htm')]",
                "//a[contains(text(), 'Voir le détail')]",
                "//a[contains(@href, 'annuaire/maitre-')]"
            ]
            
            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(By.XPATH, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and 'maitre-' in href and '.htm' in href:
                            # Nettoyer l'URL (enlever les ancres)
                            clean_url = href.split('#')[0]
                            profile_links.add(clean_url)
                except Exception as e:
                    logger.warning(f"Erreur avec le sélecteur {selector}: {e}")
                    continue
            
            profile_urls = list(profile_links)
            logger.info(f"Trouvé {len(profile_urls)} profils d'avocats uniques")
            
            if self.max_lawyers:
                profile_urls = profile_urls[:self.max_lawyers]
                logger.info(f"Limitation à {self.max_lawyers} avocats pour ce run")
            
            return profile_urls
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des URLs: {e}")
            return []
    
    def extract_lawyer_details(self, profile_url):
        """Extrait les détails complets d'un avocat"""
        try:
            logger.info(f"Extraction: {profile_url}")
            
            self.driver.get(profile_url)
            time.sleep(2)
            
            # Attendre le chargement
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
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
            
            # 1. Extraire le nom complet et titre
            self._extract_name_and_title(lawyer_data)
            
            # 2. Extraire les informations de contact
            self._extract_contact_info(lawyer_data)
            
            # 3. Extraire l'année d'inscription
            self._extract_inscription_year(lawyer_data)
            
            # 4. Extraire les spécialisations (de façon plus précise)
            self._extract_specializations(lawyer_data)
            
            # 5. Extraire la structure/cabinet
            self._extract_structure(lawyer_data)
            
            logger.info(f"✓ Extrait: {lawyer_data['nom_complet']}")
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de {profile_url}: {e}")
            return None
    
    def _extract_name_and_title(self, lawyer_data):
        """Extrait le nom et le titre"""
        name_selectors = [
            "//h1[contains(@class, 'titre') or contains(@class, 'nom')]",
            "//h1",
            "//h2",
            "//div[@class='titre-avocat']",
            "//*[contains(@class, 'nom-avocat') or contains(@class, 'lawyer-name')]",
            "//*[contains(text(), 'Maître') and not(ancestor::nav) and not(ancestor::menu)]"
        ]
        
        for selector in name_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 3 and ('Maître' in text or len(text.split()) >= 2):
                        if not any(nav_word in text.upper() for nav_word in ['ACCUEIL', 'CONTACT', 'ANNUAIRE', 'MENU']):
                            lawyer_data['titre'] = text
                            lawyer_data['nom_complet'] = text.replace('Maître ', '').replace('Maitre ', '').strip()
                            
                            # Séparer prénom et nom
                            name_parts = lawyer_data['nom_complet'].split()
                            if len(name_parts) >= 2:
                                lawyer_data['prenom'] = name_parts[0]
                                lawyer_data['nom'] = ' '.join(name_parts[1:])
                            return
            except Exception:
                continue
    
    def _extract_contact_info(self, lawyer_data):
        """Extrait email, téléphone et adresse"""
        # Email
        email_selectors = [
            "//a[contains(@href, 'mailto:')]",
            "//*[contains(text(), '@') and not(ancestor::nav)]"
        ]
        
        for selector in email_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if 'mailto:' in (element.get_attribute('href') or ''):
                        lawyer_data['email'] = element.get_attribute('href').replace('mailto:', '')
                        break
                    elif '@' in element.text and '.' in element.text:
                        # Extraire l'email du texte
                        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', element.text)
                        if email_match:
                            lawyer_data['email'] = email_match.group()
                            break
                if lawyer_data['email']:
                    break
            except Exception:
                continue
        
        # Téléphone
        phone_selectors = [
            "//*[contains(text(), '03 ') and not(ancestor::nav)]",
            "//*[contains(text(), '06 ') and not(ancestor::nav)]",
            "//*[contains(text(), '07 ') and not(ancestor::nav)]",
            "//*[@class='telephone' or @class='phone']"
        ]
        
        for selector in phone_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    phone_match = re.search(r'0[1-9](?:[\s\.-]?\d{2}){4}', text)
                    if phone_match:
                        lawyer_data['telephone'] = phone_match.group()
                        break
                if lawyer_data['telephone']:
                    break
            except Exception:
                continue
        
        # Adresse
        address_selectors = [
            "//*[contains(@class, 'adresse') or contains(@class, 'address')]",
            "//*[contains(text(), 'rue ') or contains(text(), 'avenue ') or contains(text(), 'boulevard ')]",
            "//*[contains(text(), 'Belfort') and not(ancestor::nav)]"
        ]
        
        for selector in address_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 10 and ('rue' in text.lower() or 'avenue' in text.lower() or 'boulevard' in text.lower() or 'belfort' in text.lower()):
                        lawyer_data['adresse'] = text
                        break
                if lawyer_data['adresse']:
                    break
            except Exception:
                continue
    
    def _extract_inscription_year(self, lawyer_data):
        """Extrait l'année d'inscription au barreau"""
        year_selectors = [
            "//*[contains(text(), 'inscrit') and not(ancestor::nav)]",
            "//*[contains(text(), 'serment') and not(ancestor::nav)]",
            "//*[contains(text(), '19') or contains(text(), '20')]"
        ]
        
        for selector in year_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text
                    year_matches = re.findall(r'\b(19[6-9]\d|20[0-2]\d)\b', text)
                    if year_matches:
                        # Prendre la première année trouvée qui semble cohérente
                        for year in year_matches:
                            if 1960 <= int(year) <= 2024:
                                lawyer_data['annee_inscription'] = year
                                return
            except Exception:
                continue
    
    def _extract_specializations(self, lawyer_data):
        """Extrait les spécialisations en filtrant les éléments de navigation"""
        # Chercher dans des zones spécifiques de contenu
        spec_selectors = [
            "//div[contains(@class, 'competence') or contains(@class, 'specialite') or contains(@class, 'domaine')]",
            "//div[contains(@class, 'activite')]",
            "//*[contains(text(), 'Droit') and not(ancestor::nav) and not(ancestor::footer)]",
            "//ul[not(ancestor::nav)]//li[contains(text(), 'Droit')]",
            "//p[contains(text(), 'Droit')]"
        ]
        
        specializations = set()
        
        for selector in spec_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 5:
                        # Filtrer les éléments de navigation
                        if text not in self.navigation_keywords:
                            # Chercher les domaines de droit
                            if 'droit' in text.lower():
                                # Nettoyer et ajouter
                                clean_text = re.sub(r'^[-•\s]+', '', text).strip()
                                if clean_text and clean_text not in self.navigation_keywords:
                                    specializations.add(clean_text)
                            elif any(keyword in text.lower() for keyword in ['pénal', 'civil', 'commercial', 'famille', 'divorce', 'immobilier', 'travail', 'social']):
                                clean_text = re.sub(r'^[-•\s]+', '', text).strip()
                                if clean_text and clean_text not in self.navigation_keywords:
                                    specializations.add(clean_text)
            except Exception:
                continue
        
        lawyer_data['specialisations'] = list(specializations)[:10]  # Limiter à 10 spécialisations max
    
    def _extract_structure(self, lawyer_data):
        """Extrait la structure/cabinet"""
        structure_selectors = [
            "//*[contains(@class, 'cabinet') or contains(@class, 'structure')]",
            "//*[contains(text(), 'Cabinet ') and not(ancestor::nav)]",
            "//*[contains(text(), 'SCP ') and not(ancestor::nav)]",
            "//*[contains(text(), 'SELARL ') and not(ancestor::nav)]"
        ]
        
        for selector in structure_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 3 and any(word in text for word in ['Cabinet', 'SCP', 'SELARL', 'Association']):
                        lawyer_data['structure'] = text
                        break
                if lawyer_data['structure']:
                    break
            except Exception:
                continue
    
    def scrape_all(self):
        """Scrape tous les avocats du barreau"""
        try:
            start_time = time.time()
            self.setup_driver()
            
            logger.info("🚀 Début du scraping complet du Barreau de Belfort")
            logger.info(f"Mode headless: {self.headless}")
            
            # Récupérer toutes les URLs
            profile_urls = self.get_all_lawyers_urls()
            
            if not profile_urls:
                logger.error("❌ Aucun profil d'avocat trouvé")
                return
            
            total_lawyers = len(profile_urls)
            logger.info(f"📋 {total_lawyers} profils à traiter")
            
            # Traiter chaque profil
            for i, url in enumerate(profile_urls, 1):
                try:
                    logger.info(f"🔄 [{i}/{total_lawyers}] Traitement en cours...")
                    
                    lawyer_data = self.extract_lawyer_details(url)
                    if lawyer_data:
                        self.lawyers_data.append(lawyer_data)
                    
                    # Pause entre les requêtes (être respectueux)
                    if i < total_lawyers:
                        time.sleep(1.5)
                        
                    # Sauvegarder périodiquement
                    if i % 10 == 0:
                        self._save_progress(f"belfort_partial_{i}")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur avec {url}: {e}")
                    continue
            
            # Sauvegarder les résultats finaux
            self.save_final_results()
            
            end_time = time.time()
            duration = (end_time - start_time) / 60
            
            logger.info(f"✅ Scraping terminé en {duration:.1f} minutes")
            logger.info(f"📊 {len(self.lawyers_data)}/{total_lawyers} avocats extraits avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur générale lors du scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def _save_progress(self, filename_prefix):
        """Sauvegarde de progression"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            progress_file = f"{filename_prefix}_{timestamp}.json"
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Progression sauvegardée: {progress_file}")
        except Exception as e:
            logger.warning(f"⚠️  Erreur de sauvegarde progression: {e}")
    
    def save_final_results(self):
        """Sauvegarde finale des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON complète
        json_filename = f"belfort_avocats_COMPLET_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV
        csv_filename = f"belfort_avocats_COMPLET_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                         'annee_inscription', 'specialisations', 'structure', 'titre', 'url']
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations'])
                    writer.writerow(lawyer_copy)
        
        # Sauvegarde emails uniquement
        emails_filename = f"belfort_EMAILS_SEULEMENT_{timestamp}.txt"
        emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        # Rapport final
        report_filename = f"belfort_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT COMPLET SCRAPING BARREAU BELFORT ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Nombre total d'avocats traités: {len(self.lawyers_data)}\n")
            f.write(f"Avocats avec email: {len(emails)}\n")
            f.write(f"Taux de réussite emails: {(len(emails)/len(self.lawyers_data)*100):.1f}%\n\n")
            
            f.write("Fichiers générés:\n")
            f.write(f"- {json_filename} (données complètes JSON)\n")
            f.write(f"- {csv_filename} (données complètes CSV)\n")
            f.write(f"- {emails_filename} (emails uniquement)\n\n")
            
            if self.lawyers_data:
                f.write("Exemple de données extraites:\n")
                example = self.lawyers_data[0]
                for key, value in example.items():
                    if key != 'url':
                        f.write(f"  {key}: {value}\n")
        
        print(f"\n🎉 === SCRAPING BELFORT TERMINÉ ===")
        print(f"📋 Avocats traités: {len(self.lawyers_data)}")
        print(f"📧 Emails trouvés: {len(emails)}")
        print(f"📁 Fichiers générés:")
        print(f"   • {json_filename}")
        print(f"   • {csv_filename}")
        print(f"   • {emails_filename}")
        print(f"   • {report_filename}")

if __name__ == "__main__":
    # Version de production - mode headless par défaut
    scraper = BelfortBarProductionScraper(headless=True)
    scraper.scrape_all()