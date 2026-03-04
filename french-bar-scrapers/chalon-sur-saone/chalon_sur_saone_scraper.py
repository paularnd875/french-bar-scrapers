#!/usr/bin/env python3
"""
Scraper COMPLET pour le Barreau de Chalon-sur-Saône
Récupération de TOUS les avocats avec navigation entre pages
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import re
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChalonsurSaoneBarScraperProduction:
    def __init__(self, headless=True):
        self.base_url = "https://www.avocats-chalonsursaone.com/annuaire-des-avocats-chalon-sur-saone/"
        self.lawyers_data = []
        self.headless = headless
        self.setup_driver()
    
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-gpu")
        
        # Options pour éviter la détection et optimiser les performances
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Accélérer le chargement
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
    
    def get_pagination_info(self):
        """Récupérer les informations de pagination"""
        try:
            # Chercher les liens de pagination
            pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "a.pagenav")
            
            page_numbers = []
            for link in pagination_links:
                text = link.text.strip()
                if text.isdigit():
                    page_numbers.append(int(text))
            
            max_page = max(page_numbers) if page_numbers else 1
            
            # Vérifier aussi dans le texte de la page
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                # Chercher des patterns comme "Page 1 sur 7" ou "100 total"
                total_matches = re.findall(r'(\d+)\s*(?:total|membres)', page_text, re.IGNORECASE)
                if total_matches:
                    total_lawyers = int(total_matches[-1])
                    logger.info(f"Total d'avocats détecté: {total_lawyers}")
            except:
                pass
            
            logger.info(f"Nombre de pages détectées: {max_page}")
            return max_page
            
        except Exception as e:
            logger.warning(f"Erreur lors de la détection de pagination: {e}")
            return 7  # Valeur par défaut basée sur l'analyse précédente
    
    def get_lawyers_from_current_page(self):
        """Récupérer tous les avocats de la page actuelle"""
        try:
            # Attendre que le tableau soit chargé
            table = self.wait.until(EC.presence_of_element_located((By.ID, "cbUserTable")))
            
            # Trouver toutes les lignes d'avocats dans le tbody
            lawyer_rows = self.driver.find_elements(By.CSS_SELECTOR, "#cbUserTable tbody tr")
            
            lawyers_info = []
            
            for i, row in enumerate(lawyer_rows):
                try:
                    # Extraire nom et prénom depuis les liens
                    lastname_link = row.find_element(By.CSS_SELECTOR, ".cbUserListFC_lastname a")
                    firstname_link = row.find_element(By.CSS_SELECTOR, ".cbUserListFC_firstname a")
                    
                    lastname = lastname_link.text.strip()
                    firstname = firstname_link.text.strip()
                    profile_url = lastname_link.get_attribute("href")
                    
                    # Extraire l'adresse
                    try:
                        adresse_element = row.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_adresse1")
                        adresse = adresse_element.text.strip()
                    except NoSuchElementException:
                        adresse = ""
                    
                    # Extraire la ville
                    try:
                        ville_element = row.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_ville")
                        ville = ville_element.text.strip()
                    except NoSuchElementException:
                        ville = ""
                    
                    # Extraire le téléphone
                    try:
                        telephone_element = row.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_telephone")
                        telephone = telephone_element.text.strip()
                    except NoSuchElementException:
                        telephone = ""
                    
                    lawyer_info = {
                        'nom': lastname,
                        'prenom': firstname,
                        'nom_complet': f"{firstname} {lastname}",
                        'adresse': adresse,
                        'ville': ville,
                        'telephone': telephone,
                        'profile_url': profile_url
                    }
                    
                    lawyers_info.append(lawyer_info)
                
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction de l'avocat {i+1} sur cette page: {e}")
                    continue
            
            return lawyers_info
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des avocats de cette page: {e}")
            return []
    
    def navigate_to_page(self, page_num):
        """Naviguer vers une page spécifique"""
        try:
            if page_num == 1:
                self.driver.get(self.base_url)
                time.sleep(3)
                return True
            
            # Construire l'URL pour la page spécifique
            # Format basé sur l'analyse de la pagination: limit=15&start=X
            start_value = (page_num - 1) * 15
            page_url = f"{self.base_url}userslist/Avocats.html?limit=15&start={start_value}"
            
            logger.info(f"Navigation vers la page {page_num}: {page_url}")
            self.driver.get(page_url)
            time.sleep(3)
            
            # Vérifier que la page s'est bien chargée
            table = self.wait.until(EC.presence_of_element_located((By.ID, "cbUserTable")))
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la navigation vers la page {page_num}: {e}")
            return False
    
    def extract_lawyer_details(self, lawyer_url):
        """Extraire les détails complets depuis la fiche individuelle"""
        try:
            # Naviguer vers la page de l'avocat
            self.driver.get(lawyer_url)
            time.sleep(2)
            
            details = {}
            
            # Récupérer le code source pour l'analyse par regex
            page_source = self.driver.page_source
            
            # Chercher l'email
            email_patterns = [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'mailto:([^"\'\\s]+)',
            ]
            
            for pattern in email_patterns:
                emails = re.findall(pattern, page_source, re.IGNORECASE)
                if emails:
                    for email in emails:
                        if '@' in email and '.' in email and len(email) > 5:
                            details['email'] = email.strip()
                            break
                    if 'email' in details:
                        break
            
            # Chercher l'année d'inscription au barreau
            inscription_patterns = [
                r'[Ii]nscrit(?:ion)?\s*.*?(\d{4})',
                r'[Bb]arreau\s*.*?(\d{4})',
                r'(\d{4})\s*[Ii]nscrit',
                r'depuis\s*(\d{4})',
                r'[Aa]dmis.*?(\d{4})',
            ]
            
            for pattern in inscription_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    for year in matches:
                        if 1980 <= int(year) <= 2025:
                            details['annee_inscription'] = year
                            break
                    if 'annee_inscription' in details:
                        break
            
            # Chercher les spécialisations - version améliorée
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                # Mots-clés pour les domaines de spécialisation
                specialization_keywords = [
                    'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
                    'droit de la famille', 'droit immobilier', 'droit des affaires',
                    'droit public', 'droit administratif', 'droit fiscal', 'droit social',
                    'droit international', 'droit européen', 'droit de la santé',
                    'droit de l\'environnement', 'droit bancaire', 'propriété intellectuelle',
                    'droit des sociétés', 'droit du sport', 'droit de l\'urbanisme',
                    'droit rural', 'droit maritime', 'droit aérien', 'droit de l\'informatique'
                ]
                
                found_specializations = []
                for spec in specialization_keywords:
                    if spec in body_text:
                        found_specializations.append(spec.title())
                
                if found_specializations:
                    details['specialisations'] = '; '.join(found_specializations[:3])  # Max 3
                
            except Exception as e:
                logger.debug(f"Erreur extraction spécialisations: {e}")
            
            # Chercher la structure
            structure_patterns = [
                r'[Cc]abinet\s+([A-Za-z\s&-]+)',
                r'SCP\s+([A-Za-z\s&-]+)',
                r'[Ss]ociété\s+([A-Za-z\s&-]+)',
                r'[Aa]ssociation\s+([A-Za-z\s&-]+)',
            ]
            
            for pattern in structure_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    clean_structure = re.sub(r'<[^>]+>', '', matches[0]).strip()
                    if len(clean_structure) > 3 and len(clean_structure) < 100:
                        details['structure'] = clean_structure
                        break
            
            return details
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des détails: {e}")
            return {'erreur_extraction': str(e)}
    
    def run_complete_scraping(self):
        """Lancer le scraping complet de tous les avocats"""
        try:
            logger.info("=== DÉBUT DU SCRAPING COMPLET - CHALON-SUR-SAÔNE ===")
            start_time = datetime.now()
            
            # Aller sur la première page
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Détecter le nombre de pages
            total_pages = self.get_pagination_info()
            
            logger.info(f"🚀 Début du scraping sur {total_pages} pages")
            
            # Parcourir toutes les pages
            for page_num in range(1, total_pages + 1):
                logger.info(f"\n📄 TRAITEMENT DE LA PAGE {page_num}/{total_pages}")
                
                # Naviguer vers la page
                if not self.navigate_to_page(page_num):
                    logger.error(f"Impossible d'accéder à la page {page_num}")
                    continue
                
                # Récupérer les avocats de cette page
                page_lawyers = self.get_lawyers_from_current_page()
                
                if not page_lawyers:
                    logger.warning(f"Aucun avocat trouvé sur la page {page_num}")
                    continue
                
                logger.info(f"✅ {len(page_lawyers)} avocats trouvés sur la page {page_num}")
                
                # Pour chaque avocat, récupérer les détails
                for i, lawyer in enumerate(page_lawyers):
                    try:
                        logger.info(f"  📋 Traitement {i+1}/{len(page_lawyers)}: {lawyer['nom_complet']}")
                        
                        # Extraire les détails depuis la fiche individuelle
                        details = self.extract_lawyer_details(lawyer['profile_url'])
                        
                        # Fusionner les informations
                        lawyer.update(details)
                        self.lawyers_data.append(lawyer)
                        
                        # Pause courte entre les requêtes
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"  ❌ Erreur lors du traitement de {lawyer.get('nom_complet', 'Avocat inconnu')}: {e}")
                        continue
                
                # Sauvegarde intermédiaire tous les 2 pages
                if page_num % 2 == 0:
                    self.save_intermediate_results(page_num)
                
                logger.info(f"📊 Page {page_num} terminée. Total traité: {len(self.lawyers_data)} avocats")
            
            # Sauvegarde finale
            self.save_final_results()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"\n🎉 SCRAPING TERMINÉ!")
            logger.info(f"⏱️  Durée totale: {duration}")
            logger.info(f"👥 Total d'avocats récupérés: {len(self.lawyers_data)}")
            
            # Statistiques finales
            self.print_final_statistics()
            
        except Exception as e:
            logger.error(f"Erreur générale dans le scraping complet: {e}")
        
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()
    
    def save_intermediate_results(self, page_num):
        """Sauvegarder les résultats intermédiaires"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"chalon_partial_p{page_num}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Sauvegarde intermédiaire: {filename}")
    
    def save_final_results(self):
        """Sauvegarder les résultats finaux"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV complet
        csv_filename = f"chalon_COMPLET_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if self.lawyers_data:
                fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                            'adresse', 'ville', 'annee_inscription', 'specialisations', 
                            'structure', 'profile_url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # JSON complet
        json_filename = f"chalon_COMPLET_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails seulement
        emails_filename = f"chalon_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            emails = [lawyer.get('email', '') for lawyer in self.lawyers_data if lawyer.get('email')]
            for email in sorted(set(emails)):
                emailfile.write(f"{email}\n")
        
        # Rapport final
        report_filename = f"chalon_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write("=== RAPPORT COMPLET - BARREAU CHALON-SUR-SAÔNE ===\n\n")
            reportfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"Nombre total d'avocats: {len(self.lawyers_data)}\n\n")
            
            # Statistiques
            emails_count = sum(1 for l in self.lawyers_data if l.get('email'))
            phones_count = sum(1 for l in self.lawyers_data if l.get('telephone'))
            years_count = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
            specs_count = sum(1 for l in self.lawyers_data if l.get('specialisations'))
            
            reportfile.write(f"STATISTIQUES:\n")
            reportfile.write(f"- Emails trouvés: {emails_count}/{len(self.lawyers_data)} ({emails_count/len(self.lawyers_data)*100:.1f}%)\n")
            reportfile.write(f"- Téléphones: {phones_count}/{len(self.lawyers_data)} ({phones_count/len(self.lawyers_data)*100:.1f}%)\n")
            reportfile.write(f"- Années inscription: {years_count}/{len(self.lawyers_data)} ({years_count/len(self.lawyers_data)*100:.1f}%)\n")
            reportfile.write(f"- Spécialisations: {specs_count}/{len(self.lawyers_data)} ({specs_count/len(self.lawyers_data)*100:.1f}%)\n\n")
        
        logger.info(f"✅ RÉSULTATS FINAUX SAUVEGARDÉS:")
        logger.info(f"📄 CSV complet: {csv_filename}")
        logger.info(f"📄 JSON complet: {json_filename}")
        logger.info(f"📧 Emails uniquement: {emails_filename}")
        logger.info(f"📊 Rapport: {report_filename}")
    
    def print_final_statistics(self):
        """Afficher les statistiques finales"""
        if not self.lawyers_data:
            return
        
        emails_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('email'))
        phones_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('telephone'))
        years_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('annee_inscription'))
        specs_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('specialisations'))
        structures_found = sum(1 for lawyer in self.lawyers_data if lawyer.get('structure'))
        
        total = len(self.lawyers_data)
        
        logger.info(f"\n📊 STATISTIQUES FINALES:")
        logger.info(f"👥 Total d'avocats: {total}")
        logger.info(f"📧 Emails: {emails_found}/{total} ({emails_found/total*100:.1f}%)")
        logger.info(f"📞 Téléphones: {phones_found}/{total} ({phones_found/total*100:.1f}%)")
        logger.info(f"📅 Années inscription: {years_found}/{total} ({years_found/total*100:.1f}%)")
        logger.info(f"⚖️  Spécialisations: {specs_found}/{total} ({specs_found/total*100:.1f}%)")
        logger.info(f"🏢 Structures: {structures_found}/{total} ({structures_found/total*100:.1f}%)")

def main():
    """Fonction principale avec choix du mode"""
    import sys
    
    print("🏛️  SCRAPER BARREAU DE CHALON-SUR-SAÔNE 🏛️")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--visual':
        print("Mode: VISUEL (pour debug)")
        headless = False
    else:
        print("Mode: HEADLESS (production)")
        headless = True
    
    print(f"URL: https://www.avocats-chalonsursaone.com/")
    print("=" * 50)
    
    scraper = ChalonsurSaoneBarScraperProduction(headless=headless)
    scraper.run_complete_scraping()

if __name__ == "__main__":
    main()