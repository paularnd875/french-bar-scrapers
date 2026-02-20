#!/usr/bin/env python3
"""
Scraper FINAL pour le Barreau de Saverne
Version corrigée pour récupérer TOUS les avocats avec informations complètes
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
import re
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

class SaverneScraperFinal:
    def __init__(self, headless=True, test_mode=False):
        self.base_url = "https://avocats-saverne.com"
        self.annuaire_url = "https://avocats-saverne.com/annuaire-des-avocats/"
        self.avocats_data = []
        self.headless = headless
        self.test_mode = test_mode
        self.driver = None
        self.processed_urls = set()
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
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
        """Accepter les cookies"""
        try:
            logger.info("Acceptation des cookies...")
            cookie_button = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepter') or contains(@class, 'cli-plugin-main-button')]"))
            )
            cookie_button.click()
            logger.info("✓ Cookies acceptés")
            time.sleep(2)
            return True
        except TimeoutException:
            try:
                cookie_accept = self.driver.find_element(By.CSS_SELECTOR, "[data-cli_action='accept']")
                cookie_accept.click()
                logger.info("✓ Cookies acceptés (méthode 2)")
                time.sleep(2)
                return True
            except NoSuchElementException:
                logger.info("Aucune bannière de cookies")
                return True
        except Exception as e:
            logger.warning(f"Erreur cookies: {e}")
            return False
            
    def get_all_lawyer_links(self):
        """Récupérer tous les liens uniques des avocats"""
        try:
            logger.info("Récupération des liens d'avocats...")
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            self.accept_cookies()
            
            unique_links = set()
            
            # Chercher tous les liens vers les fiches d'avocats
            selectors_to_try = [
                "a[href*='/avocats/maitre-']",
                "a[href*='/avocats/']"
            ]
            
            for selector in selectors_to_try:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and '/avocats/maitre-' in href:
                            unique_links.add(href)
                    if unique_links:
                        logger.info(f"Trouvé {len(unique_links)} liens avec {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Sélecteur {selector} failed: {e}")
            
            # Méthode alternative si nécessaire
            if not unique_links:
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link['href']
                    if '/avocats/maitre-' in href:
                        if href.startswith('/'):
                            href = self.base_url + href
                        elif not href.startswith('http'):
                            href = self.base_url + '/' + href
                        unique_links.add(href)
            
            lawyer_links = sorted(list(unique_links))
            logger.info(f"Total: {len(lawyer_links)} avocats uniques trouvés")
            
            if self.test_mode:
                logger.info("MODE TEST: limitation à 10 avocats")
                lawyer_links = lawyer_links[:10]
            
            return lawyer_links
            
        except Exception as e:
            logger.error(f"Erreur récupération liens: {e}")
            return []
    
    def extract_lawyer_details(self, url):
        """Extraire les détails d'un avocat"""
        try:
            if url in self.processed_urls:
                return None
                
            self.processed_urls.add(url)
            
            logger.info(f"Extraction: {url}")
            self.driver.get(url)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            lawyer_data = {
                'prenom': '',
                'nom': '',
                'nom_complet': '',
                'annee_inscription': '',
                'specialisations': '',
                'competences': '',
                'activites_dominantes': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'email': '',
                'site_web': '',
                'source': url
            }
            
            # Nom complet
            name_selectors = ['h1.entry-title', 'h1', '.lawyer-name', '.entry-title']
            for selector in name_selectors:
                try:
                    name_element = soup.select_one(selector)
                    if name_element and name_element.get_text().strip():
                        full_name = name_element.get_text().strip()
                        lawyer_data['nom_complet'] = full_name
                        
                        # Séparer prénom et nom
                        name_parts = self.split_name_intelligently(full_name)
                        lawyer_data['prenom'] = name_parts['prenom']
                        lawyer_data['nom'] = name_parts['nom']
                        break
                except Exception:
                    continue
            
            # Contenu textuel pour extraction
            text_content = soup.get_text()
            
            # Email
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
            if email_match:
                lawyer_data['email'] = email_match.group(0)
            
            # Téléphone
            phone_patterns = [
                r'(\+33\s?[0-9]\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2})',
                r'(0[0-9]\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2})',
                r'(0[0-9][0-9]{8})'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text_content)
                if phone_match:
                    phone = phone_match.group(1).strip()
                    phone = re.sub(r'\s+', '', phone)
                    lawyer_data['telephone'] = phone
                    break
            
            # Année d'inscription
            inscription_patterns = [
                r'inscrit[e]?\s+(?:au barreau\s+)?(?:depuis\s+|en\s+)?(\d{4})',
                r'barreau[^\d]*(\d{4})',
                r'serment[^\d]*(\d{4})',
                r'asserment[ée][^\d]*(\d{4})'
            ]
            
            for pattern in inscription_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    year = match.group(1)
                    if 1970 <= int(year) <= 2030:
                        lawyer_data['annee_inscription'] = year
                        break
            
            # Spécialisations 
            spec_keywords = ['spécialisations', 'spécialisation', 'compétences', 'domaines']
            specializations_found = []
            
            for keyword in spec_keywords:
                pattern = f'{keyword}[^:]*:([^.\n]*)'
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    clean_spec = match.strip()
                    if clean_spec and len(clean_spec) > 5:
                        specializations_found.append(clean_spec)
            
            if specializations_found:
                lawyer_data['specialisations'] = ' | '.join(set(specializations_found))
            
            # Structure/Cabinet
            structure_keywords = ['cabinet', 'structure', 'société']
            for keyword in structure_keywords:
                pattern = f'{keyword}[^:]*:([^.\n]*)'
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    lawyer_data['structure'] = match.group(1).strip()
                    break
            
            # Adresse
            address_patterns = [
                r'(\d+[^\n]*(?:rue|avenue|boulevard|place)[^\n]*)',
                r'(\d{5}\s+[A-Za-z][^\n]*)'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    address = match.group(1).strip()
                    if len(address) > 10:
                        lawyer_data['adresse'] = address
                        break
            
            logger.info(f"✓ {lawyer_data['nom_complet']} - {lawyer_data['email']}")
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur extraction {url}: {e}")
            return None
    
    def split_name_intelligently(self, full_name):
        """Séparer intelligemment prénom et nom"""
        # Nettoyer
        clean_name = re.sub(r'^(Maître|Me\.?|M\.?|Mme\.?)\s+', '', full_name, flags=re.IGNORECASE)
        clean_name = clean_name.strip()
        
        name_parts = clean_name.split()
        
        if len(name_parts) == 1:
            return {'prenom': '', 'nom': name_parts[0]}
        elif len(name_parts) == 2:
            return {'prenom': name_parts[0], 'nom': name_parts[1]}
        else:
            # Pour les noms composés
            if name_parts[-1].isupper():
                # Dernier mot en majuscules = nom de famille
                prenom = ' '.join(name_parts[:-1])
                nom = name_parts[-1]
            else:
                # Par défaut: dernier mot = nom
                prenom = ' '.join(name_parts[:-1])
                nom = name_parts[-1]
            
            return {'prenom': prenom, 'nom': nom}
    
    def run_scraping(self):
        """Lancer le scraping"""
        try:
            mode_str = "TEST" if self.test_mode else "PRODUCTION"
            logger.info(f"=== SCRAPING {mode_str} SAVERNE ===")
            
            self.setup_driver()
            
            # Récupérer tous les liens
            lawyer_urls = self.get_all_lawyer_links()
            
            if not lawyer_urls:
                logger.error("Aucun avocat trouvé !")
                return
            
            logger.info(f"Traitement de {len(lawyer_urls)} avocats...")
            
            # Traiter chaque avocat
            for i, url in enumerate(lawyer_urls, 1):
                logger.info(f"\n=== Avocat {i}/{len(lawyer_urls)} ===")
                lawyer_data = self.extract_lawyer_details(url)
                
                if lawyer_data:
                    self.avocats_data.append(lawyer_data)
                
                time.sleep(1.5)
                
                # Sauvegarde intermédiaire
                if i % 5 == 0:
                    self.save_backup(i)
            
            # Sauvegarder résultats finaux
            self.save_final_results()
            
        except Exception as e:
            logger.error(f"Erreur générale: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_backup(self, count):
        """Sauvegarde intermédiaire"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"SAVERNE_BACKUP_{count}_{timestamp}.json"
            
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(self.avocats_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Backup: {backup_filename}")
        except Exception as e:
            logger.error(f"Erreur backup: {e}")
    
    def save_final_results(self):
        """Sauvegarder les résultats finaux"""
        if not self.avocats_data:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_str = "TEST" if self.test_mode else "PRODUCTION"
        
        # CSV
        df = pd.DataFrame(self.avocats_data)
        csv_filename = f"SAVERNE_{mode_str}_FINAL_{len(self.avocats_data)}_avocats_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # JSON
        json_filename = f"SAVERNE_{mode_str}_FINAL_{len(self.avocats_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.avocats_data, f, indent=2, ensure_ascii=False)
        
        # Emails uniquement
        emails = [a['email'] for a in self.avocats_data if a['email']]
        unique_emails = sorted(set(emails))
        
        if unique_emails:
            emails_filename = f"SAVERNE_{mode_str}_EMAILS_{len(unique_emails)}_uniques_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as f:
                for email in unique_emails:
                    f.write(f"{email}\n")
        
        # Rapport complet
        report_filename = f"SAVERNE_{mode_str}_RAPPORT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT SCRAPING {mode_str} SAVERNE ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total avocats: {len(self.avocats_data)}\n")
            f.write(f"Emails trouvés: {len(unique_emails)}\n")
            f.write(f"Avec année inscription: {len([a for a in self.avocats_data if a['annee_inscription']])}\n")
            f.write(f"Avec spécialisations: {len([a for a in self.avocats_data if a['specialisations']])}\n")
            f.write(f"Avec téléphone: {len([a for a in self.avocats_data if a['telephone']])}\n\n")
            
            f.write("=== DÉTAIL PAR AVOCAT ===\n")
            f.write("-" * 80 + "\n")
            for i, avocat in enumerate(self.avocats_data, 1):
                f.write(f"{i}. {avocat['nom_complet']}\n")
                f.write(f"   Prénom: {avocat['prenom']}\n")
                f.write(f"   Nom: {avocat['nom']}\n")
                f.write(f"   Email: {avocat['email']}\n")
                f.write(f"   Téléphone: {avocat['telephone']}\n")
                f.write(f"   Année: {avocat['annee_inscription']}\n")
                f.write(f"   Spécialisations: {avocat['specialisations']}\n")
                f.write(f"   Structure: {avocat['structure']}\n")
                f.write(f"   Source: {avocat['source']}\n")
                f.write("-" * 50 + "\n")
        
        logger.info(f"\n🎉 SCRAPING TERMINÉ ! 🎉")
        logger.info(f"✅ Fichiers créés:")
        logger.info(f"📊 CSV: {csv_filename}")
        logger.info(f"📋 JSON: {json_filename}")
        if unique_emails:
            logger.info(f"📧 Emails: {emails_filename}")
        logger.info(f"📄 Rapport: {report_filename}")
        logger.info(f"👥 Total: {len(self.avocats_data)} avocats")
        logger.info(f"📧 Emails: {len(unique_emails)} uniques")

if __name__ == "__main__":
    import sys
    
    # Arguments
    test_mode = '--test' in sys.argv
    visible_mode = '--visible' in sys.argv
    
    if test_mode:
        print("🧪 MODE TEST (10 avocats maximum)")
    if visible_mode:
        print("👁️ MODE VISIBLE (avec fenêtres)")
    
    scraper = SaverneScraperFinal(
        headless=not visible_mode,
        test_mode=test_mode
    )
    scraper.run_scraping()