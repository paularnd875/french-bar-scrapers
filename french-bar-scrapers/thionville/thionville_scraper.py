#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL pour le Barreau de Thionville
Extrait tous les avocats avec leurs informations complètes
Traite correctement la structure NOMPrénom du tableau HTML

Usage:
    python3 thionville_scraper.py [--test] [--headless]
    
Arguments:
    --test      Mode test (10 premiers avocats seulement)
    --headless  Mode sans interface graphique (défaut: True)
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
import argparse
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThionvilleScraper:
    """Scraper pour le Barreau de Thionville"""
    
    def __init__(self, headless=True):
        self.base_url = "https://www.avocats-thionville.fr/"
        
        # URLs avec pagination (format limitstart)
        self.annuaire_urls = [
            "https://www.avocats-thionville.fr/annuaire/userslist/Avocats?limit=15&limitstart=0",
            "https://www.avocats-thionville.fr/annuaire/userslist/Avocats?limit=15&limitstart=15", 
            "https://www.avocats-thionville.fr/annuaire/userslist/Avocats?limit=15&limitstart=30",
            "https://www.avocats-thionville.fr/annuaire/userslist/Avocats?limit=15&limitstart=45"
        ]
        
        # Configuration Selenium
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        
    def init_driver(self):
        """Initialise le driver Selenium"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Driver Chrome initialisé")
        except Exception as e:
            logger.error(f"❌ Erreur driver: {e}")
            raise
    
    def accept_cookies(self):
        """Accepte les cookies si nécessaire"""
        try:
            cookie_selectors = [
                "button[id*='cookie']", "button[class*='cookie']", 
                "button[id*='accept']", "button[class*='accept']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            return True
        except Exception as e:
            return True

    def parse_combined_name(self, combined_text):
        """Parse un texte comme 'MULLERChristian' en nom et prénom séparés"""
        if not combined_text:
            return '', ''
        
        # Nettoyer le texte
        cleaned = combined_text.strip()
        
        # Pattern pour séparer NOMPrénom
        # Le nom est généralement en majuscules, le prénom commence par une majuscule
        patterns = [
            r'^([A-Z]{2,}[A-Z\-]*)\s*([A-Z][a-z\-]+(?:\s*[A-Z][a-z\-]+)*)$',  # MULLERChristian
            r'^([A-Z][A-Z\-]+)\s*([A-Z][a-z\-]+(?:\-[A-Z][a-z\-]+)*)$',        # MARTIN Jean-Pierre
            r'^([A-Z\-]+)\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)$'                   # DUPONT Marie Anne
        ]
        
        for pattern in patterns:
            match = re.match(pattern, cleaned)
            if match:
                nom = match.group(1).strip()
                prenom = match.group(2).strip()
                
                # Vérification que c'est cohérent
                if len(nom) >= 2 and len(prenom) >= 2:
                    return prenom, nom
        
        # Si pas de match, essayer une séparation heuristique
        # Chercher la transition majuscule -> minuscule
        for i in range(1, len(cleaned)):
            if (cleaned[i-1].isupper() and 
                cleaned[i].isupper() and 
                i < len(cleaned) - 1 and 
                cleaned[i+1].islower()):
                
                nom = cleaned[:i+1].strip()
                prenom = cleaned[i+1:].strip()
                
                if len(nom) >= 2 and len(prenom) >= 2:
                    return prenom, nom
        
        # Dernière tentative : séparer sur le premier caractère minuscule après des majuscules
        match = re.match(r'^([A-Z\-]+)([A-Z][a-z].*)$', cleaned)
        if match:
            nom = match.group(1).strip()
            prenom = match.group(2).strip()
            return prenom, nom
        
        # Si rien ne marche, retourner tel quel
        return '', cleaned

    def extract_lawyers_from_page(self, url):
        """Extrait tous les avocats d'une page"""
        logger.info(f"📄 Extraction depuis: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(2)
            self.accept_cookies()
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Trouver le tableau principal (celui avec les avocats)
            main_table = None
            tables = soup.find_all('table')
            
            for table in tables:
                # Chercher un tableau avec des liens userprofile
                links = table.find_all('a', href=True)
                profile_links = [link for link in links if 'userprofile' in link.get('href', '')]
                
                if len(profile_links) > 5:  # Table avec plusieurs avocats
                    main_table = table
                    break
            
            if not main_table:
                logger.warning(f"⚠️ Aucun tableau principal trouvé sur {url}")
                return []
            
            lawyers = []
            rows = main_table.find_all('tr')
            
            # Ignorer la première ligne (en-têtes)
            data_rows = rows[1:] if len(rows) > 1 else rows
            
            for row in data_rows:
                cells = row.find_all('td')
                if len(cells) < 4:  # Doit avoir au moins 4 colonnes
                    continue
                
                # Structure des colonnes: [Date serment, Nom/Prénom, Adresse, Tél/Fax]
                try:
                    date_cell = cells[0]
                    name_cell = cells[1] 
                    address_cell = cells[2]
                    phone_cell = cells[3]
                    
                    # Extraire la date de serment
                    date_serment = date_cell.get_text(strip=True)
                    
                    # Extraire le nom combiné
                    name_text = name_cell.get_text(strip=True)
                    
                    # Extraire l'URL du profil
                    profile_link = name_cell.find('a', href=True)
                    profile_url = ""
                    if profile_link:
                        profile_url = urljoin(self.base_url, profile_link.get('href'))
                    
                    # Parser le nom combiné
                    prenom, nom = self.parse_combined_name(name_text)
                    
                    if not nom and not prenom:
                        continue  # Skip si pas de nom valide
                    
                    # Extraire l'adresse
                    address_text = address_cell.get_text(strip=True)
                    
                    # Extraire téléphone/fax
                    phone_text = phone_cell.get_text(strip=True)
                    
                    # Séparer téléphone et fax
                    telephone, fax = self.parse_phone_fax(phone_text)
                    
                    # Séparer adresse et ville
                    adresse, ville = self.parse_address(address_text)
                    
                    lawyer_info = {
                        'id': len(lawyers) + 1,
                        'prenom': prenom,
                        'nom': nom,
                        'nom_complet': f"{prenom} {nom}".strip(),
                        'date_serment': date_serment,
                        'annee_inscription': self.extract_year_from_date(date_serment),
                        'adresse': adresse,
                        'ville': ville,
                        'telephone': telephone,
                        'fax': fax,
                        'specialisations': '',
                        'competences': '',
                        'structure': '',
                        'email': '',
                        'lien_detail': profile_url,
                        'source': url
                    }
                    
                    lawyers.append(lawyer_info)
                    logger.info(f"  ✅ {len(lawyers)}. {prenom} {nom}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur traitement ligne: {e}")
                    continue
            
            logger.info(f"📊 Page: {len(lawyers)} avocats extraits")
            return lawyers
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction page {url}: {e}")
            return []

    def parse_phone_fax(self, phone_text):
        """Sépare téléphone et fax depuis un texte comme '03.82.53.38.2403.82.51.32.62'"""
        if not phone_text:
            return '', ''
        
        # Chercher des patterns de numéros français
        phone_pattern = r'(0[1-9](?:[.\s]?\d{2}){4})'
        numbers = re.findall(phone_pattern, phone_text)
        
        if len(numbers) >= 2:
            return numbers[0], numbers[1]
        elif len(numbers) == 1:
            return numbers[0], ''
        else:
            return phone_text[:14], phone_text[14:] if len(phone_text) > 14 else ''

    def parse_address(self, address_text):
        """Sépare adresse et ville depuis un texte comme '14 avenue de GaulleTHIONVILLE'"""
        if not address_text:
            return '', ''
        
        # Pattern pour extraire l'adresse et la ville
        # La ville est généralement en majuscules à la fin
        patterns = [
            r'^(.+?)([A-Z]{3,}(?:\s+[A-Z]{3,})*)$',  # Adresse + VILLE
            r'^(.+?)(THIONVILLE)$',  # Cas spécial Thionville
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address_text.strip())
            if match:
                adresse = match.group(1).strip()
                ville = match.group(2).strip()
                return adresse, ville
        
        # Si pas de match, tout est considéré comme adresse
        return address_text, ''

    def extract_year_from_date(self, date_text):
        """Extrait l'année depuis une date comme '12/04/1972'"""
        if not date_text:
            return ''
        
        # Chercher l'année (4 chiffres)
        year_match = re.search(r'(\d{4})', date_text)
        if year_match:
            return year_match.group(1)
        
        return ''

    def extract_all_lawyers(self, test_mode=False):
        """Extrait tous les avocats de toutes les pages"""
        logger.info("🚀 === EXTRACTION BARREAU DE THIONVILLE ===")
        
        if test_mode:
            urls_to_process = [self.annuaire_urls[0]]  # Juste la première page
            logger.info("🧪 Mode TEST: première page seulement")
        else:
            urls_to_process = self.annuaire_urls
            logger.info("🏭 Mode PRODUCTION: toutes les pages")
        
        all_lawyers = []
        
        for i, url in enumerate(urls_to_process):
            try:
                logger.info(f"📋 Page {i+1}/{len(urls_to_process)}")
                page_lawyers = self.extract_lawyers_from_page(url)
                
                # Réajuster les IDs
                for lawyer in page_lawyers:
                    lawyer['id'] = len(all_lawyers) + 1
                    all_lawyers.append(lawyer)
                
                # Pause entre pages
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Erreur page {i+1}: {e}")
                continue
        
        logger.info(f"🎉 Extraction terminée: {len(all_lawyers)} avocats au total")
        return all_lawyers

    def enhance_with_profile_details(self, lawyers_data, limit=None):
        """Enrichit les données en visitant les profils individuels"""
        if limit:
            lawyers_to_process = lawyers_data[:limit]
            logger.info(f"🔍 Enrichissement de {limit} profils (mode test)")
        else:
            lawyers_to_process = lawyers_data
            logger.info(f"🔍 Enrichissement de tous les {len(lawyers_data)} profils")
        
        for i, lawyer in enumerate(lawyers_to_process):
            if not lawyer.get('lien_detail'):
                continue
            
            try:
                logger.info(f"  📖 {i+1}/{len(lawyers_to_process)}: {lawyer['nom_complet']}")
                
                # Visiter le profil
                self.driver.get(lawyer['lien_detail'])
                time.sleep(1)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                text_content = soup.get_text()
                
                # Extraire des informations supplémentaires
                lawyer['email'] = self.extract_email(text_content)
                lawyer['specialisations'] = self.extract_specializations(text_content)
                lawyer['structure'] = self.extract_structure(text_content)
                
                # Mettre à jour les coordonnées si disponibles
                detailed_coords = self.extract_detailed_coordinates(text_content)
                if detailed_coords['adresse']:
                    lawyer.update(detailed_coords)
                
            except Exception as e:
                logger.error(f"❌ Erreur enrichissement {lawyer['nom_complet']}: {e}")
                continue
        
        return lawyers_data

    def extract_email(self, text_content):
        """Extrait l'email depuis le contenu de la page"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(email_pattern, text_content)
        return matches[0] if matches else ''

    def extract_specializations(self, text_content):
        """Extrait les spécialisations"""
        patterns = [
            r'spécialis(?:é|ation)(?:e)?\s*:?\s*([^.\n]+)',
            r'compétence(?:s)?\s*:?\s*([^.\n]+)',
            r'domaine(?:s)?\s*d[\'e]\s*(?:intervention|compétence)\s*:?\s*([^.\n]+)'
        ]
        
        specializations = []
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.I)
            for match in matches[:2]:  # Limiter à 2
                cleaned = match.strip().rstrip(',;.')
                if 5 < len(cleaned) < 100:
                    specializations.append(cleaned)
        
        return '; '.join(specializations)

    def extract_structure(self, text_content):
        """Extrait la structure/cabinet"""
        patterns = [
            r'cabinet\s+([^.\n]+)',
            r'étude\s+([^.\n]+)',
            r'scp\s+([^.\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.I)
            for match in matches:
                cleaned = match.strip().rstrip(',;.')
                if 5 < len(cleaned) < 80:
                    return cleaned
        
        return ''

    def extract_detailed_coordinates(self, text_content):
        """Extrait les coordonnées détaillées depuis la page profil"""
        coords = {'adresse': '', 'ville': '', 'code_postal': ''}
        
        # Chercher le bloc coordonnées
        coord_pattern = r'Coordonnées\s+(.*?)(?=\n\n|\s{3,}|$)'
        match = re.search(coord_pattern, text_content, re.I | re.DOTALL)
        
        if match:
            coord_text = match.group(1)
            
            # Extraire adresse, code postal et ville
            addr_pattern = r'(.+?)\s*-\s*(\d{5})\s+([A-Z\s]+)'
            addr_match = re.search(addr_pattern, coord_text)
            
            if addr_match:
                coords['adresse'] = addr_match.group(1).strip()
                coords['code_postal'] = addr_match.group(2)
                coords['ville'] = addr_match.group(3).strip()
        
        return coords

    def save_results(self, lawyers_data, mode="PRODUCTION"):
        """Sauvegarde finale avec tous les formats"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        total = len(lawyers_data)
        
        if not lawyers_data:
            logger.warning("⚠️ Aucune donnée à sauvegarder")
            return {}
        
        logger.info(f"💾 Sauvegarde de {total} avocats...")
        
        # CSV principal (format le plus important)
        csv_filename = f"THIONVILLE_{mode}_{total}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=lawyers_data[0].keys())
            writer.writeheader()
            writer.writerows(lawyers_data)
        
        # JSON
        json_filename = f"THIONVILLE_{mode}_{total}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, indent=2, ensure_ascii=False)
        
        # Emails uniquement
        emails_filename = f"THIONVILLE_{mode}_EMAILS_{timestamp}.txt"
        emails = set()
        for lawyer in lawyers_data:
            if lawyer.get('email'):
                emails.add(lawyer['email'])
        
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== EMAILS BARREAU THIONVILLE ===\n")
            f.write(f"Total avocats: {total}\n")
            f.write(f"Emails trouvés: {len(emails)}\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for email in sorted(emails):
                f.write(f"{email}\n")
        
        # Rapport final
        report_filename = f"THIONVILLE_{mode}_RAPPORT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT FINAL - BARREAU DE THIONVILLE ===\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode: {mode}\n")
            f.write(f"Total avocats: {total}\n")
            f.write(f"Emails trouvés: {len(emails)}\n")
            f.write(f"Site source: {self.base_url}\n\n")
            
            # Statistiques de qualité
            f.write("=== QUALITÉ DES DONNÉES ===\n")
            stats = {
                'avec_prenom': sum(1 for l in lawyers_data if l.get('prenom')),
                'avec_nom': sum(1 for l in lawyers_data if l.get('nom')),
                'avec_date_serment': sum(1 for l in lawyers_data if l.get('date_serment')),
                'avec_telephone': sum(1 for l in lawyers_data if l.get('telephone')),
                'avec_adresse': sum(1 for l in lawyers_data if l.get('adresse')),
                'avec_email': sum(1 for l in lawyers_data if l.get('email')),
                'avec_specialisations': sum(1 for l in lawyers_data if l.get('specialisations'))
            }
            
            for key, value in stats.items():
                percentage = (value / total * 100) if total > 0 else 0
                f.write(f"{key.replace('_', ' ').title()}: {value}/{total} ({percentage:.1f}%)\n")
            
            # Échantillon
            f.write(f"\n=== ÉCHANTILLON (15 PREMIERS) ===\n")
            for i, lawyer in enumerate(lawyers_data[:15]):
                f.write(f"\n{i+1}. {lawyer['prenom']} {lawyer['nom']}\n")
                f.write(f"   Serment: {lawyer.get('date_serment', 'N/A')}\n")
                f.write(f"   Adresse: {lawyer.get('adresse', 'N/A')}\n")
                f.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\n")
                if lawyer.get('email'):
                    f.write(f"   Email: {lawyer.get('email')}\n")
        
        files = {
            'csv': csv_filename,
            'json': json_filename,
            'emails': emails_filename,
            'report': report_filename
        }
        
        logger.info("✅ === FICHIERS GÉNÉRÉS ===")
        for file_type, filename in files.items():
            logger.info(f"📄 {file_type.upper()}: {filename}")
        
        return files

    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Driver fermé")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Scraper Barreau de Thionville')
    parser.add_argument('--test', action='store_true', help='Mode test (première page seulement)')
    parser.add_argument('--no-headless', action='store_true', help='Mode avec interface graphique')
    parser.add_argument('--no-enrich', action='store_true', help='Pas d\'enrichissement des profils')
    
    args = parser.parse_args()
    
    # Configuration
    test_mode = args.test
    headless_mode = not args.no_headless
    enrich_profiles = not args.no_enrich
    
    logger.info("🎯 === SCRAPER BARREAU DE THIONVILLE ===")
    logger.info(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
    logger.info(f"Interface: {'Headless' if headless_mode else 'Graphique'}")
    logger.info(f"Enrichissement: {'Oui' if enrich_profiles else 'Non'}")
    
    scraper = ThionvilleScraper(headless=headless_mode)
    
    try:
        start_time = time.time()
        scraper.init_driver()
        
        # Extraction de base
        lawyers_data = scraper.extract_all_lawyers(test_mode=test_mode)
        
        if not lawyers_data:
            logger.error("❌ Aucun avocat extrait")
            return False
        
        # Enrichissement avec les profils (optionnel)
        if enrich_profiles:
            limit = 10 if test_mode else None
            lawyers_data = scraper.enhance_with_profile_details(lawyers_data, limit=limit)
        
        # Sauvegarde
        mode = "TEST" if test_mode else "PRODUCTION"
        files = scraper.save_results(lawyers_data, mode=mode)
        
        # Résultats finaux
        elapsed = time.time() - start_time
        logger.info("🎉 === RÉSULTATS FINAUX ===")
        logger.info(f"📊 Avocats extraits: {len(lawyers_data)}")
        logger.info(f"⏱️ Temps total: {elapsed/60:.1f} minutes")
        
        # Qualité des noms
        with_both_names = sum(1 for l in lawyers_data if l.get('prenom') and l.get('nom'))
        logger.info(f"✅ Avocats avec prénom ET nom: {with_both_names}/{len(lawyers_data)}")
        
        # Échantillon
        logger.info("👥 Échantillon des noms extraits:")
        for i, lawyer in enumerate(lawyers_data[:5]):
            logger.info(f"  {i+1}. {lawyer['prenom']} {lawyer['nom']}")
        
        logger.info("🎊 EXTRACTION TERMINÉE AVEC SUCCÈS!")
        return True
        
    except Exception as e:
        logger.error(f"💥 Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        scraper.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)