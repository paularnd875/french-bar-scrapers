#!/usr/bin/env python3
"""
Script de production pour scraper TOUS les avocats du barreau de Lyon
Mode headless - 346 pages complètes
"""

import time
import csv
import json
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_barreau_lyon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BarreauLyonProductionScraper:
    def __init__(self):
        self.setup_driver_headless()
        self.avocats_data = []
        self.total_pages = 346
        self.start_time = datetime.now()
        
    def setup_driver_headless(self):
        """Configure le driver Chrome en mode headless pour la production"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Mode headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Ne pas charger les images pour plus de rapidité
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Optimisations pour la vitesse
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values": {
                "notifications": 2
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
        logger.info("🚀 Driver Chrome configuré en mode headless")
        
    def accept_cookies_silent(self):
        """Accepte les cookies en silence"""
        try:
            time.sleep(2)
            
            # Méthodes silencieuses pour accepter les cookies
            accept_methods = [
                lambda: self.driver.execute_script("""
                    if(window.axeptio) {
                        window.axeptio.execute('all');
                        return true;
                    }
                    return false;
                """),
                lambda: self.driver.execute_script("""
                    let buttons = document.querySelectorAll('button');
                    for(let btn of buttons) {
                        if(btn.textContent.toLowerCase().includes('accepter') || 
                           btn.textContent.toLowerCase().includes('accept') ||
                           btn.textContent.toLowerCase().includes('tout')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                """),
            ]
            
            for method in accept_methods:
                try:
                    if method():
                        time.sleep(1)
                        return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            logger.debug(f"Cookies: {e}")
            return False
    
    def get_lawyer_links_from_page(self, page_num):
        """Récupère tous les liens d'avocats d'une page"""
        try:
            url = f"https://www.barreaulyon.com/annuaire/?paged={page_num}"
            self.driver.get(url)
            time.sleep(1.5)
            
            # Accepter les cookies sur la première page
            if page_num == 1:
                self.accept_cookies_silent()
            
            # Attendre le chargement
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Script optimisé pour récupérer les liens
            script = """
                let links = [];
                document.querySelectorAll('a[href*="/annuaire/avocat/"]').forEach(link => {
                    let href = link.getAttribute('href');
                    if(href && href.includes('/annuaire/avocat/') && !links.includes(href)) {
                        if(href.startsWith('/')) href = 'https://www.barreaulyon.com' + href;
                        links.push(href);
                    }
                });
                return links;
            """
            
            lawyer_links = self.driver.execute_script(script)
            logger.info(f"Page {page_num:3d}/{self.total_pages}: {len(lawyer_links)} avocats trouvés")
            
            return lawyer_links
            
        except Exception as e:
            logger.error(f"Erreur page {page_num}: {e}")
            return []
    
    def extract_data_optimized(self, text):
        """Extraction optimisée des données depuis le texte"""
        data = {
            'annee_inscription': '',
            'specialisations': '',
            'structure': '',
            'adresse': '',
            'telephone': '',
            'case_postale': '',
            'code_postal': '',
            'ville': '',
            'langues': ''
        }
        
        try:
            # Patterns optimisés avec compilation regex
            patterns = {
                'annee_inscription': r'PRESTATION DE SERMENT\s*[^\d]*(\d{4})',
                'structure': r'STRUCTURE\s*([^\n]+)',
                'adresse': r'RUE\s*([^\n]+)', 
                'case_postale': r'CASE\s*([^\n]+)',
                'langues': r'LANGUES\s*([^\n]+)',
                'code_postal_ville': r'CODE POSTAL\s*([^\n]+)',
                'telephone': r'(\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                'specialisations': r'Domaines d\'activité\s*(.*?)(?:Ordre des avocats|$)'
            }
            
            for key, pattern in patterns.items():
                if key == 'telephone':
                    phones = re.findall(pattern, text)
                    if phones:
                        data['telephone'] = ', '.join(phones[:3])  # Max 3 numéros
                elif key == 'code_postal_ville':
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        cp_text = match.group(1).strip()
                        parts = cp_text.split(None, 1)
                        if parts:
                            data['code_postal'] = parts[0]
                            if len(parts) > 1:
                                data['ville'] = parts[1]
                elif key == 'specialisations':
                    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                    if match:
                        spec_text = match.group(1).strip()
                        spec_clean = re.sub(r'\s+', ' ', spec_text)
                        data['specialisations'] = spec_clean[:200]  # Limiter la longueur
                else:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        data[key] = match.group(1).strip()
            
        except Exception as e:
            logger.debug(f"Erreur extraction données: {e}")
        
        return data
    
    def scrape_lawyer_profile_fast(self, profile_url):
        """Scraping rapide d'une fiche avocat"""
        try:
            self.driver.get(profile_url)
            time.sleep(0.8)  # Délai réduit
            
            # Données de base
            avocat_data = {
                'url': profile_url,
                'prenom': '',
                'nom': '',
                'email': '',
                'annee_inscription': '',
                'specialisations': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'case_postale': '',
                'code_postal': '',
                'ville': '',
                'langues': ''
            }
            
            # Script combiné pour nom et email
            extraction_script = """
                let data = {name: '', email: ''};
                
                // Nom
                let h1 = document.querySelector('h1');
                if(h1) {
                    data.name = h1.textContent.replace(/Maître\\s*/i, '').trim();
                }
                
                // Email
                let emailLink = document.querySelector('a[href^="mailto:"]');
                if(emailLink) {
                    data.email = emailLink.getAttribute('href').replace('mailto:', '');
                }
                
                return data;
            """
            
            extracted = self.driver.execute_script(extraction_script)
            
            # Traitement du nom
            if extracted.get('name'):
                name_parts = extracted['name'].split()
                if len(name_parts) >= 2:
                    avocat_data['nom'] = ' '.join(name_parts[:-1])
                    avocat_data['prenom'] = name_parts[-1]
                else:
                    avocat_data['nom'] = extracted['name']
            
            # Email
            avocat_data['email'] = extracted.get('email', '')
            
            # Récupérer le texte de la page et extraire les autres données
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            other_data = self.extract_data_optimized(page_text)
            avocat_data.update(other_data)
            
            return avocat_data
            
        except Exception as e:
            logger.error(f"Erreur scraping {profile_url}: {e}")
            return None
    
    def save_periodic_backup(self, page_num):
        """Sauvegarde périodique des données"""
        if len(self.avocats_data) > 0 and page_num % 50 == 0:  # Toutes les 50 pages
            backup_file = f'backup_avocats_lyon_page_{page_num}.json'
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.avocats_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Sauvegarde backup: {len(self.avocats_data)} avocats")
    
    def scrape_all_pages(self, start_page=1, end_page=None):
        """Scrape toutes les pages de l'annuaire"""
        if end_page is None:
            end_page = self.total_pages
            
        logger.info(f"🔥 DÉBUT DU SCRAPING COMPLET")
        logger.info(f"📄 Pages: {start_page} à {end_page} (sur {self.total_pages})")
        logger.info(f"🕐 Heure de début: {self.start_time.strftime('%H:%M:%S')}")
        
        try:
            total_avocats = 0
            
            for page_num in range(start_page, end_page + 1):
                page_start = time.time()
                
                # Récupérer les liens de la page
                lawyer_links = self.get_lawyer_links_from_page(page_num)
                
                if not lawyer_links:
                    logger.warning(f"Page {page_num}: Aucun avocat trouvé")
                    continue
                
                # Scraper chaque avocat de la page
                page_avocats = 0
                for link in lawyer_links:
                    avocat_data = self.scrape_lawyer_profile_fast(link)
                    if avocat_data:
                        self.avocats_data.append(avocat_data)
                        total_avocats += 1
                        page_avocats += 1
                    
                    time.sleep(0.3)  # Petite pause entre les avocats
                
                page_time = time.time() - page_start
                elapsed = datetime.now() - self.start_time
                estimated_remaining = (page_time * (end_page - page_num)) / 60  # minutes
                
                logger.info(f"✅ Page {page_num:3d} terminée: {page_avocats} avocats en {page_time:.1f}s | "
                          f"Total: {total_avocats} | Temps écoulé: {elapsed} | "
                          f"Estimation restante: {estimated_remaining:.1f}min")
                
                # Sauvegardes périodiques
                self.save_periodic_backup(page_num)
                
                # Pause entre les pages
                time.sleep(0.5)
            
            # Sauvegarder les résultats finaux
            self.save_final_results()
            
            total_time = datetime.now() - self.start_time
            logger.info(f"🎉 SCRAPING TERMINÉ!")
            logger.info(f"📊 Total: {len(self.avocats_data)} avocats extraits")
            logger.info(f"⏰ Temps total: {total_time}")
            
        except KeyboardInterrupt:
            logger.info(f"\n⏸️  Scraping interrompu par l'utilisateur")
            logger.info(f"💾 Sauvegarde des données partielles...")
            self.save_final_results()
            
        except Exception as e:
            logger.error(f"Erreur globale: {e}")
            self.save_final_results()
            
        finally:
            self.driver.quit()
            logger.info("🔚 Driver fermé")
    
    def save_final_results(self):
        """Sauvegarde finale des résultats"""
        if not self.avocats_data:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f'avocats_barreau_lyon_complet_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.avocats_data, f, ensure_ascii=False, indent=2)
        
        # CSV pour analyse
        csv_file = f'avocats_barreau_lyon_complet_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.avocats_data:
                fieldnames = list(self.avocats_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.avocats_data)
        
        # Statistiques finales
        stats = self.generate_statistics()
        stats_file = f'statistiques_scraping_{timestamp}.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Fichiers sauvegardés:")
        logger.info(f"   📄 JSON: {json_file}")
        logger.info(f"   📄 CSV: {csv_file}")
        logger.info(f"   📊 Stats: {stats_file}")
    
    def generate_statistics(self):
        """Génère des statistiques complètes"""
        if not self.avocats_data:
            return {}
        
        total = len(self.avocats_data)
        stats = {
            'total_avocats': total,
            'timestamp': datetime.now().isoformat(),
            'temps_total': str(datetime.now() - self.start_time),
            'avec_email': sum(1 for a in self.avocats_data if a.get('email')),
            'avec_structure': sum(1 for a in self.avocats_data if a.get('structure')),
            'avec_specialisations': sum(1 for a in self.avocats_data if a.get('specialisations')),
            'avec_annee_inscription': sum(1 for a in self.avocats_data if a.get('annee_inscription')),
            'avec_telephone': sum(1 for a in self.avocats_data if a.get('telephone')),
        }
        
        # Années d'inscription
        annees = [a.get('annee_inscription') for a in self.avocats_data if a.get('annee_inscription')]
        if annees:
            annees_int = [int(a) for a in annees if a.isdigit()]
            if annees_int:
                stats['annee_inscription_min'] = min(annees_int)
                stats['annee_inscription_max'] = max(annees_int)
        
        # Structures les plus fréquentes
        structures = [a.get('structure') for a in self.avocats_data if a.get('structure')]
        from collections import Counter
        stats['top_structures'] = dict(Counter(structures).most_common(10))
        
        return stats

def main():
    """Fonction principale"""
    print("🚀 SCRAPER BARREAU DE LYON - PRODUCTION")
    print("=" * 50)
    print("Mode: HEADLESS (aucune fenêtre)")
    print("Pages: 1 à 346")
    print("Estimation: ~4-6 heures")
    print("=" * 50)
    
    choice = input("\nCommencer le scraping complet? (o/N): ").lower().strip()
    
    if choice in ['o', 'oui', 'y', 'yes']:
        scraper = BarreauLyonProductionScraper()
        
        # Options de démarrage
        start_page = 1
        end_page = None
        
        custom = input("Personnaliser les pages? (o/N): ").lower().strip()
        if custom in ['o', 'oui', 'y', 'yes']:
            try:
                start_page = int(input("Page de début (1): ") or "1")
                end_input = input("Page de fin (346): ") or "346"
                end_page = int(end_input) if end_input != "346" else None
            except ValueError:
                print("Valeurs invalides, utilisation des paramètres par défaut")
        
        print(f"\n🔥 Lancement du scraping...")
        print(f"📄 Pages: {start_page} à {end_page or 346}")
        print("💡 Pressez Ctrl+C pour arrêter et sauvegarder")
        print("-" * 50)
        
        scraper.scrape_all_pages(start_page, end_page)
    else:
        print("❌ Scraping annulé")

if __name__ == "__main__":
    main()