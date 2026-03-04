#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER PRINCIPAL - BARREAU DE MEAUX
Version finale optimisée avec découverte des pages cachées
URL: https://ordreavocats-meaux.fr/fr/annuaire

UTILISATION:
python3 meaux_scraper_main.py

RÉSULTATS ATTENDUS:
- ~185 avocats (incluant pages cachées 15-19)
- Extraction complète: noms, emails, téléphones, dates serment
- Format de sortie: CSV, JSON, TXT (emails)

DÉVELOPPÉ POUR: https://github.com/paularnd875/french-bar-scrapers
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import csv
import json
import logging
from datetime import datetime
import re
import html

# Configuration du logging
def setup_logging():
    timestamp_log = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'MEAUX_SCRAPING_{timestamp_log}.log'),
            logging.StreamHandler()
        ]
    )

class MeauxBarreauScraper:
    def __init__(self, headless=True, timeout=15):
        self.headless = headless
        self.timeout = timeout
        self.lawyers = []
        self.base_url = "https://ordreavocats-meaux.fr/fr/annuaire"
        self.driver = None
        
    def setup_driver(self):
        """Configure le driver Chrome avec options optimisées"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_page_load_timeout(self.timeout)
        self.driver.implicitly_wait(5)
        logging.info("Driver Selenium configuré")

    def accept_cookies(self):
        """Accepte automatiquement les cookies TarteAuCitron"""
        cookie_selectors = [
            "button#tarteaucitronPersonalize2",
            "button[aria-label='Tout accepter']",
            ".tac_accept_all",
            "#tarteaucitronAcceptAll"
        ]
        
        for selector in cookie_selectors:
            try:
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                self.driver.execute_script("arguments[0].click();", element)
                logging.info(f"Cookies acceptés avec: {selector}")
                return True
            except:
                continue
        return False

    def discover_all_pages(self):
        """Découvre toutes les pages incluant les pages cachées"""
        self.driver.get(self.base_url)
        time.sleep(3)
        self.accept_cookies()
        time.sleep(2)
        
        # Détecter les pages visibles
        try:
            pagination_links = self.driver.find_elements(By.CSS_SELECTOR, ".pagination a")
            visible_pages = []
            for link in pagination_links:
                text = link.text.strip()
                if text.isdigit():
                    visible_pages.append(int(text))
            
            last_visible_page = max(visible_pages) if visible_pages else 14
            logging.info(f"Dernière page visible: {last_visible_page}")
        except Exception as e:
            logging.warning(f"Détection pagination échouée: {e}")
            last_visible_page = 14
        
        # Découvrir les pages cachées
        hidden_pages_count = 0
        for page_num in range(last_visible_page + 1, last_visible_page + 10):
            try:
                url = f"{self.base_url}/page-{page_num}"
                self.driver.get(url)
                time.sleep(2)
                
                lawyers_elements = self.driver.find_elements(By.CSS_SELECTOR, ".annuaire-item")
                if lawyers_elements and len(lawyers_elements) > 0:
                    hidden_pages_count += 1
                    logging.info(f"Page cachée {page_num} trouvée avec {len(lawyers_elements)} avocats")
                else:
                    break
            except:
                break
        
        total_pages = last_visible_page + hidden_pages_count
        logging.info(f"Total pages découvertes: {total_pages} (dont {hidden_pages_count} cachées)")
        return total_pages

    def parse_name(self, full_name):
        """Parse le nom complet en séparant nom/prénom avec gestion des particules"""
        if not full_name:
            return "", ""
            
        full_name = re.sub(r'\s+', ' ', html.unescape(full_name.strip()))
        particles = ['DE', 'DU', 'VAN', 'VON', 'LE', 'LA', 'DES', "D'", "D'"]
        
        parts = full_name.split(' ')
        if len(parts) < 2:
            return full_name, ""
            
        # Le premier mot est toujours le nom
        nom_parts = [parts[0]]
        i = 1
        
        # Ajouter les particules et mots en majuscules au nom
        while i < len(parts) and (parts[i].upper() in particles or parts[i].isupper()):
            nom_parts.append(parts[i])
            i += 1
        
        # Le reste constitue le prénom
        prenom_parts = parts[i:]
        
        return " ".join(nom_parts), " ".join(prenom_parts)

    def extract_lawyer_data(self, lawyer_element, page_num):
        """Extrait toutes les données d'un avocat"""
        try:
            lawyer_data = {
                'nom': '',
                'prenom': '',
                'cabinet': '',
                'adresse': '',
                'ville': '',
                'code_postal': '',
                'telephone': '',
                'email': '',
                'date_serment': '',
                'case_palais': '',
                'specialisations': [],
                'activites_dominantes': [],
                'langues': [],
                'fax': '',
                'page': page_num,
                'lien_source': self.driver.current_url
            }
            
            # Déplier les détails
            try:
                details_btn = lawyer_element.find_element(By.CSS_SELECTOR, ".details-avocat")
                self.driver.execute_script("arguments[0].click();", details_btn)
                time.sleep(1.5)
            except:
                pass
            
            # Extraction du nom
            try:
                name_element = lawyer_element.find_element(By.CSS_SELECTOR, ".nom a, .nom")
                full_name = name_element.text.strip()
                nom, prenom = self.parse_name(full_name)
                lawyer_data['nom'] = nom
                lawyer_data['prenom'] = prenom
            except:
                logging.warning("Nom non trouvé")
                return None
            
            # Attendre le chargement des détails
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".details"))
                )
            except:
                pass
            
            # Email
            try:
                email_link = lawyer_element.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                lawyer_data['email'] = email_link.get_attribute("href").replace("mailto:", "")
            except:
                pass
            
            # Téléphone
            try:
                tel_link = lawyer_element.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
                lawyer_data['telephone'] = tel_link.get_attribute("href").replace("tel:", "")
            except:
                pass
            
            # Date de serment
            try:
                details_text = lawyer_element.text
                serment_match = re.search(r'Serment du (\d{2}/\d{2}/\d{4})', details_text)
                if serment_match:
                    lawyer_data['date_serment'] = serment_match.group(1)
            except:
                pass
            
            # Activités dominantes
            try:
                details_text = lawyer_element.text
                if "ACTIVITÉS DOMINANTES" in details_text:
                    lines = details_text.split('\n')
                    collecting_activities = False
                    activities = []
                    
                    for line in lines:
                        line = line.strip()
                        if "ACTIVITÉS DOMINANTES" in line:
                            collecting_activities = True
                            continue
                        elif collecting_activities:
                            if line and not line.isupper() and "Droit" in line:
                                for activity in re.split(r'[,;|]', line):
                                    activity = activity.strip()
                                    if activity and len(activity) > 3:
                                        activities.append(activity)
                            elif line.isupper() or not line:
                                break
                    
                    lawyer_data['activites_dominantes'] = activities[:5]
            except:
                pass
                
            return lawyer_data
            
        except Exception as e:
            logging.error(f"Erreur extraction avocat: {e}")
            return None

    def scrape_all_pages(self):
        """Lance l'extraction complète de toutes les pages"""
        self.setup_driver()
        
        # Découvrir toutes les pages
        total_pages = self.discover_all_pages()
        
        # Extraire chaque page
        for page_num in range(1, total_pages + 1):
            try:
                url = f"{self.base_url}/page-{page_num}" if page_num > 1 else self.base_url
                logging.info(f"Extraction page {page_num}: {url}")
                
                self.driver.get(url)
                time.sleep(2)
                
                if page_num == 1:
                    self.accept_cookies()
                    time.sleep(1)
                
                # Attendre les éléments avocats
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".annuaire-item"))
                    )
                except TimeoutException:
                    logging.warning(f"Page {page_num} vide")
                    continue
                
                lawyers_elements = self.driver.find_elements(By.CSS_SELECTOR, ".annuaire-item")
                
                if not lawyers_elements:
                    continue
                
                page_type = "CACHÉE" if page_num > 14 else "normale"
                logging.info(f"Page {page_num} ({page_type}): {len(lawyers_elements)} avocats")
                
                # Extraire chaque avocat
                for i, lawyer_element in enumerate(lawyers_elements, 1):
                    logging.info(f"Extraction {i}/{len(lawyers_elements)} (page {page_num})")
                    
                    lawyer_data = self.extract_lawyer_data(lawyer_element, page_num)
                    if lawyer_data:
                        self.lawyers.append(lawyer_data)
                        email_info = f" - {lawyer_data.get('email', 'N/A')}"
                        logging.info(f"✓ {lawyer_data['nom']} {lawyer_data['prenom']}{email_info}")
                    
                    time.sleep(0.5)
                
                logging.info(f"Page {page_num}: {len(lawyers_elements)} avocats extraits")
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Erreur page {page_num}: {e}")
                continue

    def save_results(self):
        """Sauvegarde les résultats dans tous les formats"""
        if not self.lawyers:
            logging.info("Aucun avocat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_file = f"MEAUX_AVOCATS_{len(self.lawyers)}avocats_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['nom', 'prenom', 'cabinet', 'adresse', 'ville', 'code_postal', 
                         'telephone', 'email', 'date_serment', 'case_palais', 
                         'specialisations', 'activites_dominantes', 'langues', 'fax', 'page', 'lien_source']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers:
                row = lawyer.copy()
                # Convertir les listes en chaînes pour CSV
                row['activites_dominantes'] = ' | '.join(lawyer['activites_dominantes']) if lawyer['activites_dominantes'] else ''
                row['specialisations'] = ' | '.join(lawyer['specialisations']) if lawyer['specialisations'] else ''
                row['langues'] = ' | '.join(lawyer['langues']) if lawyer['langues'] else ''
                writer.writerow(row)
        
        # JSON
        json_file = f"MEAUX_AVOCATS_{len(self.lawyers)}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails
        emails = sorted(set([l['email'] for l in self.lawyers if l.get('email')]))
        email_file = f"MEAUX_EMAILS_{len(emails)}uniques_{timestamp}.txt"
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        # Statistiques
        emails_count = len(emails)
        hidden_lawyers = len([l for l in self.lawyers if l['page'] > 14])
        
        print(f"\n🎉 EXTRACTION MEAUX TERMINÉE !")
        print(f"📊 {len(self.lawyers)} avocats extraits")
        if hidden_lawyers > 0:
            print(f"🔍 {hidden_lawyers} avocats des pages cachées (15-19)")
        print(f"📧 {emails_count} emails ({emails_count/len(self.lawyers)*100:.1f}%)")
        print(f"\n📁 Fichiers générés:")
        print(f"  📊 CSV: {csv_file}")
        print(f"  🗂️  JSON: {json_file}")
        print(f"  📧 Emails: {email_file}")
        
        return csv_file, json_file, email_file

    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()

def main():
    print("=" * 70)
    print("🏛️  SCRAPER BARREAU DE MEAUX - VERSION FINALE")
    print("=" * 70)
    print("🌐 URL: https://ordreavocats-meaux.fr/fr/annuaire")
    print("🎯 Objectif: ~185 avocats (pages cachées incluses)")
    print("📊 Extraction: Noms, emails, téléphones, dates serment")
    
    setup_logging()
    scraper = MeauxBarreauScraper(headless=True)
    
    try:
        print("\n🚀 Démarrage de l'extraction complète...")
        start_time = time.time()
        
        scraper.scrape_all_pages()
        
        end_time = time.time()
        duration = (end_time - start_time) / 60
        print(f"\n⏱️  Durée: {duration:.1f} minutes")
        
        scraper.save_results()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        logging.error(f"Erreur générale: {e}")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()