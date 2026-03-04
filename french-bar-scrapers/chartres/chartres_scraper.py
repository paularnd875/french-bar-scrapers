#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import logging
import re

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chartres_production.log'),
        logging.StreamHandler()
    ]
)

class ChartresLawyerScraper:
    def __init__(self, headless=False):
        self.base_url = "https://www.ordredesavocats-chartres.com"
        self.start_url = f"{self.base_url}/Annuaire-des-avocats.html?p=0"
        self.driver = self._setup_driver(headless)
        self.lawyers_data = []
        
    def _setup_driver(self, headless):
        """Configuration du navigateur Chrome"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
        
        # Options pour éviter la détection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def accept_cookies(self):
        """Accepter les cookies si nécessaire"""
        try:
            logging.info("Tentative d'acceptation des cookies...")
            
            # Attendre et chercher les boutons de cookies
            wait = WebDriverWait(self.driver, 10)
            
            cookie_selectors = [
                "#tarteaucitronAllDeny",
                "#tarteaucitronPersonalize", 
                "#tarteaucitronAllowed",
                ".tarteaucitronAllow",
                "button[onclick*='tarteaucitron']",
                "[onclick*='acceptAll']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    logging.info(f"Bouton cookies trouvé: {selector}")
                    cookie_button.click()
                    time.sleep(2)
                    return True
                except:
                    continue
                    
            logging.info("Cookies déjà acceptés ou non présents")
            return True
            
        except Exception as e:
            logging.warning(f"Erreur cookies: {e}")
            return False
    
    def get_total_pages(self):
        """Récupérer le nombre total de pages"""
        try:
            pagination_links = self.driver.find_elements(By.CSS_SELECTOR, ".pagination a, .pagination span")
            
            if not pagination_links:
                return 1
                
            page_numbers = []
            for link in pagination_links:
                try:
                    text = link.text.strip()
                    if text.isdigit():
                        page_numbers.append(int(text))
                except:
                    continue
            
            total_pages = max(page_numbers) if page_numbers else 1
            logging.info(f"Pages détectées: {total_pages}")
            return total_pages
            
        except Exception as e:
            logging.error(f"Erreur détection pages: {e}")
            return 6  # Valeur par défaut basée sur l'observation
    
    def extract_lawyers_from_page(self):
        """Extraire la liste des avocats de la page actuelle"""
        lawyers = []
        try:
            # Attendre le chargement
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            lawyer_articles = soup.find_all('article')
            
            logging.info(f"Articles trouvés: {len(lawyer_articles)}")
            
            for article in lawyer_articles:
                try:
                    lawyer_data = {}
                    
                    # Nom et URL de la fiche
                    header = article.find('header')
                    if header:
                        # Recherche du lien principal
                        link = header.find('a')
                        if link:
                            lawyer_data['nom'] = link.get_text(strip=True)
                            href = link.get('href', '')
                            if href and href.endswith('.html'):
                                lawyer_data['url_fiche'] = f"{self.base_url}/{href}"
                    
                    # Si pas de lien trouvé dans header, chercher dans onclick
                    if 'url_fiche' not in lawyer_data and header:
                        onclick = header.get('onclick', '')
                        if onclick:
                            # Extraire le nom de fichier de onclick="location='Nom-PRENOM.html'"
                            match = re.search(r'location\s*=\s*["\']([^"\']+\.html)["\']', onclick)
                            if match:
                                filename = match.group(1)
                                lawyer_data['url_fiche'] = f"{self.base_url}/{filename}"
                                # Extraire le nom du filename si pas déjà fait
                                if 'nom' not in lawyer_data:
                                    name_part = filename.replace('.html', '').replace('-', ' ')
                                    lawyer_data['nom'] = name_part
                    
                    # Adresse et téléphone
                    article_text = article.get_text()
                    
                    # Recherche d'adresse avec patterns français
                    address_patterns = [
                        r'(\d+[\w\s\-,\.]*(?:rue|avenue|boulevard|place|allée|impasse|chemin)[\w\s\-,\.]*28\d{3}[\w\s]*)',
                        r'((?:rue|avenue|boulevard|place|allée|impasse|chemin)[\w\s\-,\.]*28\d{3}[\w\s]*)',
                        r'(28\d{3}\s*[A-Z\s]+)'
                    ]
                    
                    for pattern in address_patterns:
                        match = re.search(pattern, article_text, re.IGNORECASE)
                        if match:
                            lawyer_data['adresse'] = match.group(1).strip()
                            break
                    
                    # Téléphone
                    phone_patterns = [
                        r'(\+33[\s\.]?\d[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2})',
                        r'(0\d[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2})',
                        r'(\d{2}[\.\s]\d{2}[\.\s]\d{2}[\.\s]\d{2}[\.\s]\d{2})'
                    ]
                    
                    for pattern in phone_patterns:
                        phone_match = re.search(pattern, article_text)
                        if phone_match:
                            lawyer_data['telephone'] = phone_match.group(1)
                            break
                    
                    # Ajouter seulement si on a au moins un nom
                    if lawyer_data.get('nom') and len(lawyer_data['nom']) > 2:
                        lawyers.append(lawyer_data)
                        logging.info(f"Avocat: {lawyer_data.get('nom')}")
                
                except Exception as e:
                    logging.error(f"Erreur extraction avocat: {e}")
                    continue
            
        except Exception as e:
            logging.error(f"Erreur extraction page: {e}")
        
        return lawyers
    
    def extract_lawyer_details(self, lawyer_url):
        """Extraire les détails complets d'un avocat"""
        try:
            logging.info(f"Détails pour: {lawyer_url}")
            self.driver.get(lawyer_url)
            time.sleep(2)
            
            # Vérifier que la page s'est bien chargée
            if "404" in self.driver.title or "erreur" in self.driver.title.lower():
                logging.warning(f"Page 404 ou erreur pour {lawyer_url}")
                return {}
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            page_text = soup.get_text()
            
            details = {}
            
            # Nom complet (titre h1)
            name_elem = soup.find(['h1', 'h2'])
            if name_elem:
                details['nom_complet'] = name_elem.get_text(strip=True)
            
            # Email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_text)
            if emails:
                # Filtrer les emails génériques
                for email in emails:
                    if not any(word in email.lower() for word in ['noreply', 'contact@ordredesavocats', 'webmaster']):
                        details['email'] = email
                        break
                if 'email' not in details and emails:
                    details['email'] = emails[0]
            
            # Téléphone détaillé
            phone_patterns = [
                r'(\+33[\s\.]?\d[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2})',
                r'(0\d[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2})',
                r'(\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2}[\s\.]?\d{2})'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, page_text)
                if phone_match:
                    details['telephone_detail'] = phone_match.group(1)
                    break
            
            # Année d'inscription
            year_patterns = [
                r'inscrit[e]?[\s\w]*(?:en|depuis|le)[\s]*(\d{4})',
                r'admission[\s\w]*(\d{4})',
                r'serment[\s\w]*(\d{4})',
                r'barreau[\s\w]*(\d{4})'
            ]
            
            for pattern in year_patterns:
                year_match = re.search(pattern, page_text, re.IGNORECASE)
                if year_match:
                    year = int(year_match.group(1))
                    if 1970 <= year <= 2025:  # Années plausibles
                        details['annee_inscription'] = year
                        break
            
            # Spécialisations
            specialization_keywords = [
                'droit pénal', 'droit civil', 'droit commercial', 'droit de la famille',
                'droit du travail', 'droit immobilier', 'droit des affaires', 'droit social',
                'droit administratif', 'droit fiscal', 'droit bancaire', 'droit de l\'environnement'
            ]
            
            found_specializations = []
            page_text_lower = page_text.lower()
            for spec in specialization_keywords:
                if spec in page_text_lower:
                    found_specializations.append(spec.title())
            
            if found_specializations:
                details['specialisations'] = ', '.join(list(set(found_specializations)))
            
            # Structure/Cabinet
            structure_patterns = [
                r'(cabinet[\w\s\-\.]{5,50})',
                r'(s\.?c\.?p\.?[\w\s\-\.]{5,50})',
                r'(selarl[\w\s\-\.]{5,50})',
                r'(société[\w\s\-\.]{5,50}avocat)',
                r'(associé[e]?[\w\s\-\.]{5,50})'
            ]
            
            for pattern in structure_patterns:
                struct_match = re.search(pattern, page_text, re.IGNORECASE)
                if struct_match:
                    details['structure'] = struct_match.group(1).strip()
                    break
            
            # Adresse complète depuis la fiche
            address_patterns = [
                r'(\d+[\w\s\-,\.]*(?:rue|avenue|boulevard|place|allée|impasse|chemin)[\w\s\-,\.]*28\d{3}[\w\s]*)',
                r'((?:rue|avenue|boulevard|place|allée|impasse|chemin)[\w\s\-,\.]*28\d{3}[\w\s]*)'
            ]
            
            for pattern in address_patterns:
                addr_match = re.search(pattern, page_text, re.IGNORECASE)
                if addr_match:
                    details['adresse_complete'] = addr_match.group(1).strip()
                    break
            
            return details
            
        except Exception as e:
            logging.error(f"Erreur détails {lawyer_url}: {e}")
            return {}
    
    def run_test(self, max_pages=2):
        """Test sur 2 pages"""
        try:
            logging.info(f"=== TEST - {max_pages} pages ===")
            
            self.driver.get(self.start_url)
            time.sleep(3)
            
            self.accept_cookies()
            time.sleep(2)
            
            total_pages = self.get_total_pages()
            
            for page_num in range(min(max_pages, total_pages)):
                try:
                    if page_num > 0:
                        page_url = f"{self.base_url}/Annuaire-des-avocats.html?p={page_num}"
                        logging.info(f"Page {page_num + 1}: {page_url}")
                        self.driver.get(page_url)
                        time.sleep(3)
                    
                    lawyers = self.extract_lawyers_from_page()
                    logging.info(f"Page {page_num + 1}: {len(lawyers)} avocats")
                    
                    # Test détails sur 3 premiers avocats par page
                    for i, lawyer in enumerate(lawyers[:3]):
                        if lawyer.get('url_fiche'):
                            details = self.extract_lawyer_details(lawyer['url_fiche'])
                            lawyer.update(details)
                            time.sleep(1)
                    
                    self.lawyers_data.extend(lawyers)
                    
                except Exception as e:
                    logging.error(f"Erreur page {page_num + 1}: {e}")
                    continue
            
            self.save_results(test_mode=True)
            
        except Exception as e:
            logging.error(f"Erreur générale test: {e}")
        finally:
            self.driver.quit()
    
    def run_production(self):
        """Production complète en mode headless"""
        try:
            logging.info("=== PRODUCTION COMPLÈTE ===")
            
            self.driver.get(self.start_url)
            time.sleep(3)
            
            self.accept_cookies()
            time.sleep(2)
            
            total_pages = self.get_total_pages()
            logging.info(f"Production: {total_pages} pages")
            
            for page_num in range(total_pages):
                try:
                    if page_num > 0:
                        page_url = f"{self.base_url}/Annuaire-des-avocats.html?p={page_num}"
                        logging.info(f"PROD Page {page_num + 1}/{total_pages}")
                        self.driver.get(page_url)
                        time.sleep(2)
                    
                    lawyers = self.extract_lawyers_from_page()
                    logging.info(f"Page {page_num + 1}: {len(lawyers)} avocats")
                    
                    # Traiter tous les avocats
                    for i, lawyer in enumerate(lawyers):
                        if lawyer.get('url_fiche'):
                            logging.info(f"  Avocat {i+1}/{len(lawyers)}: {lawyer.get('nom')}")
                            details = self.extract_lawyer_details(lawyer['url_fiche'])
                            lawyer.update(details)
                            time.sleep(0.5)  # Pause courte
                    
                    self.lawyers_data.extend(lawyers)
                    
                    # Sauvegarde intermédiaire
                    if (page_num + 1) % 2 == 0:
                        self.save_intermediate(page_num + 1)
                    
                except Exception as e:
                    logging.error(f"Erreur page {page_num + 1}: {e}")
                    continue
            
            self.save_results(test_mode=False)
            
        except Exception as e:
            logging.error(f"Erreur générale production: {e}")
        finally:
            self.driver.quit()
    
    def save_intermediate(self, page_num):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chartres_partial_p{page_num}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        logging.info(f"Sauvegarde: {filename} ({len(self.lawyers_data)} avocats)")
    
    def save_results(self, test_mode=False):
        """Sauvegarde finale"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "chartres_TEST" if test_mode else "chartres_PRODUCTION"
        
        if not self.lawyers_data:
            logging.warning("Aucune donnée à sauvegarder!")
            return
        
        # CSV
        csv_file = f"{prefix}_{timestamp}.csv"
        fieldnames = set()
        for lawyer in self.lawyers_data:
            fieldnames.update(lawyer.keys())
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        # JSON
        json_file = f"{prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails_file = f"{prefix}_EMAILS_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            emails_found = []
            for lawyer in self.lawyers_data:
                if lawyer.get('email'):
                    emails_found.append(lawyer['email'])
            
            for email in sorted(set(emails_found)):
                f.write(f"{email}\n")
        
        # Rapport détaillé
        report_file = f"{prefix}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT SCRAPING BARREAU DE CHARTRES\n")
            f.write(f"{'='*50}\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}\n")
            f.write(f"Total avocats: {len(self.lawyers_data)}\n\n")
            
            # Stats
            with_email = sum(1 for l in self.lawyers_data if l.get('email'))
            with_phone = sum(1 for l in self.lawyers_data if l.get('telephone_detail'))
            with_specializations = sum(1 for l in self.lawyers_data if l.get('specialisations'))
            with_year = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
            
            f.write(f"STATISTIQUES:\n")
            f.write(f"- Emails trouvés: {with_email} ({with_email/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"- Téléphones: {with_phone} ({with_phone/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"- Spécialisations: {with_specializations} ({with_specializations/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"- Années inscription: {with_year} ({with_year/len(self.lawyers_data)*100:.1f}%)\n\n")
            
            f.write(f"EMAILS TROUVÉS:\n")
            for lawyer in self.lawyers_data:
                if lawyer.get('email'):
                    f.write(f"- {lawyer['email']} ({lawyer.get('nom', 'Sans nom')})\n")
            
            f.write(f"\nEXEMPLES DÉTAILLÉS:\n")
            for i, lawyer in enumerate(self.lawyers_data[:5]):
                f.write(f"\n{i+1}. {lawyer.get('nom', 'Sans nom')}\n")
                f.write(f"   Email: {lawyer.get('email', 'Non trouvé')}\n")
                f.write(f"   Téléphone: {lawyer.get('telephone_detail', 'Non trouvé')}\n")
                f.write(f"   Spécialisations: {lawyer.get('specialisations', 'Non trouvé')}\n")
                f.write(f"   Année: {lawyer.get('annee_inscription', 'Non trouvé')}\n")
        
        logging.info(f"=== SAUVEGARDE TERMINÉE ===")
        logging.info(f"CSV: {csv_file}")
        logging.info(f"JSON: {json_file}")
        logging.info(f"Emails: {emails_file}")
        logging.info(f"Rapport: {report_file}")

if __name__ == "__main__":
    print("=== SCRAPER BARREAU DE CHARTRES ===")
    print("1. Test (2 pages, navigateur visible)")
    print("2. Production (toutes pages, headless)")
    
    choice = input("Votre choix (1 ou 2): ").strip()
    
    if choice == "1":
        scraper = ChartresLawyerScraper(headless=False)
        scraper.run_test(max_pages=2)
    elif choice == "2":
        scraper = ChartresLawyerScraper(headless=True)
        scraper.run_production()
    else:
        print("Choix invalide")