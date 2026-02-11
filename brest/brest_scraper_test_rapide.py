#!/usr/bin/env python3
"""
🧪 Scraper Barreau de Brest - Version test rapide
Test rapide sur 3 pages pour validation

Usage:
    python3 brest_scraper_test_rapide.py      # Test headless (3 pages)
    python3 brest_scraper_test_rapide.py -v   # Test visuel pour debug
"""

import time
import json
import csv
import re
import argparse
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

class BrestLawyerTester:
    """Version test rapide du scraper Brest"""
    
    def __init__(self, headless=True):
        self.setup_driver(headless)
        self.base_url = "https://www.avocats-brest.fr/avocats/"
        
    def setup_driver(self, headless=True):
        """Configure le driver Chrome"""
        options = Options()
        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)

    def extract_lawyer_data_from_page(self):
        """Extrait rapidement les données essentielles"""
        try:
            # Attendre le chargement
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Chercher tous les liens "Plus d'infos"
            plus_info_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), \"Plus d'infos\")]")
            
            lawyers_data = []
            
            for link in plus_info_links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extraire l'email depuis l'URL
                    email_match = re.search(r'email=([^&]+)', href)
                    email = email_match.group(1) if email_match else ""
                    
                    # Extraire le nom depuis l'URL
                    url_name_match = re.search(r'/avocats/([^/?]+)', href)
                    nom_slug = url_name_match.group(1) if url_name_match else ""
                    
                    # Convertir le slug en nom lisible
                    nom_complet = nom_slug.replace('-', ' ').title() if nom_slug else ""
                    
                    # Chercher le téléphone dans le conteneur parent
                    parent_container = link.find_element(By.XPATH, "./ancestor::li | ./ancestor::div[contains(@class, 'jobs-content')]")
                    
                    telephone = ""
                    phone_elements = parent_container.find_elements(By.XPATH, ".//*[contains(text(), '02') or contains(text(), '06') or contains(text(), '07')]")
                    for phone_el in phone_elements:
                        phone_text = phone_el.text.strip()
                        phone_match = re.search(r'(\b(?:02|06|07|01|03|04|05|08|09)\s?(?:\d{2}\s?){4}\b)', phone_text)
                        if phone_match:
                            telephone = phone_match.group(1).strip()
                            break
                    
                    lawyer_data = {
                        'nom_complet': nom_complet,
                        'prenom': nom_complet.split()[0] if nom_complet else "",
                        'nom': ' '.join(nom_complet.split()[1:]) if len(nom_complet.split()) > 1 else nom_complet,
                        'email': email,
                        'telephone': telephone,
                        'url_fiche': href
                    }
                    
                    lawyers_data.append(lawyer_data)
                    
                except Exception as e:
                    logger.warning(f"Erreur extraction avocat: {e}")
                    continue
            
            logger.info(f"✅ {len(lawyers_data)} avocats extraits de cette page")
            return lawyers_data
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction page: {e}")
            return []

    def test_quick_scraping(self, max_pages=3):
        """Test rapide sur les premières pages"""
        try:
            logger.info(f"🧪 === TEST RAPIDE BREST ({max_pages} PAGES) ===")
            
            all_lawyers = []
            
            for page_num in range(1, max_pages + 1):
                if page_num == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}?page_job={page_num}"
                
                logger.info(f"📄 Page {page_num}: {url}")
                self.driver.get(url)
                
                # Extraire les données
                page_lawyers = self.extract_lawyer_data_from_page()
                all_lawyers.extend(page_lawyers)
                
                logger.info(f"📊 Page {page_num}: {len(page_lawyers)} avocats - Total: {len(all_lawyers)}")
                
                time.sleep(1)  # Pause courte
            
            return all_lawyers
            
        except Exception as e:
            logger.error(f"❌ Erreur test: {e}")
            return []

    def save_test_results(self, results, filename_prefix="brest_test"):
        """Sauvegarde rapide des résultats de test"""
        if not results:
            print("❌ Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'url_fiche']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        # Emails seulement
        email_filename = f"{filename_prefix}_emails_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as f:
            emails = [r['email'] for r in results if r.get('email')]
            f.write('\n'.join(sorted(emails)))
        
        logger.info(f"💾 Fichiers créés:")
        logger.info(f"  📋 JSON: {json_filename}")
        logger.info(f"  📊 CSV: {csv_filename}")
        logger.info(f"  📧 Emails: {email_filename}")

    def close(self):
        """Ferme le driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Test principal"""
    parser = argparse.ArgumentParser(description='Test rapide Barreau de Brest')
    parser.add_argument('-v', '--visual', action='store_true', help='Mode visuel pour debug')
    args = parser.parse_args()
    
    headless = not args.visual
    
    print("🧪 === TEST RAPIDE BARREAU DE BREST ===")
    print(f"👁️  Mode: {'Visuel' if not headless else 'Headless'}")
    print(f"📄 Pages: 3 (test)")
    print(f"🌐 Site: https://www.avocats-brest.fr/avocats/")
    print()
    
    tester = BrestLawyerTester(headless=headless)
    
    try:
        results = tester.test_quick_scraping(max_pages=3)
        
        if results:
            # Statistiques
            emails_found = sum(1 for r in results if r.get('email'))
            phones_found = sum(1 for r in results if r.get('telephone'))
            
            print(f"\n🎯 === RÉSULTATS DU TEST ===")
            print(f"👥 Avocats extraits: {len(results)}")
            print(f"📧 Emails trouvés: {emails_found}/{len(results)} ({emails_found/len(results)*100:.1f}%)")
            print(f"📞 Téléphones trouvés: {phones_found}/{len(results)} ({phones_found/len(results)*100:.1f}%)")
            
            print(f"\n📋 Premiers résultats:")
            for i, result in enumerate(results[:10], 1):
                print(f"{i}. {result.get('nom_complet', 'N/A')}")
                print(f"   📧 {result.get('email', 'Non trouvé')}")
                print(f"   📞 {result.get('telephone', 'Non trouvé')}")
                print()
            
            # Sauvegarder
            tester.save_test_results(results)
            print(f"✅ Test terminé avec succès!")
        else:
            print("❌ Aucun résultat extrait")
        
    except KeyboardInterrupt:
        print("\n⚡ Arrêt demandé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        tester.close()

if __name__ == "__main__":
    main()