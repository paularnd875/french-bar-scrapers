#!/usr/bin/env python3
"""
Scraper PRODUCTION pour le Barreau d'Ain - Mode HEADLESS
Scrape TOUS les avocats du barreau d'Ain en mode invisible
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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'ain_production_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AinBarreauProductionScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.base_url = "https://www.bourg-avocats.com/annuaire-des-avocats"
        self.lawyers_data = []
        self.driver = None
        self.start_time = datetime.now()
        
    def setup_driver(self):
        """Configure le driver Chrome en mode production"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            logger.info("🔒 Mode headless activé - aucune fenêtre n'apparaîtra")
        
        # Options optimisées pour la production
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-images")  # Économie de bande passante
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(30)
        
        return self.driver
    
    def get_all_lawyers_with_links(self):
        """Récupère TOUS les avocats avec leurs liens détaillés"""
        lawyers_info = []
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.clickable-row[data-mid]")
            total_lawyers = len(rows)
            logger.info(f"🎯 TROUVÉ {total_lawyers} AVOCATS À EXTRAIRE")
            
            for i, row in enumerate(rows):
                try:
                    detail_link = row.get_attribute('data-mid')
                    if detail_link:
                        detail_url = f"https://www.bourg-avocats.com{detail_link}" if detail_link.startswith('/') else detail_link
                        
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        lawyer_basic = {
                            'nom_complet': cells[0].text.strip() if len(cells) > 0 else '',
                            'specialisations_tableau': cells[1].text.strip() if len(cells) > 1 else '',
                            'aide_juridictionnelle': cells[2].text.strip() if len(cells) > 2 else '',
                            'adresse_tableau': cells[3].text.strip() if len(cells) > 3 else '',
                            'detail_url': detail_url
                        }
                        
                        lawyers_info.append(lawyer_basic)
                        
                        # Log de progression tous les 20 avocats
                        if (i + 1) % 20 == 0:
                            logger.info(f"📋 Récupérés {i+1}/{total_lawyers} liens avocats")
                        
                except Exception as e:
                    logger.warning(f"Erreur avec la ligne {i+1}: {e}")
                    continue
            
            logger.info(f"✅ {len(lawyers_info)} avocats prêts pour l'extraction détaillée")
            return lawyers_info
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des avocats: {e}")
            return []
    
    def extract_detailed_info(self, basic_info, index, total):
        """Extrait les informations détaillées d'une fiche avocat"""
        detailed_info = {
            'prenom': '',
            'nom': '',
            'email': '',
            'telephone': '',
            'fax': '',
            'annee_inscription': '',
            'date_serment': '',
            'specialisations': basic_info['specialisations_tableau'],
            'structure': '',
            'adresse': basic_info['adresse_tableau'],
            'aide_juridictionnelle': basic_info['aide_juridictionnelle'],
            'langues': '',
            'url_fiche': basic_info['detail_url'],
            'nom_complet_tableau': basic_info['nom_complet'],
            'extraction_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Navigation vers la fiche
            self.driver.get(basic_info['detail_url'])
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)  # Pause courte mais respectueuse
            
            # Extraction du contenu
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            self.parse_lawyer_details(page_text, detailed_info)
            
            # Compléter le nom si nécessaire
            if not detailed_info['nom'] or not detailed_info['prenom']:
                self.parse_name_from_table(basic_info['nom_complet'], detailed_info)
            
            # Log de progression avec informations utiles
            progress_pct = (index + 1) / total * 100
            logger.info(f"✅ [{progress_pct:5.1f}%] {index+1:3d}/{total} - {detailed_info['nom']} {detailed_info['prenom']}")
            
            if detailed_info['email']:
                logger.info(f"   📧 {detailed_info['email']}")
                
            return detailed_info
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction {basic_info['nom_complet']}: {e}")
            self.parse_name_from_table(basic_info['nom_complet'], detailed_info)
            return detailed_info
    
    def parse_lawyer_details(self, page_text, lawyer_info):
        """Parse toutes les informations depuis le texte de la fiche"""
        
        # EMAIL
        email_match = re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', page_text)
        if email_match:
            lawyer_info['email'] = email_match.group().strip()
        
        # TÉLÉPHONES
        phone_patterns = [
            r'(0[1-9][0-9]{8})',
            r'(0[1-9](?:[0-9]{2}){4})'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, page_text)
            phones.extend(matches)
        
        if phones:
            lawyer_info['telephone'] = phones[0]
        if len(phones) > 1:
            lawyer_info['fax'] = phones[1]
        
        # ANNÉE D'INSCRIPTION
        serment_match = re.search(r'prêté serment le (\d{2})/(\d{2})/(\d{4})', page_text)
        if serment_match:
            day, month, year = serment_match.groups()
            lawyer_info['date_serment'] = f"{day}/{month}/{year}"
            lawyer_info['annee_inscription'] = year
        
        # NOM/PRÉNOM
        name_match = re.search(r'Maître\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][A-Z\s-]+)', page_text)
        if name_match:
            lawyer_info['prenom'] = name_match.group(1).strip()
            lawyer_info['nom'] = name_match.group(2).strip()
        
        # LANGUES
        langues_match = re.search(r'Langues parlées:\s*([^\n]+)', page_text)
        if langues_match:
            lawyer_info['langues'] = langues_match.group(1).strip()
        
        # AIDE JURIDICTIONNELLE
        aide_match = re.search(r'Aide juridictionnelle:\s*(OUI|NON)', page_text)
        if aide_match:
            lawyer_info['aide_juridictionnelle'] = aide_match.group(1)
        
        # COMPÉTENCES
        comp_match = re.search(r'Compétences:\s*([^\n]+)', page_text)
        if comp_match:
            competences = comp_match.group(1).strip()
            if len(competences) > len(lawyer_info['specialisations']):
                lawyer_info['specialisations'] = competences
        
        # STRUCTURE
        address_lines = page_text.split('\n')
        for i, line in enumerate(address_lines):
            if 'CHEMIN' in line or 'avenue' in line or 'rue' in line or 'place' in line:
                for j in range(max(0, i-3), i):
                    prev_line = address_lines[j].strip()
                    if any(word in prev_line.upper() for word in ['CABINET', 'SCP', 'SELARL', 'SOCIÉTÉ']):
                        lawyer_info['structure'] = prev_line
                        break
                break
    
    def parse_name_from_table(self, full_name, lawyer_info):
        """Parse nom/prénom depuis le tableau avec détection intelligente du format"""
        if not full_name or (lawyer_info['nom'] and lawyer_info['prenom']):
            return
        
        full_name = full_name.strip()
        
        # Analyser les mots pour déterminer lequel est le nom de famille
        words = full_name.split()
        if len(words) < 2:
            return
        
        # Heuristique: le nom de famille est généralement en majuscules
        # ou le mot qui semble être un nom de famille
        potential_lastname = None
        potential_firstname = None
        
        # Chercher le mot entièrement en majuscules (nom de famille)
        for i, word in enumerate(words):
            if word.isupper() and len(word) > 1:
                potential_lastname = word
                # Le reste est le prénom
                remaining_words = words[:i] + words[i+1:]
                potential_firstname = ' '.join(remaining_words)
                break
        
        # Si pas trouvé, utiliser l'heuristique: premier mot en majuscules = nom de famille
        if not potential_lastname:
            # Format "DUPONT Jean" ou "MARTIN Jean-Luc"
            if words[0].isupper():
                potential_lastname = words[0]
                potential_firstname = ' '.join(words[1:])
            # Format "Jean DUPONT" 
            elif words[-1].isupper():
                potential_lastname = words[-1]
                potential_firstname = ' '.join(words[:-1])
            else:
                # Fallback: dernier mot = nom
                potential_lastname = words[-1]
                potential_firstname = ' '.join(words[:-1])
        
        lawyer_info['nom'] = potential_lastname
        lawyer_info['prenom'] = potential_firstname
    
    def scrape_all_lawyers_production(self):
        """SCRAPING COMPLET PRODUCTION - TOUS LES AVOCATS"""
        try:
            logger.info("🚀 DÉBUT DU SCRAPING PRODUCTION BARREAU D'AIN")
            logger.info(f"⏰ Heure de début: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"🔒 Mode headless: {self.headless}")
            
            self.setup_driver()
            
            logger.info(f"🌐 Navigation vers: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Récupération de tous les liens
            lawyers_basic = self.get_all_lawyers_with_links()
            
            if not lawyers_basic:
                logger.error("❌ Aucun avocat trouvé")
                return
            
            total_lawyers = len(lawyers_basic)
            logger.info(f"🎯 DÉBUT EXTRACTION DÉTAILLÉE - {total_lawyers} AVOCATS")
            logger.info("=" * 60)
            
            # Extraction détaillée de chaque avocat
            for i, basic_info in enumerate(lawyers_basic):
                try:
                    detailed_info = self.extract_detailed_info(basic_info, i, total_lawyers)
                    self.lawyers_data.append(detailed_info)
                    
                    # Pause respectueuse entre requêtes
                    time.sleep(0.8)
                    
                    # Sauvegarde intermédiaire tous les 25 avocats
                    if (i + 1) % 25 == 0:
                        self.save_partial_results(i + 1, total_lawyers)
                        self.log_progress_stats(i + 1, total_lawyers)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur avec l'avocat {i+1}: {e}")
                    continue
            
            # Sauvegarde finale
            self.save_final_results()
            self.log_final_stats()
            
        except Exception as e:
            logger.error(f"💥 Erreur critique: {e}")
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔧 Driver fermé")
    
    def save_partial_results(self, count, total):
        """Sauvegarde intermédiaire sécurisée"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ain_partial_{count}_sur_{total}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Sauvegarde intermédiaire: {filename}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde intermédiaire: {e}")
    
    def save_final_results(self):
        """Sauvegarde finale complète"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON principal
        json_filename = f"ain_PRODUCTION_COMPLET_{timestamp}.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 JSON FINAL: {json_filename}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde JSON: {e}")
        
        # CSV principal
        if self.lawyers_data:
            csv_filename = f"ain_PRODUCTION_COMPLET_{timestamp}.csv"
            try:
                with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.lawyers_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.lawyers_data)
                logger.info(f"📊 CSV FINAL: {csv_filename}")
            except Exception as e:
                logger.error(f"Erreur sauvegarde CSV: {e}")
        
        # CSV emails uniquement
        lawyers_with_emails = [l for l in self.lawyers_data if l.get('email')]
        if lawyers_with_emails:
            email_csv_filename = f"ain_EMAILS_SEULEMENT_{timestamp}.csv"
            try:
                with open(email_csv_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=lawyers_with_emails[0].keys())
                    writer.writeheader()
                    writer.writerows(lawyers_with_emails)
                logger.info(f"📧 CSV EMAILS: {email_csv_filename}")
            except Exception as e:
                logger.error(f"Erreur sauvegarde CSV emails: {e}")
    
    def log_progress_stats(self, current, total):
        """Affiche les statistiques de progression"""
        if self.lawyers_data:
            emails = sum(1 for l in self.lawyers_data if l.get('email'))
            phones = sum(1 for l in self.lawyers_data if l.get('telephone'))
            
            elapsed = datetime.now() - self.start_time
            rate = current / elapsed.total_seconds() * 60  # avocats par minute
            eta_minutes = (total - current) / (rate if rate > 0 else 1)
            
            logger.info("📊 STATS INTERMÉDIAIRES:")
            logger.info(f"   👥 Traités: {current}/{total} ({current/total*100:.1f}%)")
            logger.info(f"   📧 Emails: {emails} ({emails/current*100:.1f}%)")
            logger.info(f"   📞 Téléphones: {phones} ({phones/current*100:.1f}%)")
            logger.info(f"   ⚡ Vitesse: {rate:.1f} avocats/min")
            logger.info(f"   ⏱️  ETA: {eta_minutes:.0f} minutes")
            logger.info("=" * 60)
    
    def log_final_stats(self):
        """Affiche les statistiques finales"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("")
        logger.info("🎉" * 20)
        logger.info("🏁 SCRAPING PRODUCTION TERMINÉ AVEC SUCCÈS!")
        logger.info("🎉" * 20)
        logger.info(f"⏰ Durée totale: {str(duration).split('.')[0]}")
        logger.info(f"📋 Avocats extraits: {len(self.lawyers_data)}")
        
        if self.lawyers_data:
            emails = sum(1 for l in self.lawyers_data if l.get('email'))
            phones = sum(1 for l in self.lawyers_data if l.get('telephone'))
            years = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
            specializations = sum(1 for l in self.lawyers_data if l.get('specialisations'))
            
            logger.info("")
            logger.info("📈 RÉSULTATS FINAUX:")
            logger.info(f"   📧 Emails: {emails} ({emails/len(self.lawyers_data)*100:.1f}%)")
            logger.info(f"   📞 Téléphones: {phones} ({phones/len(self.lawyers_data)*100:.1f}%)")
            logger.info(f"   📅 Années inscription: {years} ({years/len(self.lawyers_data)*100:.1f}%)")
            logger.info(f"   ⚖️  Spécialisations: {specializations} ({specializations/len(self.lawyers_data)*100:.1f}%)")
            
            logger.info("")
            logger.info("🥇 TOP 5 EMAILS EXTRAITS:")
            count = 0
            for lawyer in self.lawyers_data:
                if lawyer.get('email') and count < 5:
                    logger.info(f"   {count+1}. {lawyer['prenom']} {lawyer['nom']} - {lawyer['email']}")
                    count += 1
        
        logger.info("")
        logger.info("✅ MISSION ACCOMPLIE! Tous les fichiers sont sauvegardés.")

if __name__ == "__main__":
    print("🚀 LANCEMENT DU SCRAPER PRODUCTION BARREAU D'AIN")
    print("⚠️  ATTENTION: Ce script va scraper TOUS les avocats du barreau")
    print("💻 Aucune fenêtre ne s'ouvrira (mode headless)")
    print("✅ Démarrage automatique...")
    print()
    
    # Lancement automatique
    scraper = AinBarreauProductionScraper(headless=True)
    scraper.scrape_all_lawyers_production()