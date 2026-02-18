#!/usr/bin/env python3
"""
Scraper FINAL pour avocats-nancy.com
Extrait les 273 avocats en utilisant le bouton "Load More"
"""

import time
import json
import re
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Nancy273FinalScraper:
    def __init__(self):
        self.url = "https://avocats-nancy.com/annuaire-pro/"
        self.driver = None
        self.avocats = []
        
    def setup_driver(self):
        """Configure le driver Selenium"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
            '''
        })
    
    def apply_nancy_filter(self):
        """Applique le filtre Nancy via JavaScript direct"""
        logger.info("Application du filtre Nancy...")
        
        try:
            time.sleep(3)
            
            # Méthode JavaScript directe pour cliquer sur Nancy
            result = self.driver.execute_script("""
                let found = false;
                
                // Chercher le filtre Nancy dans les labels
                document.querySelectorAll('label').forEach(label => {
                    if (label.textContent.includes('Nancy') && label.textContent.includes('(273)')) {
                        // Trouver l'input associé
                        let input = label.querySelector('input[type="checkbox"], input[type="radio"]');
                        if (!input) {
                            // Chercher par for attribute
                            let forId = label.getAttribute('for');
                            if (forId) {
                                input = document.getElementById(forId);
                            }
                        }
                        
                        if (input && !input.checked) {
                            input.click();
                            found = true;
                        } else if (!input) {
                            // Cliquer sur le label lui-même
                            label.click();
                            found = true;
                        }
                    }
                });
                
                // Alternative: chercher dans les spans
                if (!found) {
                    document.querySelectorAll('span').forEach(span => {
                        if (span.textContent === 'Nancy' && span.parentElement) {
                            let parent = span.parentElement;
                            if (parent.tagName === 'LABEL') {
                                parent.click();
                                found = true;
                            }
                        }
                    });
                }
                
                return found;
            """)
            
            if result:
                logger.info("Filtre Nancy appliqué avec succès")
                time.sleep(5)  # Attendre le rechargement
                return True
            else:
                logger.warning("Filtre Nancy non trouvé - continuera sans filtre")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application du filtre: {e}")
            return False
    
    def load_all_cards(self):
        """Charge toutes les cartes en cliquant sur le bouton Load More"""
        logger.info("Chargement de toutes les cartes...")
        
        cards_loaded = 0
        max_attempts = 50  # Maximum de clics sur Load More
        
        for attempt in range(max_attempts):
            # Compter les cartes actuelles
            current_cards = len(self.driver.find_elements(By.CSS_SELECTOR, ".wpgb-card"))
            logger.info(f"Tentative {attempt + 1}: {current_cards} cartes actuellement")
            
            # Chercher et cliquer sur le bouton Load More
            load_more_clicked = self.driver.execute_script("""
                let button = document.querySelector('.wpgb-load-more button, .wpgb-load-more, button[data-action="load-more"]');
                if (button && !button.disabled && button.style.display !== 'none') {
                    button.scrollIntoView({behavior: 'smooth', block: 'center'});
                    button.click();
                    return true;
                }
                return false;
            """)
            
            if load_more_clicked:
                logger.info("Bouton 'Load More' cliqué")
                # Attendre le chargement des nouvelles cartes
                time.sleep(3)
                
                # Attendre que le loader disparaisse
                try:
                    WebDriverWait(self.driver, 10).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".wpgb-loader, .wpgb-loading"))
                    )
                except:
                    pass
                
                # Vérifier si de nouvelles cartes ont été chargées
                new_cards_count = len(self.driver.find_elements(By.CSS_SELECTOR, ".wpgb-card"))
                if new_cards_count == current_cards:
                    logger.info("Plus de nouvelles cartes à charger")
                    break
                    
                cards_loaded = new_cards_count
                
                # Si on a atteint 273 cartes ou plus, on peut arrêter
                if new_cards_count >= 273:
                    logger.info(f"Objectif atteint: {new_cards_count} cartes chargées")
                    break
            else:
                logger.info("Bouton 'Load More' non trouvé ou désactivé")
                break
        
        # Forcer l'affichage des cartes cachées
        self.driver.execute_script("""
            document.querySelectorAll('.wpgb-card-hidden').forEach(card => {
                card.classList.remove('wpgb-card-hidden');
                card.style.display = '';
                card.style.visibility = 'visible';
            });
        """)
        
        final_count = len(self.driver.find_elements(By.CSS_SELECTOR, ".wpgb-card"))
        logger.info(f"Total final de cartes: {final_count}")
        return final_count
    
    def extract_name_from_url(self, url):
        """Extrait le nom depuis l'URL portfolio"""
        if not url:
            return None
            
        match = re.search(r'/portfolio/([^/]+)/?', url)
        if match:
            name_slug = match.group(1)
            # Convertir le slug en nom propre
            parts = name_slug.split('-')
            
            # Gérer les noms composés et les particules
            name_parts = []
            for part in parts:
                if part.lower() in ['de', 'du', 'le', 'la', 'van', 'von']:
                    name_parts.append(part.lower())
                else:
                    name_parts.append(part.upper())
            
            return ' '.join(name_parts)
        return None
    
    def extract_lawyer_info(self, card, index):
        """Extrait les informations d'une carte avocat"""
        try:
            info = {
                "index": index,
                "nom": None,
                "url": None,
                "email": None,
                "telephone": None,
                "adresse": None,
                "specialite": None
            }
            
            # Extraire le nom et l'URL
            # Priorité 1: Lien portfolio
            portfolio_links = card.find_elements(By.CSS_SELECTOR, "a[href*='/portfolio/']")
            if portfolio_links:
                link = portfolio_links[0]
                url = link.get_attribute("href")
                text = link.text.strip()
                
                if text:
                    info["nom"] = text
                else:
                    # Extraire depuis data-title ou URL
                    data_title = card.find_element(By.CSS_SELECTOR, "[data-title]").get_attribute("data-title") if card.find_elements(By.CSS_SELECTOR, "[data-title]") else None
                    if data_title and data_title not in ["", "Agrandir la photo"]:
                        info["nom"] = data_title
                    else:
                        info["nom"] = self.extract_name_from_url(url)
                
                info["url"] = url
            
            # Si pas de portfolio link, chercher dans h3
            if not info["nom"]:
                h3_elements = card.find_elements(By.CSS_SELECTOR, "h3, .wpgb-block-3")
                for elem in h3_elements:
                    text = elem.text.strip()
                    if text:
                        info["nom"] = text
                        # Chercher un lien dans le h3
                        links = elem.find_elements(By.TAG_NAME, "a")
                        if links:
                            info["url"] = links[0].get_attribute("href")
                        break
            
            # Extraire email
            email_links = card.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
            if email_links:
                info["email"] = email_links[0].get_attribute("href").replace("mailto:", "")
            
            # Extraire téléphone
            tel_links = card.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
            if tel_links:
                info["telephone"] = tel_links[0].get_attribute("href").replace("tel:", "")
            
            # Extraire adresse
            address_elements = card.find_elements(By.CSS_SELECTOR, ".address, .location, address, .wpgb-block-2")
            if address_elements:
                info["adresse"] = address_elements[0].text.strip()
            
            # Extraire spécialité
            specialite_elements = card.find_elements(By.CSS_SELECTOR, ".specialite, .specialty, .wpgb-block-4")
            if specialite_elements:
                info["specialite"] = specialite_elements[0].text.strip()
            
            return info
            
        except Exception as e:
            logger.error(f"Erreur extraction carte {index}: {e}")
            return None
    
    def run(self):
        """Exécute le scraping complet"""
        logger.info("=" * 80)
        logger.info("DÉMARRAGE DU SCRAPER NANCY 273 AVOCATS")
        logger.info("=" * 80)
        
        try:
            self.setup_driver()
            logger.info(f"Accès à {self.url}")
            self.driver.get(self.url)
            
            # Appliquer le filtre Nancy
            filter_applied = self.apply_nancy_filter()
            
            # Charger toutes les cartes via Load More
            total_cards = self.load_all_cards()
            
            # Récupérer toutes les cartes
            all_cards = self.driver.find_elements(By.CSS_SELECTOR, ".wpgb-card")
            logger.info(f"\nExtraction de {len(all_cards)} cartes...")
            
            # Extraire les informations de chaque carte
            for i, card in enumerate(all_cards, 1):
                if i % 20 == 0:
                    logger.info(f"Progression: {i}/{len(all_cards)} cartes traitées")
                
                # Scroller jusqu'à la carte pour s'assurer qu'elle est visible
                if i % 10 == 0:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card)
                    time.sleep(0.3)
                
                info = self.extract_lawyer_info(card, i)
                if info and info["nom"]:
                    self.avocats.append(info)
            
            logger.info(f"\nExtraction terminée: {len(self.avocats)} avocats trouvés sur {len(all_cards)} cartes")
            
            # Sauvegarder les résultats
            self.save_results()
            
        except Exception as e:
            logger.error(f"Erreur pendant le scraping: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Sauvegarde les résultats dans plusieurs formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Créer le rapport
        report_lines = [
            "=" * 80,
            "RAPPORT FINAL - NANCY 273 AVOCATS",
            "=" * 80,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"URL: {self.url}",
            "",
            "RÉSULTATS:",
            f"- Avocats extraits: {len(self.avocats)}",
            f"- Avocats avec email: {sum(1 for a in self.avocats if a.get('email'))}",
            f"- Avocats avec téléphone: {sum(1 for a in self.avocats if a.get('telephone'))}",
            "",
            "LISTE COMPLÈTE DES AVOCATS:",
            "-" * 40
        ]
        
        for avocat in self.avocats:
            report_lines.append(f"\n{avocat['index']}. {avocat['nom']}")
            if avocat.get('email'):
                report_lines.append(f"   Email: {avocat['email']}")
            if avocat.get('telephone'):
                report_lines.append(f"   Tél: {avocat['telephone']}")
            if avocat.get('adresse'):
                report_lines.append(f"   Adresse: {avocat['adresse']}")
            if avocat.get('specialite'):
                report_lines.append(f"   Spécialité: {avocat['specialite']}")
        
        # Sauvegarder le rapport texte
        report_file = f"NANCY_273_RAPPORT_FINAL_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        logger.info(f"✓ Rapport sauvegardé: {report_file}")
        
        # Sauvegarder JSON
        json_file = f"NANCY_273_AVOCATS_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.avocats, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ JSON sauvegardé: {json_file}")
        
        # Sauvegarder CSV
        csv_file = f"NANCY_273_AVOCATS_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.avocats:
                fieldnames = ['index', 'nom', 'email', 'telephone', 'adresse', 'specialite', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.avocats)
        logger.info(f"✓ CSV sauvegardé: {csv_file}")
        
        # Sauvegarder liste d'emails
        emails = [a['email'] for a in self.avocats if a.get('email')]
        if emails:
            email_file = f"NANCY_273_EMAILS_{timestamp}.txt"
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(emails))
            logger.info(f"✓ Liste d'emails sauvegardée: {email_file} ({len(emails)} emails)")
        
        # Afficher le résumé final
        print("\n" + "=" * 80)
        print("EXTRACTION TERMINÉE AVEC SUCCÈS")
        print("=" * 80)
        print(f"✓ {len(self.avocats)} avocats extraits")
        print(f"✓ {len(emails)} emails récupérés")
        print(f"✓ Fichiers générés:")
        print(f"  - {report_file}")
        print(f"  - {json_file}")
        print(f"  - {csv_file}")
        if emails:
            print(f"  - {email_file}")
        print("=" * 80)

if __name__ == "__main__":
    scraper = Nancy273FinalScraper()
    scraper.run()