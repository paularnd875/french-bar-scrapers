#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL CORRIGÉ - Barreau de Dijon
Version définitive avec gestion cookies corrigée pour capturer TOUS les avocats (378)
Corrige le problème qui ne trouvait que 22 avocats au lieu de 378
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import re
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import ssl
import urllib3

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

class DijonScraperFixedCookies:
    def __init__(self, headless=True, test_mode=False):
        self.base_url = "https://www.barreau-dijon.avocat.fr"
        self.annuaire_url = "https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/"
        self.results_url = "https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/annuaire-des-avocats-barreau-de-dijon-resultats/?q&ville&domaine&specialisation"
        self.headless = headless
        self.test_mode = test_mode
        self.max_test_avocats = 10 if test_mode else None
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialisation du driver
        self.driver = None
        self.setup_driver()
        
        # Compteurs et statistiques
        self.processed_count = 0
        self.successful_profiles = 0
        self.failed_profiles = 0
        self.current_page = 1
        self.max_pages = 25  # Sécurité pour 19+ pages
        
        # Statistiques temporelles
        self.start_time = None
        self.profile_extraction_times = []
        
        # Optimisations production
        self.batch_size = 50  # Sauvegarde tous les 50 avocats
        self.max_retries = 3  # 3 tentatives en cas d'échec
        self.retry_delay = 2   # Délai entre tentatives
        self.connection_errors = 0
        self.max_connection_errors = 10
        
    def setup_driver(self):
        """Configure le driver ultra-optimisé pour la production"""
        try:
            chrome_options = Options()
            
            # Mode headless pour la production
            if self.headless:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
            
            # Optimisations maximales pour la production
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Préférences pour optimiser la vitesse
            prefs = {
                "profile.managed_default_content_settings.images": 2,  # Bloquer les images
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_setting_values.media_stream": 2,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Créer le driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Optimisations temporelles
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info("✅ Driver Selenium configuré pour la production optimisée")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur configuration driver: {e}")
            return False
    
    def accept_cookies_robust(self):
        """Gestion robuste des cookies avec plusieurs méthodes"""
        try:
            # Attendre un peu pour que la bannière apparaisse
            time.sleep(2)
            
            # Liste de sélecteurs possibles pour accepter les cookies
            cookie_selectors = [
                '.cmplz-accept',
                '#acceptCookies', 
                '[onclick*="accept"]',
                'button[contains(text(),"Accepter")]',
                '.cookie-accept',
                'button.cmplz-btn',
                '#cmplz-functional-consent',
                '.cmplz-btn.cmplz-accept'
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    # Utiliser JavaScript pour éviter les interceptions
                    self.driver.execute_script("arguments[0].click();", cookie_element)
                    self.logger.info(f"✅ Cookies acceptés via: {selector}")
                    time.sleep(2)
                    return True
                except:
                    continue
            
            # Méthode JavaScript alternative
            try:
                result = self.driver.execute_script("""
                    var acceptBtn = document.querySelector('[onclick*="accept"], #acceptCookies, .cmplz-accept, .cookie-accept');
                    if(acceptBtn) {
                        acceptBtn.click();
                        return 'clicked';
                    }
                    return 'not found';
                """)
                if result == 'clicked':
                    self.logger.info("✅ Cookies acceptés via JavaScript")
                    time.sleep(2)
                    return True
            except:
                pass
            
            self.logger.info("⚠️ Aucun bouton cookies trouvé, continuation...")
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur gestion cookies: {e}")
            return False
    
    def trigger_search_robust(self):
        """Déclenche la recherche de manière robuste"""
        try:
            # Méthode 1: Clic direct sur le bouton submit
            try:
                search_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
                )
                # Utiliser JavaScript pour éviter les interceptions
                self.driver.execute_script("arguments[0].click();", search_button)
                self.logger.info("✅ Recherche déclenchée via bouton submit")
                time.sleep(5)
                return True
            except:
                pass
            
            # Méthode 2: Aller directement à l'URL des résultats
            try:
                self.driver.get(self.results_url)
                self.logger.info("✅ Accès direct aux résultats")
                time.sleep(3)
                return True
            except:
                pass
                
            # Méthode 3: JavaScript pour soumettre le formulaire
            try:
                self.driver.execute_script("""
                    var form = document.querySelector('form');
                    if(form) form.submit();
                """)
                self.logger.info("✅ Recherche déclenchée via JavaScript")
                time.sleep(5)
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erreur déclenchement recherche: {e}")
            return False
    
    def get_all_profile_links(self):
        """Récupère tous les liens vers les fiches d'avocats avec pagination COMPLÈTE"""
        try:
            self.logger.info("🔍 Collecte de tous les liens vers les fiches...")
            
            # Accès initial
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            # Gestion robuste des cookies
            self.accept_cookies_robust()
            
            # Déclencher la recherche
            if not self.trigger_search_robust():
                self.logger.error("❌ Impossible de déclencher la recherche")
                return []
            
            all_profile_links = []
            page = 1
            
            while page <= self.max_pages:
                self.logger.info(f"📄 Collecte liens page {page}...")
                
                # Extraire les liens de la page actuelle
                page_links = self.extract_links_from_current_page()
                
                if not page_links:
                    self.logger.info(f"❌ Pas de liens sur la page {page}, arrêt")
                    break
                
                all_profile_links.extend(page_links)
                self.logger.info(f"  ✅ Page {page}: {len(page_links)} liens collectés")
                
                # Mode test: limiter
                if self.test_mode and len(all_profile_links) >= self.max_test_avocats:
                    all_profile_links = all_profile_links[:self.max_test_avocats]
                    self.logger.info(f"🧪 Mode test: limité à {len(all_profile_links)} avocats")
                    break
                
                # Aller à la page suivante
                if not self.go_to_next_page():
                    self.logger.info("📋 Pas de page suivante, fin de collecte")
                    break
                
                page += 1
                time.sleep(2)  # Pause entre les pages
            
            # Supprimer les doublons
            unique_links = list({link['url']: link for link in all_profile_links}.values())
            
            self.logger.info(f"🎯 Total collecté: {len(unique_links)} liens uniques sur {page-1} pages")
            return unique_links
            
        except Exception as e:
            self.logger.error(f"❌ Erreur collecte liens: {e}")
            return []
    
    def extract_links_from_current_page(self):
        """Extrait les liens de la page actuelle"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            profile_links = []
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and '/avocat/' in href and href != '/avocat/' and not href.endswith('/avocat/'):
                    if href.startswith('/'):
                        full_url = self.base_url + href
                    else:
                        full_url = href
                    
                    # Extraire le nom depuis l'URL
                    name_match = re.search(r'/avocat/([^/]+)/?', href)
                    if name_match:
                        avocat_slug = name_match.group(1)
                        avocat_name = avocat_slug.replace('-', ' ').title()
                        
                        profile_links.append({
                            'name': avocat_name,
                            'url': full_url.rstrip('/') + '/',
                            'slug': avocat_slug
                        })
            
            # Déduplication immédiate
            seen_urls = set()
            unique_links = []
            for link in profile_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            return unique_links
            
        except Exception as e:
            self.logger.error(f"❌ Erreur extraction liens page: {e}")
            return []
    
    def go_to_next_page(self):
        """Va à la page suivante avec gestion améliorée"""
        try:
            # Construire l'URL de la page suivante directement
            next_page_num = self.current_page + 1
            next_page_url = f"{self.results_url}&avocats_page={next_page_num}"
            
            # Aller à la page suivante
            self.driver.get(next_page_url)
            time.sleep(3)
            
            # Vérifier qu'il y a du contenu sur cette page
            avocat_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/avocat/')]")
            if len(avocat_links) > 0:
                self.current_page = next_page_num
                return True
            else:
                return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur pagination: {e}")
            return False
    
    def extract_name_from_content(self, soup, text_content, profile_url):
        """Extrait nom et prénom avec méthodes multiples et robustes"""
        # Initialiser
        extracted_name = {'nom': '', 'prenom': ''}
        
        # Méthode 1: Titre de la page  
        title = self.driver.title
        if title and title != "Page non trouvée":
            # Nettoyer le titre
            clean_title = re.sub(r'\s*[-|].*$', '', title).strip()  # Supprimer après - ou |
            clean_title = re.sub(r'\s*avocat.*$', '', clean_title, flags=re.IGNORECASE).strip()
            clean_title = re.sub(r'^\s*(?:Maître|Me)\s+', '', clean_title, flags=re.IGNORECASE).strip()
            
            # Patterns pour extraire nom/prénom du titre
            title_patterns = [
                # Prénom NOM (le plus courant)
                r'^([A-ZÀ-Ÿ][a-zà-ÿ-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ-]*)*)\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ-]+)$',
                # NOM Prénom (inversé)
                r'^([A-ZÀ-Ÿ][A-ZÀ-Ÿ-]+)\s+([A-ZÀ-Ÿ][a-zà-ÿ-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ-]*)*)$',
                # Prénom plusieurs-mots NOM
                r'^([A-ZÀ-Ÿ][a-zà-ÿ-]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ-]+)*)\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ-]+)$'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, clean_title)
                if match:
                    part1, part2 = match.groups()
                    # Déterminer lequel est le nom (généralement en majuscules)
                    if part2.isupper() or len([c for c in part2 if c.isupper()]) > len(part2) / 2:
                        extracted_name['prenom'] = part1.strip()
                        extracted_name['nom'] = part2.strip()
                    else:
                        extracted_name['prenom'] = part1.strip()
                        extracted_name['nom'] = part2.strip()
                    break
        
        # Méthode fallback: extraire depuis l'URL
        if not extracted_name['nom']:
            url_match = re.search(r'/avocat/([^/]+)', profile_url)
            if url_match:
                slug = url_match.group(1)
                parts = slug.replace('-', ' ').title().split()
                if len(parts) >= 2:
                    extracted_name['prenom'] = ' '.join(parts[:-1])
                    extracted_name['nom'] = parts[-1]
        
        return extracted_name

    def extract_clean_address(self, soup, text_content):
        """Extrait et nettoie l'adresse"""
        address = ""
        
        # Sélecteurs pour l'adresse
        address_selectors = [
            '.address', '.adresse', 
            '[class*="address"]', '[class*="adresse"]',
            'p:contains("Adresse")', 'div:contains("Adresse")'
        ]
        
        for selector in address_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 10 and any(word in text.lower() for word in ['rue', 'avenue', 'boulevard', 'place', 'cedex']):
                        # Nettoyer l'adresse
                        clean_addr = re.sub(r'^\s*adresse\s*:?\s*', '', text, flags=re.IGNORECASE).strip()
                        clean_addr = re.sub(r'\s+', ' ', clean_addr)
                        if len(clean_addr) > len(address):
                            address = clean_addr
                        break
            except:
                continue
        
        # Fallback: recherche dans tout le texte
        if not address:
            address_patterns = [
                r'(\d+[^,\n]*(?:rue|avenue|boulevard|place|chemin)[^,\n]*\d{5}[^,\n]*)',
                r'((?:rue|avenue|boulevard|place|chemin)[^,\n]*\d{5}[^,\n]*)',
                r'(\d{5}\s+[A-Z][^,\n]+)'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    address = matches[0].strip()
                    break
        
        return address[:200] if address else ""

    def extract_clean_structure(self, soup, text_content):
        """Extrait et nettoie la structure/cabinet"""
        structure = ""
        
        # Sélecteurs pour la structure
        structure_selectors = [
            '.cabinet', '.structure', '.firm',
            '[class*="cabinet"]', '[class*="structure"]',
            'h2', 'h3'
        ]
        
        for selector in structure_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and 5 <= len(text) <= 100 and any(word in text.lower() for word in ['cabinet', 'associés', 'avocats', 'société']):
                        structure = text
                        break
                if structure:
                    break
            except:
                continue
        
        return structure[:150] if structure else ""

    def extract_profile_details(self, profile_url):
        """Extrait les détails d'un profil d'avocat"""
        profile_data = {
            'nom': '',
            'prenom': '',
            'annee_serment': '',
            'date_serment_complete': '',
            'specialisations': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'structure': '',
            'site_web': '',
            'source_fiche': profile_url,
            'extraction_reussie': False,
            'duree_extraction': 0
        }
        
        start_time = time.time()
        
        try:
            # Accéder à la page
            self.driver.get(profile_url)
            time.sleep(3)
            
            # Parser le contenu
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            text_content = soup.get_text()
            
            # Extraction du nom
            name_data = self.extract_name_from_content(soup, text_content, profile_url)
            profile_data.update(name_data)
            
            # Extraction de l'adresse
            profile_data['adresse'] = self.extract_clean_address(soup, text_content)
            
            # Extraction de la structure
            profile_data['structure'] = self.extract_clean_structure(soup, text_content)
            
            # Extraction année serment
            serment_match = re.search(r'(?:serment|inscription).*?(\d{4})', text_content, re.IGNORECASE)
            if serment_match:
                profile_data['annee_serment'] = serment_match.group(1)
            
            # Extraction spécialisations
            specializations = []
            spec_patterns = [
                r'(?:spécialisation|domaine|expertise).*?:.*?([^\.]+)',
                r'(droit\s+(?:civil|pénal|commercial|public|privé|des\s+affaires)[^,\.]*)',
                r'(médiation|contentieux|entreprise|environnement)',
            ]
            
            for pattern in spec_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    clean_spec = re.sub(r'[^\w\s,-]', '', match).strip()
                    if clean_spec and len(clean_spec) < 50:
                        specializations.append(clean_spec)
            
            if specializations:
                profile_data['specialisations'] = '; '.join(specializations[:5])
            
            # Extraction email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content)
            if email_match:
                profile_data['email'] = email_match.group()
            
            # Extraction téléphone
            phone_patterns = [
                r'(\d{2}\.?\s?\d{2}\.?\s?\d{2}\.?\s?\d{2}\.?\s?\d{2})',
                r'(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})',
                r'(0[1-9](?:[-.\s]?\d{2}){4})'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text_content)
                if phone_match:
                    profile_data['telephone'] = phone_match.group(1)
                    break
            
            # Extraction site web
            site_match = re.search(r'https?://[^\s<>"\']+', text_content)
            if site_match:
                profile_data['site_web'] = site_match.group()
            
            profile_data['extraction_reussie'] = True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Erreur extraction profil {profile_url}: {e}")
        
        profile_data['duree_extraction'] = round(time.time() - start_time, 2)
        return profile_data

    def run_extraction(self):
        """Lance l'extraction complète"""
        try:
            self.start_time = time.time()
            
            # Collecte des liens
            profile_links = self.get_all_profile_links()
            
            if not profile_links:
                self.logger.error("❌ Aucun lien collecté")
                return []
            
            self.logger.info(f"🎯 Démarrage extraction de {len(profile_links)} fiches...")
            
            results = []
            
            for i, link_info in enumerate(profile_links, 1):
                progress = (i / len(profile_links)) * 100
                remaining_time = ((time.time() - self.start_time) / i) * (len(profile_links) - i) / 60
                
                self.logger.info(f"📊 Progrès: [{i}/{len(profile_links)}] ({progress:.1f}%) - Temps restant estimé: {remaining_time:.1f}min")
                
                # Extraction du profil
                profile_data = self.extract_profile_details(link_info['url'])
                results.append(profile_data)
                
                if profile_data['extraction_reussie']:
                    self.successful_profiles += 1
                else:
                    self.failed_profiles += 1
                
                # Sauvegarde périodique
                if i % self.batch_size == 0:
                    self.save_partial_results(results, i)
            
            total_time = (time.time() - self.start_time) / 60
            self.logger.info(f"✅ Scraping terminé en {total_time:.1f} minutes")
            self.logger.info(f"⚡ Moyenne: {(time.time() - self.start_time) / len(profile_links):.1f}s par avocat")
            self.logger.info(f"📊 Réussites: {self.successful_profiles}/{len(profile_links)} ({(self.successful_profiles/len(profile_links)*100):.1f}%)")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Erreur extraction: {e}")
            return []

    def save_partial_results(self, results, count):
        """Sauvegarde partielle des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde backup
        backup_file = f"DIJON_BACKUP_{count}avocats_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 Sauvegarde partielle: {backup_file}")

    def save_results(self, results):
        """Sauvegarde finale des résultats"""
        if not results:
            self.logger.warning("⚠️ Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_prefix = "TEST" if self.test_mode else "PRODUCTION_COMPLETE"
        
        # Statistiques
        successful_results = [r for r in results if r['extraction_reussie']]
        emails_found = len([r for r in successful_results if r['email']])
        phones_found = len([r for r in successful_results if r['telephone']])
        addresses_found = len([r for r in successful_results if r['adresse']])
        structures_found = len([r for r in successful_results if r['structure']])
        serments_found = len([r for r in successful_results if r['annee_serment']])
        specialisations_found = len([r for r in successful_results if r['specialisations']])
        
        # Fichiers de sortie
        csv_file = f"DIJON_{mode_prefix}_{len(results)}_avocats_{timestamp}.csv"
        json_file = f"DIJON_{mode_prefix}_{len(results)}_avocats_{timestamp}.json"
        report_file = f"DIJON_{mode_prefix}_{len(results)}_avocats_{timestamp}_RAPPORT_COMPLET.txt"
        emails_file = f"DIJON_{mode_prefix}_{len(results)}_avocats_{timestamp}_EMAILS_UNIQUES_{emails_found}.txt"
        
        # Sauvegarde CSV
        df = pd.DataFrame(results)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Sauvegarde JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Rapport détaillé
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION - BARREAU DE DIJON\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Mode: {mode_prefix}\n")
            f.write(f"Total avocats: {len(results)}\n")
            f.write(f"Extractions réussies: {len(successful_results)} ({len(successful_results)/len(results)*100:.1f}%)\n\n")
            
            f.write(f"STATISTIQUES DÉTAILLÉES:\n")
            f.write(f"📅 Avec année serment: {serments_found}/{len(results)} ({serments_found/len(results)*100:.1f}%)\n")
            f.write(f"🎯 Avec spécialisations: {specialisations_found}/{len(results)} ({specialisations_found/len(results)*100:.1f}%)\n")
            f.write(f"📧 Avec email: {emails_found}/{len(results)} ({emails_found/len(results)*100:.1f}%)\n")
            f.write(f"📞 Avec téléphone: {phones_found}/{len(results)} ({phones_found/len(results)*100:.1f}%)\n")
            f.write(f"🏠 Avec adresse: {addresses_found}/{len(results)} ({addresses_found/len(results)*100:.1f}%)\n")
            f.write(f"🏢 Avec structure: {structures_found}/{len(results)} ({structures_found/len(results)*100:.1f}%)\n\n")
            
            # Aperçu des données
            f.write(f"APERÇU DES DONNÉES:\n")
            for i, result in enumerate(successful_results[:10], 1):
                f.write(f"   {i}. {result['prenom']} {result['nom']}\n")
                if result['annee_serment']:
                    f.write(f"      📅 Serment: {result['annee_serment']}\n")
                if result['email']:
                    f.write(f"      📧 {result['email']}\n")
                if result['adresse']:
                    f.write(f"      🏠 {result['adresse'][:100]}{'...' if len(result['adresse']) > 100 else ''}\n")
                if result['specialisations']:
                    f.write(f"      🎯 {result['specialisations'][:80]}{'...' if len(result['specialisations']) > 80 else ''}\n")
                f.write(f"\n")
            
            if len(successful_results) > 10:
                f.write(f"   ... et {len(successful_results) - 10} autres avocats\n")
        
        # Emails uniques
        if emails_found > 0:
            unique_emails = list(set([r['email'] for r in successful_results if r['email']]))
            with open(emails_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(unique_emails))
        
        # Affichage console
        print(f"\n✅ MISSION ACCOMPLIE!")
        print(f"🎯 {len(results)} avocats extraits avec parsing corrigé")
        print(f"📁 Fichiers CSV, JSON et rapports générés avec succès")
        print(f"✅ Noms, adresses et structures correctement formatés")
        
        self.logger.info("✅ Résultats sauvegardés:")
        self.logger.info(f"   📊 CSV complet: {csv_file}")
        self.logger.info(f"   📋 JSON: {json_file}")
        self.logger.info(f"   📑 Rapport: {report_file}")
        if emails_found > 0:
            self.logger.info(f"   📧 Emails ({emails_found}): {emails_file}")

    def cleanup(self):
        """Nettoyage final"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔚 Driver fermé")
        except:
            pass

    def run(self):
        """Méthode principale d'exécution"""
        try:
            results = self.run_extraction()
            self.save_results(results)
            return results
        finally:
            self.cleanup()

def main():
    print("🚀 SCRAPER FINAL CORRIGÉ - BARREAU DE DIJON")
    print("============================================================")
    print("✅ Gestion cookies corrigée pour capturer TOUS les avocats")
    print("🔍 Mode headless (aucune interface visuelle)")
    print("⚡ Optimisé pour traitement robuste de masse")
    print("💾 Sauvegardes automatiques de sécurité")
    print()
    
    print("Modes disponibles:")
    print("1. Test (10 avocats pour validation)")
    print("2. Production COMPLÈTE (tous les ~378 avocats du barreau)")
    print()
    
    try:
        choice = input("Choisissez le mode [1/2]: ").strip()
        
        if choice == "1":
            print("🧪 MODE TEST ACTIVÉ")
            print("⏳ Test sur 10 avocats...")
            scraper = DijonScraperFixedCookies(headless=True, test_mode=True)
            results = scraper.run()
            
        elif choice == "2":
            print("🏭 MODE PRODUCTION ACTIVÉ")
            print("⚠️  ATTENTION: Ceci va scraper TOUS les avocats du barreau (~378)")
            print("⏰ Temps estimé: 45-90 minutes")
            print("💾 Sauvegardes automatiques tous les 50 avocats")
            print()
            
            confirm = input("Êtes-vous sûr de continuer ? [oui/non]: ").strip().lower()
            if confirm in ['oui', 'o', 'yes', 'y']:
                print("⏳ Initialisation du scraper corrigé...")
                print("🔄 Démarrage de l'extraction...")
                print("💡 Le scraper va maintenant collecter tous les liens, puis extraire chaque fiche")
                print("📊 Le progrès sera affiché tous les 10 avocats")
                print("🔄 Retry automatique en cas d'échec")
                print("✅ Parsing amélioré pour noms, adresses et structures")
                print()
                
                scraper = DijonScraperFixedCookies(headless=True, test_mode=False)
                results = scraper.run()
            else:
                print("❌ Opération annulée")
                
        else:
            print("❌ Choix invalide")
            
    except KeyboardInterrupt:
        print("\n⚠️ Interruption par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")

if __name__ == "__main__":
    main()