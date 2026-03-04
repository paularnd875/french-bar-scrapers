#!/usr/bin/env python3
"""
Scraper pour récupérer les informations des avocats du barreau de Grenoble
Site: https://ordre-grenoble.avocat.fr/recherche-avocats/
"""

import asyncio
import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import pandas as pd


# Configuration
BASE_URL = "https://ordre-grenoble.avocat.fr/recherche-avocats/"
OUTPUT_DIR = "scraped_data"
LAWYERS_LIST_CSV = "lawyers_list.csv"
LAWYERS_DETAILS_CSV = "lawyers_details.csv"
LOG_FILE = "scraping.log"
MAX_RETRIES = 3
MIN_DELAY = 2  # secondes
MAX_DELAY = 5  # secondes
TIMEOUT = 30000  # milliseconds


class GrenobleBarScraper:
    """Scraper pour le barreau de Grenoble"""
    
    def __init__(self):
        """Initialise le scraper"""
        self.setup_logging()
        self.setup_directories()
        self.lawyers_data = []
        self.lawyers_details = []
        self.browser = None
        self.page = None
        
    def setup_logging(self):
        """Configure le système de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(OUTPUT_DIR, LOG_FILE)),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Crée les répertoires nécessaires"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.logger.info(f"Répertoire de sortie: {OUTPUT_DIR}")
        
    async def random_delay(self):
        """Applique un délai aléatoire entre les requêtes"""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        self.logger.debug(f"Attente de {delay:.2f} secondes...")
        await asyncio.sleep(delay)
        
    async def setup_browser(self):
        """Initialise le navigateur Playwright"""
        self.logger.info("Initialisation du navigateur...")
        playwright = await async_playwright().start()
        
        # Configuration pour éviter la détection
        self.browser = await playwright.chromium.launch(
            headless=False,  # Mode visible pour debug
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Création du contexte avec user agent réaliste
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='fr-FR',
            timezone_id='Europe/Paris'
        )
        
        self.page = await context.new_page()
        
        # Injection de scripts pour masquer l'automatisation
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en-US', 'en']
            });
        """)
        
        self.logger.info("Navigateur initialisé avec succès")
        
    async def close_browser(self):
        """Ferme le navigateur"""
        if self.browser:
            await self.browser.close()
            self.logger.info("Navigateur fermé")
            
    async def get_locations(self) -> List[str]:
        """Récupère la liste des localisations disponibles"""
        self.logger.info("Récupération des localisations...")
        
        try:
            await self.page.goto(BASE_URL, wait_until='networkidle', timeout=TIMEOUT)
            await self.random_delay()
            
            # Chercher le sélecteur de localisation
            locations = []
            
            # Tentative 1: Menu déroulant
            select_elements = await self.page.query_selector_all('select')
            for select in select_elements:
                options = await select.query_selector_all('option')
                for option in options:
                    value = await option.get_attribute('value')
                    text = await option.text_content()
                    if value and text and text.strip() != "":
                        locations.append({
                            'value': value,
                            'text': text.strip()
                        })
                        
            # Tentative 2: Checkboxes ou radio buttons
            if not locations:
                inputs = await self.page.query_selector_all('input[type="checkbox"], input[type="radio"]')
                for input_elem in inputs:
                    label = await self.page.query_selector(f'label[for="{await input_elem.get_attribute("id")}"]')
                    if label:
                        text = await label.text_content()
                        value = await input_elem.get_attribute('value')
                        if value and text:
                            locations.append({
                                'value': value,
                                'text': text.strip()
                            })
                            
            # Tentative 3: Liste de liens
            if not locations:
                links = await self.page.query_selector_all('a[href*="localisation"], a[href*="ville"], a[href*="location"]')
                for link in links:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if href and text:
                        locations.append({
                            'value': href,
                            'text': text.strip()
                        })
                        
            self.logger.info(f"Nombre de localisations trouvées: {len(locations)}")
            return locations
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des localisations: {e}")
            return []
            
    async def scrape_lawyers_list_for_location(self, location: Optional[Dict] = None) -> List[Dict]:
        """Scrape la liste des avocats pour une localisation donnée"""
        lawyers = []
        page_num = 1
        
        location_name = location['text'] if location else "Toutes"
        self.logger.info(f"Scraping des avocats pour la localisation: {location_name}")
        
        try:
            # Si une localisation est spécifiée, la sélectionner
            if location:
                # Essayer différentes méthodes de sélection
                try:
                    # Menu déroulant
                    await self.page.select_option('select', value=location['value'])
                except:
                    try:
                        # Checkbox ou radio
                        await self.page.click(f'input[value="{location["value"]}"]')
                    except:
                        try:
                            # Lien
                            await self.page.goto(location['value'], wait_until='networkidle')
                        except:
                            self.logger.warning(f"Impossible de sélectionner la localisation {location_name}")
                            
                await self.random_delay()
                
            while True:
                self.logger.info(f"Scraping page {page_num} pour {location_name}...")
                
                # Attendre le chargement des résultats
                await self.page.wait_for_selector('body', state='visible', timeout=10000)
                
                # Extraire les avocats de la page actuelle
                page_lawyers = await self.extract_lawyers_from_page()
                
                if not page_lawyers:
                    self.logger.info(f"Aucun avocat trouvé sur la page {page_num}")
                    break
                    
                # Ajouter la localisation aux données
                for lawyer in page_lawyers:
                    lawyer['localisation'] = location_name
                    lawyer['page_number'] = page_num
                    
                lawyers.extend(page_lawyers)
                self.logger.info(f"Page {page_num}: {len(page_lawyers)} avocats trouvés")
                
                # Chercher le bouton "Suivant" ou pagination
                has_next = await self.go_to_next_page()
                
                if not has_next:
                    self.logger.info(f"Fin de la pagination pour {location_name}")
                    break
                    
                page_num += 1
                await self.random_delay()
                
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping de la localisation {location_name}: {e}")
            
        return lawyers
        
    async def extract_lawyers_from_page(self) -> List[Dict]:
        """Extrait les informations des avocats de la page actuelle"""
        lawyers = []
        
        try:
            # Obtenir le HTML de la page
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Stratégies pour trouver les avocats
            strategies = [
                # Stratégie 1: Divs avec classe spécifique
                (soup.find_all('div', class_=re.compile(r'avocat|lawyer|result|card|profile', re.I)), 'div'),
                # Stratégie 2: Articles
                (soup.find_all('article'), 'article'),
                # Stratégie 3: Listes
                (soup.find_all('li', class_=re.compile(r'avocat|lawyer|result', re.I)), 'li'),
                # Stratégie 4: Sections
                (soup.find_all('section', class_=re.compile(r'avocat|lawyer|result', re.I)), 'section'),
            ]
            
            for elements, tag_type in strategies:
                if elements:
                    self.logger.debug(f"Utilisation de la stratégie: {tag_type} ({len(elements)} éléments)")
                    
                    for elem in elements:
                        lawyer_info = await self.extract_lawyer_info(elem)
                        if lawyer_info and lawyer_info.get('name'):
                            lawyers.append(lawyer_info)
                            
                    if lawyers:
                        break
                        
            # Si aucune stratégie n'a fonctionné, chercher tous les liens
            if not lawyers:
                links = soup.find_all('a', href=True)
                for link in links:
                    if any(keyword in link['href'].lower() for keyword in ['avocat', 'lawyer', 'profil', 'fiche']):
                        name = link.get_text(strip=True)
                        if name and len(name) > 3 and not name.startswith('http'):
                            lawyers.append({
                                'name': name,
                                'profile_url': urljoin(BASE_URL, link['href']),
                                'extraction_time': datetime.now().isoformat()
                            })
                            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des avocats: {e}")
            
        return lawyers
        
    async def extract_lawyer_info(self, element) -> Dict:
        """Extrait les informations d'un avocat depuis un élément HTML"""
        info = {}
        
        try:
            # Chercher le nom
            name_patterns = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'b', '.name', '.nom']
            for pattern in name_patterns:
                name_elem = element.find(pattern)
                if name_elem:
                    info['name'] = name_elem.get_text(strip=True)
                    break
                    
            # Si pas de nom dans les titres, chercher dans les liens
            if not info.get('name'):
                link = element.find('a')
                if link and link.get_text(strip=True):
                    info['name'] = link.get_text(strip=True)
                    
            # Chercher le lien vers le profil
            profile_link = element.find('a', href=True)
            if profile_link:
                info['profile_url'] = urljoin(BASE_URL, profile_link['href'])
                
            # Extraire d'autres informations visibles
            # Téléphone
            phone_patterns = [r'\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}', r'\+33.*\d{9}']
            text_content = element.get_text()
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text_content)
                if phone_match:
                    info['phone'] = phone_match.group()
                    break
                    
            # Email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_match = re.search(email_pattern, text_content)
            if email_match:
                info['email'] = email_match.group()
                
            # Adresse
            address_elem = element.find(class_=re.compile(r'address|adresse', re.I))
            if address_elem:
                info['address'] = address_elem.get_text(strip=True)
                
            # Spécialisation
            spec_elem = element.find(class_=re.compile(r'special|competence|expertise', re.I))
            if spec_elem:
                info['specialization'] = spec_elem.get_text(strip=True)
                
            # Timestamp
            info['extraction_time'] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.debug(f"Erreur lors de l'extraction des infos: {e}")
            
        return info
        
    async def go_to_next_page(self) -> bool:
        """Navigue vers la page suivante"""
        try:
            # Stratégies pour trouver le bouton suivant
            next_selectors = [
                'a:has-text("Suivant")',
                'a:has-text("Next")',
                'button:has-text("Suivant")',
                'button:has-text("Next")',
                'a.next',
                'a.suivant',
                '.pagination a:last-child',
                'a[aria-label*="suivant" i]',
                'a[aria-label*="next" i]',
            ]
            
            for selector in next_selectors:
                try:
                    next_button = await self.page.query_selector(selector)
                    if next_button:
                        is_disabled = await next_button.get_attribute('disabled')
                        if not is_disabled:
                            await next_button.click()
                            await self.page.wait_for_load_state('networkidle')
                            return True
                except:
                    continue
                    
            # Vérifier la pagination numérotée
            current_page = await self.page.query_selector('.pagination .active, .pagination .current')
            if current_page:
                current_text = await current_page.text_content()
                try:
                    current_num = int(re.search(r'\d+', current_text).group())
                    next_num = current_num + 1
                    next_page_link = await self.page.query_selector(f'a:has-text("{next_num}")')
                    if next_page_link:
                        await next_page_link.click()
                        await self.page.wait_for_load_state('networkidle')
                        return True
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Erreur lors de la navigation: {e}")
            
        return False
        
    async def scrape_lawyer_details(self, lawyer: Dict) -> Dict:
        """Scrape les détails complets d'un avocat"""
        details = lawyer.copy()
        
        if not lawyer.get('profile_url'):
            self.logger.warning(f"Pas d'URL de profil pour {lawyer.get('name', 'Inconnu')}")
            return details
            
        self.logger.info(f"Scraping des détails pour: {lawyer.get('name', 'Inconnu')}")
        
        for attempt in range(MAX_RETRIES):
            try:
                await self.page.goto(lawyer['profile_url'], wait_until='networkidle', timeout=TIMEOUT)
                await self.random_delay()
                
                content = await self.page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extraction du nom complet
                name_selectors = ['h1', '.lawyer-name', '.nom-avocat', '#name']
                for selector in name_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        details['full_name'] = elem.get_text(strip=True)
                        break
                        
                # Extraction du cabinet
                cabinet_patterns = ['cabinet', 'firm', 'office']
                for pattern in cabinet_patterns:
                    elem = soup.find(text=re.compile(pattern, re.I))
                    if elem and elem.parent:
                        details['cabinet'] = elem.parent.get_text(strip=True)
                        break
                        
                # Extraction de l'adresse complète
                address_selectors = ['.address', '.adresse', 'address']
                for selector in address_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        details['full_address'] = elem.get_text(strip=True)
                        break
                        
                # Extraction du téléphone
                phone_patterns = [
                    r'(?:Tél|Tel|Téléphone|Phone)[:\s]*([0-9\s.-]+)',
                    r'\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}[\s.-]\d{2}'
                ]
                for pattern in phone_patterns:
                    match = re.search(pattern, soup.get_text(), re.I)
                    if match:
                        details['phone'] = match.group(1) if match.groups() else match.group()
                        break
                        
                # Extraction du fax
                fax_pattern = r'(?:Fax)[:\s]*([0-9\s.-]+)'
                fax_match = re.search(fax_pattern, soup.get_text(), re.I)
                if fax_match:
                    details['fax'] = fax_match.group(1)
                    
                # Extraction de l'email
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, soup.get_text())
                if emails:
                    details['email'] = emails[0]
                    
                # Extraction du site web
                website_elem = soup.find('a', href=re.compile(r'^https?://(?!.*avocat\.fr)'))
                if website_elem:
                    details['website'] = website_elem['href']
                    
                # Extraction des spécialisations
                spec_selectors = ['.specialization', '.competences', '.expertise']
                specializations = []
                for selector in spec_selectors:
                    elems = soup.select(selector)
                    for elem in elems:
                        spec_text = elem.get_text(strip=True)
                        if spec_text:
                            specializations.append(spec_text)
                            
                if specializations:
                    details['specializations'] = ' | '.join(specializations)
                    
                # Extraction des langues
                lang_pattern = r'(?:Langues?|Languages?)[:\s]*([^\.]+)'
                lang_match = re.search(lang_pattern, soup.get_text(), re.I)
                if lang_match:
                    details['languages'] = lang_match.group(1).strip()
                    
                # Extraction de la date d'inscription
                date_pattern = r'(?:Inscri[pt]|Serment|Prestation)[:\s]*(\d{2}/\d{2}/\d{4}|\d{4})'
                date_match = re.search(date_pattern, soup.get_text(), re.I)
                if date_match:
                    details['registration_date'] = date_match.group(1)
                    
                # Extraction des formations
                formation_selectors = ['.formation', '.education', '.diplome']
                formations = []
                for selector in formation_selectors:
                    elems = soup.select(selector)
                    for elem in elems:
                        form_text = elem.get_text(strip=True)
                        if form_text:
                            formations.append(form_text)
                            
                if formations:
                    details['formations'] = ' | '.join(formations)
                    
                # Extraction des honoraires
                honor_pattern = r'(?:Honoraires?|Tarifs?|Fees?)[:\s]*([^\.]+)'
                honor_match = re.search(honor_pattern, soup.get_text(), re.I)
                if honor_match:
                    details['honoraires'] = honor_match.group(1).strip()
                    
                # Timestamp de scraping
                details['detail_extraction_time'] = datetime.now().isoformat()
                
                self.logger.info(f"Détails extraits avec succès pour {lawyer.get('name', 'Inconnu')}")
                return details
                
            except Exception as e:
                self.logger.error(f"Erreur lors du scraping des détails (tentative {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(5)
                    
        return details
        
    def save_to_csv(self, data: List[Dict], filename: str):
        """Sauvegarde les données dans un fichier CSV"""
        if not data:
            self.logger.warning(f"Aucune donnée à sauvegarder dans {filename}")
            return
            
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        try:
            df = pd.DataFrame(data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            self.logger.info(f"Données sauvegardées dans {filepath} ({len(data)} entrées)")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde CSV: {e}")
            # Fallback avec csv standard
            try:
                keys = data[0].keys()
                with open(filepath, 'w', newline='', encoding='utf-8-sig') as output_file:
                    dict_writer = csv.DictWriter(output_file, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(data)
                self.logger.info(f"Données sauvegardées avec csv standard dans {filepath}")
            except Exception as e2:
                self.logger.error(f"Erreur critique lors de la sauvegarde: {e2}")
                
    def save_checkpoint(self, data: List[Dict], checkpoint_name: str):
        """Sauvegarde un checkpoint pour reprendre en cas d'erreur"""
        checkpoint_file = os.path.join(OUTPUT_DIR, f"checkpoint_{checkpoint_name}.json")
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Checkpoint sauvegardé: {checkpoint_file}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du checkpoint: {e}")
            
    async def run(self):
        """Exécution principale du scraper"""
        start_time = time.time()
        self.logger.info("=" * 50)
        self.logger.info("Démarrage du scraping du barreau de Grenoble")
        self.logger.info("=" * 50)
        
        try:
            await self.setup_browser()
            
            # Phase 1: Récupération de la liste des avocats
            self.logger.info("\n### PHASE 1: Extraction de la liste des avocats ###\n")
            
            # Aller à la page principale
            await self.page.goto(BASE_URL, wait_until='networkidle', timeout=TIMEOUT)
            await self.random_delay()
            
            # Obtenir les localisations
            locations = await self.get_locations()
            
            if locations:
                self.logger.info(f"Scraping de {len(locations)} localisations...")
                for i, location in enumerate(locations, 1):
                    self.logger.info(f"\n--- Localisation {i}/{len(locations)}: {location['text']} ---")
                    lawyers = await self.scrape_lawyers_list_for_location(location)
                    self.lawyers_data.extend(lawyers)
                    
                    # Sauvegarde intermédiaire
                    if i % 5 == 0:
                        self.save_checkpoint(self.lawyers_data, f"lawyers_list_{i}")
            else:
                # Scraper sans sélection de localisation
                self.logger.info("Pas de localisations trouvées, scraping global...")
                lawyers = await self.scrape_lawyers_list_for_location(None)
                self.lawyers_data.extend(lawyers)
                
            # Supprimer les doublons basés sur l'URL du profil
            unique_lawyers = {}
            for lawyer in self.lawyers_data:
                url = lawyer.get('profile_url', lawyer.get('name', ''))
                if url not in unique_lawyers:
                    unique_lawyers[url] = lawyer
                    
            self.lawyers_data = list(unique_lawyers.values())
            
            # Sauvegarder la liste des avocats
            self.save_to_csv(self.lawyers_data, LAWYERS_LIST_CSV)
            self.logger.info(f"\nTotal d'avocats uniques trouvés: {len(self.lawyers_data)}")
            
            # Phase 2: Extraction des détails
            if self.lawyers_data:
                self.logger.info("\n### PHASE 2: Extraction des fiches détaillées ###\n")
                
                for i, lawyer in enumerate(self.lawyers_data, 1):
                    self.logger.info(f"\nTraitement {i}/{len(self.lawyers_data)}: {lawyer.get('name', 'Inconnu')}")
                    
                    lawyer_details = await self.scrape_lawyer_details(lawyer)
                    self.lawyers_details.append(lawyer_details)
                    
                    # Sauvegarde intermédiaire tous les 10 avocats
                    if i % 10 == 0:
                        self.save_to_csv(self.lawyers_details, f"lawyers_details_partial_{i}.csv")
                        self.save_checkpoint(self.lawyers_details, f"details_{i}")
                        
                    # Pause plus longue tous les 20 avocats
                    if i % 20 == 0:
                        self.logger.info("Pause longue pour éviter la détection...")
                        await asyncio.sleep(10)
                        
                # Sauvegarder les détails finaux
                self.save_to_csv(self.lawyers_details, LAWYERS_DETAILS_CSV)
                
        except Exception as e:
            self.logger.error(f"Erreur fatale: {e}")
            # Sauvegarder les données collectées jusqu'à présent
            if self.lawyers_data:
                self.save_to_csv(self.lawyers_data, f"lawyers_list_emergency_{int(time.time())}.csv")
            if self.lawyers_details:
                self.save_to_csv(self.lawyers_details, f"lawyers_details_emergency_{int(time.time())}.csv")
                
        finally:
            await self.close_browser()
            
        # Rapport final
        elapsed_time = time.time() - start_time
        self.logger.info("\n" + "=" * 50)
        self.logger.info("RAPPORT FINAL")
        self.logger.info("=" * 50)
        self.logger.info(f"Temps total: {elapsed_time/60:.2f} minutes")
        self.logger.info(f"Avocats trouvés: {len(self.lawyers_data)}")
        self.logger.info(f"Détails extraits: {len(self.lawyers_details)}")
        self.logger.info(f"Fichiers de sortie:")
        self.logger.info(f"  - Liste: {os.path.join(OUTPUT_DIR, LAWYERS_LIST_CSV)}")
        self.logger.info(f"  - Détails: {os.path.join(OUTPUT_DIR, LAWYERS_DETAILS_CSV)}")
        self.logger.info(f"  - Logs: {os.path.join(OUTPUT_DIR, LOG_FILE)}")
        

async def main():
    """Point d'entrée principal"""
    scraper = GrenobleBarScraper()
    await scraper.run()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SCRAPER DU BARREAU DE GRENOBLE")
    print("="*60 + "\n")
    print("Ce script va extraire les informations des avocats depuis:")
    print(f"  {BASE_URL}")
    print("\nLes données seront sauvegardées dans le dossier:", OUTPUT_DIR)
    print("\nAppuyez sur Ctrl+C pour interrompre le processus à tout moment.")
    print("Les données déjà collectées seront sauvegardées.\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProcessus interrompu par l'utilisateur.")
        print("Les données partielles ont été sauvegardées.")
    except Exception as e:
        print(f"\n\nErreur inattendue: {e}")
        print("Consultez les logs pour plus de détails.")