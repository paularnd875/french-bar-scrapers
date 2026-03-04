#!/usr/bin/env python3
"""
Nancy Portfolio Scraper - Extraction complète des informations détaillées
Parcourt chaque fiche avocat pour récupérer toutes les informations disponibles
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

class NancyPortfolioScraper:
    def __init__(self):
        self.driver = None
        self.avocats_detailles = []
        self.load_existing_data()
        
    def load_existing_data(self):
        """Charge les données de base depuis le fichier JSON existant"""
        try:
            with open('/Users/paularnould/NANCY_273_AVOCATS_20260217_171009.json', 'r', encoding='utf-8') as f:
                self.base_data = json.load(f)
            logger.info(f"Données de base chargées: {len(self.base_data)} avocats")
        except Exception as e:
            logger.error(f"Erreur chargement données de base: {e}")
            self.base_data = []
        
    def setup_driver(self):
        """Configure le driver Selenium en mode headless"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
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

    def extract_email(self, text):
        """Extrait l'email du texte"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None

    def extract_phone(self, text):
        """Extrait le numéro de téléphone du texte"""
        # Patterns français
        phone_patterns = [
            r'0[1-9](?:[.-\s]?\d{2}){4}',  # 01 23 45 67 89
            r'\+33[.-\s]?[1-9](?:[.-\s]?\d{2}){4}',  # +33 1 23 45 67 89
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    def extract_year(self, text):
        """Extrait l'année d'inscription au barreau"""
        # Chercher des patterns comme "inscrit au Barreau en 2010", "depuis 1995", etc.
        year_patterns = [
            r'(?:inscrit|inscription).*?(?:barreau|Barreau).*?(?:en\s+|depuis\s+)?(\d{4})',
            r'(?:barreau|Barreau).*?(?:en\s+|depuis\s+)?(\d{4})',
            r'(\d{4}).*?(?:inscrit|inscription)',
            r'(\d{4})'  # Dernière option: toute année de 4 chiffres
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                year = int(match)
                if 1950 <= year <= 2026:  # Années plausibles pour un avocat
                    return year
        return None

    def extract_prestation_date(self, driver):
        """Extrait la date de prestation de serment spécifiquement"""
        try:
            # Méthode 1: Chercher le paragraphe spécifique avec la classe
            prestation_elements = driver.find_elements(By.CSS_SELECTOR, 
                "p.has-text-align-right.wp-block-paragraph")
            
            for elem in prestation_elements:
                text = elem.text.strip()
                if "prestation de serment" in text.lower():
                    # Extraire la date au format DD/MM/YYYY
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                    if date_match:
                        date_str = date_match.group(1)
                        # Convertir en année
                        try:
                            year = int(date_str.split('/')[-1])
                            return year, date_str
                        except:
                            pass
            
            # Méthode 2: Chercher dans tous les paragraphes
            all_paragraphs = driver.find_elements(By.TAG_NAME, "p")
            for p in all_paragraphs:
                text = p.text.strip()
                if "prestation de serment" in text.lower():
                    # Extraire la date
                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            year = int(date_str.split('/')[-1])
                            return year, date_str
                        except:
                            pass
            
            # Méthode 3: Chercher dans le texte complet
            page_text = driver.find_element(By.TAG_NAME, "body").text
            prestation_match = re.search(r'prestation\s+de\s+serment\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})', 
                                        page_text, re.IGNORECASE)
            if prestation_match:
                date_str = prestation_match.group(1)
                try:
                    year = int(date_str.split('/')[-1])
                    return year, date_str
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Erreur extraction date prestation: {e}")
        
        return None, None

    def separate_name_ultimate(self, full_name):
        """Sépare prénom et nom avec gestion des noms composés"""
        if not full_name:
            return None, None
            
        # Nettoyage
        full_name = full_name.strip()
        
        # Cas spéciaux pour noms composés
        special_cases = {
            "DAL MOLIN, Georges": ("Georges", "DAL MOLIN"),
            "DEVARENNE ODAERT, Nathalie": ("Nathalie", "DEVARENNE ODAERT"),
            "DI ROSA, Betty": ("Betty", "DI ROSA"),
            "DE LA ROSA, Maria": ("Maria", "DE LA ROSA"),
            "VAN DER BERG, Peter": ("Peter", "VAN DER BERG"),
        }
        
        if full_name in special_cases:
            return special_cases[full_name]
        
        # Pattern principal: "NOM, Prénom" ou "NOM Prénom"
        if ',' in full_name:
            parts = full_name.split(',', 1)
            nom = parts[0].strip()
            prenom = parts[1].strip()
        else:
            words = full_name.split()
            if len(words) >= 2:
                # Dernier mot = prénom, le reste = nom
                prenom = words[-1]
                nom = ' '.join(words[:-1])
            else:
                # Un seul mot
                nom = full_name
                prenom = ""
        
        return prenom, nom

    def extract_portfolio_details(self, url):
        """Extrait toutes les informations détaillées d'une fiche portfolio"""
        try:
            logger.debug(f"Accès à {url}")
            self.driver.get(url)
            
            # Attendre le chargement
            time.sleep(2)
            
            # Récupérer tout le texte de la page
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            details = {
                'email': None,
                'telephone': None,
                'telephone_2': None,  # Numéro secondaire
                'adresse': None,
                'adresse_complete': None,
                'code_postal': None,
                'ville': None,
                'annee_inscription': None,
                'date_prestation_serment': None,  # Date complète DD/MM/YYYY
                'specialites': [],
                'competences': [],
                'langues': [],
                'cabinet': None,
                'titre': None,  # Me, Maître, etc.
                'description': None,
                'horaires': None,
                'site_web': None
            }
            
            # Extraction des éléments spécifiques
            try:
                # Email
                email_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                if email_elements:
                    details['email'] = email_elements[0].get_attribute('href').replace('mailto:', '').strip()
                else:
                    # Chercher dans le texte
                    details['email'] = self.extract_email(page_text)
                
                # Téléphone
                tel_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
                if tel_elements:
                    details['telephone'] = tel_elements[0].get_attribute('href').replace('tel:', '').strip()
                    # Deuxième numéro s'il existe
                    if len(tel_elements) > 1:
                        details['telephone_2'] = tel_elements[1].get_attribute('href').replace('tel:', '').strip()
                else:
                    # Chercher dans le texte
                    details['telephone'] = self.extract_phone(page_text)
                
                # Adresse - chercher dans plusieurs endroits possibles
                address_selectors = [
                    ".address", ".location", ".contact-info", 
                    "[class*='address']", "[class*='contact']",
                    "p:contains('Avenue')", "p:contains('Rue')", "p:contains('Boulevard')"
                ]
                
                for selector in address_selectors:
                    try:
                        addr_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if addr_elements:
                            addr_text = addr_elements[0].text.strip()
                            if addr_text and len(addr_text) > 5:  # Éviter les textes trop courts
                                details['adresse'] = addr_text
                                break
                    except:
                        continue
                
                # Spécialités - chercher dans les contenus
                specialite_keywords = ['spécialit', 'domaine', 'expertise', 'compétence']
                specialites_found = []
                
                # Chercher dans les listes et paragraphes
                list_elements = self.driver.find_elements(By.CSS_SELECTOR, "ul li, ol li")
                for li in list_elements:
                    text = li.text.strip()
                    if any(keyword in text.lower() for keyword in specialite_keywords) or \
                       any(word in text.lower() for word in ['droit', 'pénal', 'civil', 'commercial', 'famille']):
                        if text not in specialites_found and len(text) < 100:
                            specialites_found.append(text)
                
                details['specialites'] = specialites_found[:5]  # Limiter à 5
                
                # Date de prestation de serment (prioritaire)
                year_prestation, date_prestation = self.extract_prestation_date(self.driver)
                if year_prestation:
                    details['annee_inscription'] = year_prestation
                    details['date_prestation_serment'] = date_prestation
                else:
                    # Fallback: chercher dans le texte général
                    details['annee_inscription'] = self.extract_year(page_text)
                
                # Site web
                web_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='http']:not([href*='avocats-nancy.com'])")
                if web_elements:
                    details['site_web'] = web_elements[0].get_attribute('href')
                
                # Description - paragraphe principal
                desc_elements = self.driver.find_elements(By.CSS_SELECTOR, ".entry-content p, .content p, .description, article p")
                if desc_elements:
                    desc_text = desc_elements[0].text.strip()
                    if len(desc_text) > 50:  # Description substantielle
                        details['description'] = desc_text[:500]  # Limiter la longueur
                
                # Cabinet/Structure
                cabinet_keywords = ['cabinet', 'société', 'scpa', 'scp', 'selarl']
                for keyword in cabinet_keywords:
                    if keyword in page_text.lower():
                        # Extraire le nom du cabinet autour du mot-clé
                        import re
                        pattern = rf'([A-Z][A-Za-z\s&-]+{keyword}[A-Za-z\s&-]*)'
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            details['cabinet'] = match.group(1).strip()
                            break
                
            except Exception as e:
                logger.debug(f"Erreur extraction détails pour {url}: {e}")
            
            return details
            
        except Exception as e:
            logger.error(f"Erreur accès portfolio {url}: {e}")
            return None

    def run(self):
        """Exécute le scraping complet des portfolios"""
        logger.info("=" * 80)
        logger.info("DÉMARRAGE DU SCRAPER DÉTAILLÉ DES PORTFOLIOS NANCY")
        logger.info("=" * 80)
        
        try:
            self.setup_driver()
            
            total_avocats = len(self.base_data)
            logger.info(f"Traitement de {total_avocats} portfolios d'avocats")
            
            for i, avocat_base in enumerate(self.base_data, 1):
                if i % 10 == 0:
                    logger.info(f"Progression: {i}/{total_avocats} portfolios traités")
                
                # Données de base
                avocat_complet = avocat_base.copy()
                
                # Séparer prénom/nom
                prenom, nom = self.separate_name_ultimate(avocat_base.get('nom', ''))
                avocat_complet['prenom'] = prenom
                avocat_complet['nom_famille'] = nom
                
                # Extraire détails du portfolio
                if avocat_base.get('url'):
                    details = self.extract_portfolio_details(avocat_base['url'])
                    if details:
                        avocat_complet.update(details)
                
                self.avocats_detailles.append(avocat_complet)
                
                # Pause pour éviter la surcharge
                time.sleep(0.5)
            
            logger.info(f"Extraction terminée: {len(self.avocats_detailles)} avocats traités")
            
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
        """Sauvegarde les résultats détaillés"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Statistiques
        total_avocats = len(self.avocats_detailles)
        avec_email = sum(1 for a in self.avocats_detailles if a.get('email'))
        avec_telephone = sum(1 for a in self.avocats_detailles if a.get('telephone'))
        avec_adresse = sum(1 for a in self.avocats_detailles if a.get('adresse'))
        avec_specialites = sum(1 for a in self.avocats_detailles if a.get('specialites'))
        avec_annee = sum(1 for a in self.avocats_detailles if a.get('annee_inscription'))
        avec_date_prestation = sum(1 for a in self.avocats_detailles if a.get('date_prestation_serment'))
        
        # Rapport détaillé
        report_lines = [
            "=" * 80,
            "RAPPORT COMPLET - PORTFOLIOS NANCY",
            "=" * 80,
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total d'avocats: {total_avocats}",
            "",
            "STATISTIQUES:",
            f"- Avec email: {avec_email} ({avec_email/total_avocats*100:.1f}%)",
            f"- Avec téléphone: {avec_telephone} ({avec_telephone/total_avocats*100:.1f}%)",
            f"- Avec adresse: {avec_adresse} ({avec_adresse/total_avocats*100:.1f}%)",
            f"- Avec spécialités: {avec_specialites} ({avec_specialites/total_avocats*100:.1f}%)",
            f"- Avec année inscription: {avec_annee} ({avec_annee/total_avocats*100:.1f}%)",
            f"- Avec date prestation serment: {avec_date_prestation} ({avec_date_prestation/total_avocats*100:.1f}%)",
            "",
            "ÉCHANTILLON DES DONNÉES:",
            "-" * 40
        ]
        
        # Afficher 5 premiers exemples
        for avocat in self.avocats_detailles[:5]:
            report_lines.append(f"\n{avocat.get('nom', 'N/A')}")
            report_lines.append(f"  Prénom: {avocat.get('prenom', 'N/A')}")
            report_lines.append(f"  Nom famille: {avocat.get('nom_famille', 'N/A')}")
            report_lines.append(f"  Email: {avocat.get('email', 'N/A')}")
            report_lines.append(f"  Téléphone: {avocat.get('telephone', 'N/A')}")
            report_lines.append(f"  Adresse: {avocat.get('adresse', 'N/A')}")
            report_lines.append(f"  Année: {avocat.get('annee_inscription', 'N/A')}")
            report_lines.append(f"  Date prestation: {avocat.get('date_prestation_serment', 'N/A')}")
            report_lines.append(f"  Spécialités: {', '.join(avocat.get('specialites', []))}")
        
        # Sauvegarder rapport
        report_file = f"NANCY_PORTFOLIOS_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report_lines))
        
        # Sauvegarder JSON complet
        json_file = f"NANCY_PORTFOLIOS_COMPLET_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.avocats_detailles, f, ensure_ascii=False, indent=2)
        
        # Sauvegarder CSV détaillé
        csv_file = f"NANCY_PORTFOLIOS_COMPLET_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.avocats_detailles:
                fieldnames = [
                    'index', 'nom', 'prenom', 'nom_famille', 'email', 'telephone', 'telephone_2',
                    'adresse', 'adresse_complete', 'code_postal', 'ville', 'annee_inscription', 
                    'date_prestation_serment', 'specialites', 'specialite', 'competences', 'langues', 
                    'cabinet', 'titre', 'site_web', 'description', 'horaires', 'url'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for avocat in self.avocats_detailles:
                    # Convertir les listes en chaînes
                    row = avocat.copy()
                    if row.get('specialites'):
                        row['specialites'] = '; '.join(row['specialites'])
                    writer.writerow(row)
        
        # Liste des emails uniquement
        emails = [a['email'] for a in self.avocats_detailles if a.get('email')]
        if emails:
            email_file = f"NANCY_PORTFOLIOS_EMAILS_{timestamp}.txt"
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(sorted(set(emails))))
        
        # Afficher résumé final
        print("\n" + "=" * 80)
        print("EXTRACTION PORTFOLIOS TERMINÉE")
        print("=" * 80)
        print(f"✓ {total_avocats} avocats traités")
        print(f"✓ {avec_email} emails récupérés ({avec_email/total_avocats*100:.1f}%)")
        print(f"✓ {avec_telephone} téléphones récupérés ({avec_telephone/total_avocats*100:.1f}%)")
        print(f"✓ {avec_adresse} adresses récupérées ({avec_adresse/total_avocats*100:.1f}%)")
        print(f"✓ Fichiers générés:")
        print(f"  - {report_file}")
        print(f"  - {json_file}")
        print(f"  - {csv_file}")
        if emails:
            print(f"  - {email_file} ({len(emails)} emails)")
        print("=" * 80)

if __name__ == "__main__":
    scraper = NancyPortfolioScraper()
    scraper.run()