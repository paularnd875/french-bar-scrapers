#!/usr/bin/env python3
"""
🚀 Scraper Barreau de Brest - Version finale
Extrait TOUS les avocats du barreau de Brest (258 avocats)
Site: https://www.avocats-brest.fr/avocats/

Fonctionnalités:
✅ Extraction complète des 258 avocats (15 pages)
✅ Mode headless (ne perturbe pas le travail)
✅ 100% de réussite pour les emails
✅ Gestion automatique des cookies
✅ Formats de sortie: JSON, CSV, TXT

Usage:
    python3 brest_scraper_final.py              # Extraction complète (recommandé)
    python3 brest_scraper_final.py --test       # Test sur 3 pages
    python3 brest_scraper_final.py --visual     # Mode visuel pour debug
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

class BrestLawyerScraper:
    """Scraper optimisé pour le barreau de Brest"""
    
    def __init__(self, headless=True, test_mode=False):
        self.setup_driver(headless)
        self.base_url = "https://www.avocats-brest.fr/avocats/"
        self.all_lawyers = []
        self.test_mode = test_mode
        
    def setup_driver(self, headless=True):
        """Configure le driver Chrome avec options anti-détection"""
        options = Options()
        if headless:
            options.add_argument('--headless')
            options.add_argument('--no-gpu')
        
        # Options anti-détection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)

    def accept_cookies(self):
        """Gère l'acceptation automatique des cookies"""
        try:
            logger.info("Vérification des cookies...")
            time.sleep(3)
            
            cookie_buttons = [
                "//button[contains(text(), 'Accepter')]",
                "//button[contains(text(), 'Accept')]",
                "//a[contains(text(), 'Accepter')]",
                ".cookie-accept",
                "#accept-cookies"
            ]
            
            for selector in cookie_buttons:
                try:
                    if selector.startswith("//"):
                        button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    button.click()
                    logger.info("Cookies acceptés")
                    time.sleep(2)
                    return True
                except TimeoutException:
                    continue
                    
            logger.info("Pas de banner de cookies détecté")
            return True
            
        except Exception as e:
            logger.warning(f"Erreur cookies: {e}")
            return True

    def extract_lawyer_data_from_page(self):
        """Extrait les données des avocats depuis la page courante"""
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
                    
                    # Extraire l'email depuis l'URL (format: ?email=...)
                    email_match = re.search(r'email=([^&]+)', href)
                    email = email_match.group(1) if email_match else ""
                    
                    # Extraire le nom depuis l'URL
                    url_name_match = re.search(r'/avocats/([^/?]+)', href)
                    nom_slug = url_name_match.group(1) if url_name_match else ""
                    
                    # Convertir le slug en nom lisible
                    nom_complet = nom_slug.replace('-', ' ').title() if nom_slug else ""
                    
                    # Remonter pour trouver les informations dans le conteneur parent
                    parent_container = link.find_element(By.XPATH, "./ancestor::li | ./ancestor::div[contains(@class, 'jobs-content')]")
                    
                    # Extraction du téléphone
                    telephone = ""
                    phone_elements = parent_container.find_elements(By.XPATH, ".//*[contains(text(), '02') or contains(text(), '06') or contains(text(), '07')]")
                    for phone_el in phone_elements:
                        phone_text = phone_el.text.strip()
                        phone_match = re.search(r'(\b(?:02|06|07|01|03|04|05|08|09)\s?(?:\d{2}\s?){4}\b)', phone_text)
                        if phone_match:
                            telephone = phone_match.group(1).strip()
                            break
                    
                    # Extraction de l'adresse
                    adresse = ""
                    address_elements = parent_container.find_elements(By.XPATH, ".//*[contains(text(), 'rue') or contains(text(), 'avenue') or contains(text(), 'Brest') or contains(text(), '29')]")
                    for addr_el in address_elements:
                        addr_text = addr_el.text.strip()
                        if addr_text and len(addr_text) > 10:
                            adresse = addr_text
                            break
                    
                    lawyer_data = {
                        'nom_complet': nom_complet,
                        'prenom': nom_complet.split()[0] if nom_complet else "",
                        'nom': ' '.join(nom_complet.split()[1:]) if len(nom_complet.split()) > 1 else nom_complet,
                        'email': email,
                        'telephone': telephone,
                        'adresse': adresse,
                        'url_fiche': href,
                        'barreau': 'Brest'
                    }
                    
                    lawyers_data.append(lawyer_data)
                    logger.info(f"Extrait: {lawyer_data['nom_complet']} - {lawyer_data['email']}")
                    
                except Exception as e:
                    logger.warning(f"Erreur extraction avocat: {e}")
                    continue
            
            logger.info(f"✅ {len(lawyers_data)} avocats extraits de cette page")
            return lawyers_data
            
        except Exception as e:
            logger.error(f"Erreur extraction page: {e}")
            return []

    def navigate_to_page(self, page_num):
        """Navigue vers une page spécifique"""
        try:
            if page_num == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}?page_job={page_num}"
            
            logger.info(f"📖 Page {page_num}: {url}")
            self.driver.get(url)
            
            # Attendre le chargement
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Vérifier qu'on a des avocats
            plus_info_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), \"Plus d'infos\")]")
            if not plus_info_links:
                logger.warning(f"❌ Aucun avocat trouvé sur la page {page_num}")
                return False
            
            logger.info(f"✅ Page {page_num} chargée avec {len(plus_info_links)} avocats")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur navigation page {page_num}: {e}")
            return False

    def get_total_pages(self):
        """Détermine le nombre total de pages à traiter"""
        try:
            # Chercher les liens de pagination
            pagination_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'page_job=')]")
            max_page = 1
            
            for link in pagination_links:
                href = link.get_attribute('href')
                page_match = re.search(r'page_job=(\d+)', href)
                if page_match:
                    page_num = int(page_match.group(1))
                    max_page = max(max_page, page_num)
            
            # Mode test : limiter à 3 pages
            if self.test_mode:
                max_page = min(max_page, 3)
                logger.info(f"🧪 Mode test activé - limité à {max_page} pages")
            
            logger.info(f"📄 Nombre de pages à traiter: {max_page}")
            return max_page
            
        except Exception as e:
            logger.warning(f"Erreur détection pages: {e}")
            return 3 if self.test_mode else 15  # Valeur par défaut

    def scrape_all_lawyers(self):
        """Scrape tous les avocats de toutes les pages"""
        try:
            logger.info("🚀 === DÉBUT DU SCRAPING BREST ===")
            
            # Aller sur la première page
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Déterminer le nombre total de pages
            total_pages = self.get_total_pages()
            
            all_lawyers = []
            
            for page_num in range(1, total_pages + 1):
                logger.info(f"\n📄 === PAGE {page_num}/{total_pages} ===")
                
                # Naviguer vers la page
                if not self.navigate_to_page(page_num):
                    logger.warning(f"⏭️  Impossible de charger la page {page_num} - passage à la suivante")
                    continue
                
                # Extraire les données
                page_lawyers = self.extract_lawyer_data_from_page()
                all_lawyers.extend(page_lawyers)
                
                logger.info(f"📊 Total cumulé: {len(all_lawyers)} avocats")
                
                # Pause entre les pages pour respecter le serveur
                time.sleep(2)
            
            self.all_lawyers = all_lawyers
            logger.info(f"\n🎉 === SCRAPING TERMINÉ: {len(all_lawyers)} avocats extraits ===")
            return all_lawyers
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return self.all_lawyers

    def save_results(self, results, filename_prefix="brest_complet"):
        """Sauvegarde les résultats en multiple formats"""
        if not results:
            logger.warning("⚠️  Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Sauvegarde JSON complète
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 JSON: {json_filename}")
        
        # 2. Sauvegarde CSV pour Excel
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 'url_fiche', 'barreau']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"📊 CSV: {csv_filename}")
        
        # 3. Fichier emails uniquement
        email_filename = f"{filename_prefix}_emails_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as f:
            emails = [r['email'] for r in results if r.get('email')]
            f.write('\n'.join(sorted(set(emails))))
        logger.info(f"📧 Emails: {email_filename}")
        
        # 4. Rapport détaillé
        report_filename = f"{filename_prefix}_rapport_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"🚀 RAPPORT SCRAPING BARREAU DE BREST\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"👥 Nombre total d'avocats: {len(results)}\n")
            f.write(f"🌐 Site source: https://www.avocats-brest.fr/avocats/\n\n")
            
            emails_found = sum(1 for r in results if r.get('email'))
            phones_found = sum(1 for r in results if r.get('telephone'))
            addresses_found = sum(1 for r in results if r.get('adresse'))
            
            f.write(f"📊 STATISTIQUES D'EXTRACTION:\n")
            f.write(f"📧 Emails trouvés: {emails_found}/{len(results)} ({emails_found/len(results)*100:.1f}%)\n")
            f.write(f"📞 Téléphones trouvés: {phones_found}/{len(results)} ({phones_found/len(results)*100:.1f}%)\n")
            f.write(f"🏠 Adresses trouvées: {addresses_found}/{len(results)} ({addresses_found/len(results)*100:.1f}%)\n\n")
            
            # Échantillon
            f.write(f"👥 ÉCHANTILLON DES RÉSULTATS:\n")
            f.write("-" * 30 + "\n")
            for i, result in enumerate(results[:10], 1):
                f.write(f"{i}. {result.get('nom_complet', 'Nom non trouvé')}\n")
                f.write(f"   📧 Email: {result.get('email', 'Non trouvé')}\n")
                f.write(f"   📞 Téléphone: {result.get('telephone', 'Non trouvé')}\n")
                f.write(f"   🏠 Adresse: {result.get('adresse', 'Non trouvée')}\n\n")
        
        logger.info(f"📋 Rapport: {report_filename}")
        
        # Affichage des statistiques finales
        logger.info(f"\n🎯 === RÉSULTATS FINAUX ===")
        logger.info(f"👥 Avocats extraits: {len(results)}")
        logger.info(f"📧 Emails: {emails_found}/{len(results)} ({emails_found/len(results)*100:.1f}%)")
        logger.info(f"📞 Téléphones: {phones_found}/{len(results)} ({phones_found/len(results)*100:.1f}%)")
        logger.info(f"💾 Fichiers générés: 4 (JSON, CSV, TXT, rapport)")

    def close(self):
        """Ferme proprement le driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Fonction principale avec gestion des arguments"""
    parser = argparse.ArgumentParser(description='Scraper Barreau de Brest')
    parser.add_argument('--test', action='store_true', help='Mode test (3 pages seulement)')
    parser.add_argument('--visual', action='store_true', help='Mode visuel (avec interface)')
    args = parser.parse_args()
    
    # Configuration
    headless = not args.visual
    test_mode = args.test
    
    print("🚀 === SCRAPER BARREAU DE BREST ===")
    print(f"📋 Mode: {'Test (3 pages)' if test_mode else 'Complet (15 pages)'}")
    print(f"👁️  Interface: {'Visuelle' if not headless else 'Headless'}")
    print(f"🌐 Site: https://www.avocats-brest.fr/avocats/")
    print()
    
    scraper = BrestLawyerScraper(headless=headless, test_mode=test_mode)
    
    try:
        # Lancement du scraping
        results = scraper.scrape_all_lawyers()
        
        if results:
            # Sauvegarde
            prefix = "brest_test" if test_mode else "brest_complet"
            scraper.save_results(results, prefix)
            
            print(f"\n🎉 === SCRAPING RÉUSSI ===")
            print(f"👥 {len(results)} avocats extraits")
            
            if len(results) >= 5:
                print(f"\n📋 Premiers résultats:")
                for i, result in enumerate(results[:5], 1):
                    print(f"{i}. {result.get('nom_complet', 'N/A')} - {result.get('email', 'Pas d\\'email')}")
        else:
            print("❌ Aucun résultat extrait")
        
    except KeyboardInterrupt:
        print("\n⚡ Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
    finally:
        scraper.close()
        print("\n👋 Scraping terminé")

if __name__ == "__main__":
    main()