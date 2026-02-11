#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper CORRIGÉ pour le Barreau de Carpentras
Version finale avec gestion correcte des noms composés et dédoublonnage
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('carpentras_corrige_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CarpentrasScraperCorrigeFinal:
    def __init__(self, headless=True):
        self.base_url = "https://www.barreaudecarpentras.fr/annuaire-des-avocats-de-carpentras"
        self.driver = None
        self.headless = headless
        self.results = []
        self.seen_emails = set()  # Pour éviter les doublons
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Options anti-détection et optimisation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            logger.info("Driver Chrome initialisé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du driver: {e}")
            return False
    
    def accept_cookies(self):
        """Accepter les cookies si nécessaire"""
        try:
            cookie_selectors = [
                "button[id*='cookie']", "button[class*='cookie']",
                "a[id*='cookie']", "a[class*='cookie']",
                ".cookie-accept", "#cookie-accept",
                ".accept-cookies", "#accept-cookies"
            ]
            
            wait = WebDriverWait(self.driver, 3)
            for selector in cookie_selectors:
                try:
                    cookie_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    cookie_btn.click()
                    logger.info(f"Cookies acceptés")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
            logger.info("Aucun bouton de cookies nécessaire")
            return True
            
        except Exception as e:
            logger.warning(f"Erreur cookies: {e}")
            return True
    
    def parse_full_name(self, full_name):
        """
        Parser correctement les noms composés et prénoms
        """
        if not full_name:
            return "", ""
        
        full_name = full_name.strip().upper()
        
        # Gestion des cas spéciaux de noms composés
        special_cases = {
            "DE LEPINAU HERVÉ": ("DE LEPINAU", "HERVÉ"),
            "GROS– LE MAUT ALIX": ("GROS-LE MAUT", "ALIX"),
            "EL AOUADI HAYET": ("EL AOUADI", "HAYET"),
            "ROUGEMONT-PELLET MARIE-HÉLÈNE": ("ROUGEMONT-PELLET", "MARIE-HÉLÈNE"),
            "MILHE-COLOMBAIN CHRISTOPHE": ("MILHE-COLOMBAIN", "CHRISTOPHE"),
            "BRUNEL-BESANCON DOROTHÉE": ("BRUNEL-BESANÇON", "DOROTHÉE"),
            "YASSINE-DBIZA RAJAE": ("YASSINE-DBIZA", "RAJAE"),
            "GOACOLOU-BOREL MORGANE": ("GOACOLOU-BOREL", "MORGANE"),
        }
        
        # Vérifier les cas spéciaux d'abord
        for pattern, (nom, prenom) in special_cases.items():
            if full_name.replace("–", "-").replace(" ", " ") == pattern.replace("–", "-"):
                return nom, prenom
        
        # Patterns pour identifier les particules et préfixes de noms
        particules = ["DE", "DU", "DES", "LA", "LE", "LES", "VAN", "VON", "EL", "AL", "BEN", "ABD", "SAINT", "SAINTE"]
        
        parts = full_name.split()
        if len(parts) < 2:
            return full_name, ""
        
        # Chercher les indices où pourrait se situer la séparation nom/prénom
        for i in range(1, len(parts)):
            potential_nom = " ".join(parts[:i])
            potential_prenom = " ".join(parts[i:])
            
            # Si la partie "nom" contient une particule, on continue
            if any(part in particules for part in parts[:i]):
                continue
            
            # Si on trouve un tiret dans les dernières parties (nom composé complet)
            if "-" in " ".join(parts[:i+1]) and i < len(parts) - 1:
                continue
                
            # Cas standard : le premier mot (ou groupe avec particule) = nom de famille
            if i == 1 or (i == 2 and parts[0] in particules):
                return potential_nom, potential_prenom
        
        # Par défaut : premier mot = nom de famille, reste = prénom
        return parts[0], " ".join(parts[1:])
    
    def is_duplicate_lawyer(self, lawyer_data):
        """
        Vérifier si cet avocat est un doublon
        """
        # Vérification par email unique
        if lawyer_data.get('email'):
            if lawyer_data['email'] in self.seen_emails:
                logger.warning(f"Doublon détecté (email): {lawyer_data['email']}")
                return True
            self.seen_emails.add(lawyer_data['email'])
        
        # Vérification par nom/prénom si pas d'email
        if not lawyer_data.get('email'):
            full_name = f"{lawyer_data.get('nom', '')} {lawyer_data.get('prenom', '')}".strip()
            for existing in self.results:
                existing_name = f"{existing.get('nom', '')} {existing.get('prenom', '')}".strip()
                if full_name == existing_name and full_name:
                    logger.warning(f"Doublon détecté (nom): {full_name}")
                    return True
        
        return False
    
    def extract_lawyer_info(self, lawyer_container):
        """Extraire les informations d'un avocat avec gestion améliorée"""
        lawyer_data = {
            'nom': '', 'prenom': '', 'email': '', 'telephone': '', 'fax': '',
            'adresse': '', 'ville': '', 'annee_inscription': '',
            'specialisations': [], 'structure': '', 'site_web': ''
        }
        
        try:
            # Extraction du nom depuis h2 avec parsing amélioré
            try:
                name_element = lawyer_container.find_element(By.CSS_SELECTOR, "h2.eb-post-title a")
                full_name = name_element.text.strip()
                
                # Parser correctement le nom
                nom, prenom = self.parse_full_name(full_name)
                lawyer_data['nom'] = nom
                lawyer_data['prenom'] = prenom
                
                logger.debug(f"Nom parsé: '{full_name}' -> Nom: '{nom}', Prénom: '{prenom}'")
                
            except NoSuchElementException:
                # Fallback
                container_text = lawyer_container.text.split('\n')[0] if lawyer_container.text else ""
                if container_text:
                    nom, prenom = self.parse_full_name(container_text.strip())
                    lawyer_data['nom'] = nom
                    lawyer_data['prenom'] = prenom
            
            # Extraction email (nettoyage amélioré)
            try:
                email_element = lawyer_container.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                email = email_element.get_attribute('href').replace('mailto:', '').strip()
                # Nettoyer l'email de caractères indésirables
                email = re.sub(r'[^\w\.-@]', '', email)
                if '@' in email and '.' in email:
                    lawyer_data['email'] = email
            except NoSuchElementException:
                pass
            
            # Extraction informations depuis le tableau (inchangé)
            try:
                table = lawyer_container.find_element(By.CSS_SELECTOR, "table.table-bordered")
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 2:
                            label = cells[0].text.strip().lower()
                            value = cells[1].text.strip()
                            
                            if 'adresse' in label:
                                lawyer_data['adresse'] = value
                                if 'à ' in value:
                                    lawyer_data['ville'] = value.split('à ')[-1].strip()
                                    
                            elif 'coordonnées' in label or 'téléphone' in label:
                                # Extraire téléphone
                                phone_match = re.search(r'(?:tél\.?|téléphone)\s*:?\s*([\d\.\s\-]{10,})', value, re.IGNORECASE)
                                if phone_match:
                                    lawyer_data['telephone'] = phone_match.group(1).strip()
                                
                                # Extraire fax
                                fax_match = re.search(r'fax\s*:?\s*([\d\.\s\-]{10,})', value, re.IGNORECASE)
                                if fax_match:
                                    lawyer_data['fax'] = fax_match.group(1).strip()
                                
                                # Email si pas encore trouvé
                                if not lawyer_data['email']:
                                    email_match = re.search(r'([\w\.-]+@[\w\.-]+\.\w+)', value)
                                    if email_match:
                                        lawyer_data['email'] = email_match.group(1)
                                        
                            elif 'site' in label:
                                try:
                                    link_element = cells[1].find_element(By.TAG_NAME, "a")
                                    lawyer_data['site_web'] = link_element.get_attribute('href')
                                except NoSuchElementException:
                                    if 'http' in value:
                                        lawyer_data['site_web'] = value.strip()
                                        
                    except Exception:
                        continue
                        
            except NoSuchElementException:
                pass
            
            # Extraction année d'inscription (inchangé)
            try:
                full_text = lawyer_container.text
                year_patterns = [
                    r'(?:serment|prestation)\s*:?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.](\d{4}))',
                    r'(?:inscription|admis).*?(\d{4})',
                    r'(\d{4})',
                ]
                
                for pattern in year_patterns:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        year = match.group(2) if match.lastindex >= 2 else match.group(1)
                        if year.isdigit() and 1950 <= int(year) <= 2030:
                            lawyer_data['annee_inscription'] = year
                            break
                    if lawyer_data['annee_inscription']:
                        break
                        
            except Exception:
                pass
            
            # Extraction spécialisations (inchangé)
            try:
                full_text = lawyer_container.text
                special_mentions = [
                    r'(ANCIEN BATONNIER|ANCIEN BÂTONNIER)',
                    r'(BATONNIER|BÂTONNIER)',
                    r'(ANCIEN MEMBRE DU CONSEIL)',
                    r'(MEMBRE DU CONSEIL)',
                    r'(SPECIALISTE|SPÉCIALISTE).*?([A-ZÀ-Ü][a-zà-ü\s]+)',
                ]
                
                for pattern in special_mentions:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        specialisation = match.group(0).strip()
                        if specialisation and specialisation not in lawyer_data['specialisations']:
                            lawyer_data['specialisations'].append(specialisation)
                            
            except Exception:
                pass
            
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur extraction avocat: {e}")
            return lawyer_data
    
    def scrape_all_lawyers(self):
        """Scraper tous les avocats avec dédoublonnage"""
        try:
            logger.info(f"🚀 DÉBUT EXTRACTION CORRIGÉE - {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            self.accept_cookies()
            time.sleep(1)
            
            # Attendre et récupérer les conteneurs
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".eb-post-content")))
            lawyer_containers = self.driver.find_elements(By.CSS_SELECTOR, ".eb-post-content")
            
            total_lawyers = len(lawyer_containers)
            logger.info(f"📊 {total_lawyers} conteneurs trouvés")
            
            if not lawyer_containers:
                logger.error("❌ Aucun avocat trouvé")
                return False
            
            # Extraction avec dédoublonnage
            successful_extractions = 0
            duplicates_skipped = 0
            
            for i, container in enumerate(lawyer_containers):
                try:
                    # Affichage du progrès
                    if i % 10 == 0 or i == total_lawyers - 1:
                        progress = ((i + 1) / total_lawyers) * 100
                        logger.info(f"📈 Progrès: {i+1}/{total_lawyers} ({progress:.1f}%) - Extraits: {successful_extractions}, Doublons: {duplicates_skipped}")
                    
                    lawyer_data = self.extract_lawyer_info(container)
                    
                    # Validation et vérification des doublons
                    if lawyer_data['nom'] or lawyer_data['email']:
                        if not self.is_duplicate_lawyer(lawyer_data):
                            self.results.append(lawyer_data)
                            successful_extractions += 1
                        else:
                            duplicates_skipped += 1
                    else:
                        logger.debug(f"⚠️ Avocat {i+1} - données insuffisantes")
                    
                    # Pause courte entre extractions
                    time.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur avocat {i+1}: {e}")
                    continue
            
            logger.info(f"🎉 Extraction terminée:")
            logger.info(f"   ✅ {successful_extractions} avocats uniques extraits")
            logger.info(f"   🔄 {duplicates_skipped} doublons évités")
            logger.info(f"   📊 {len(set(self.seen_emails))} emails uniques")
            
            return successful_extractions > 0
            
        except Exception as e:
            logger.error(f"💥 Erreur pendant le scraping: {e}")
            return False
    
    def save_results(self):
        """Sauvegarder tous les résultats avec dédoublonnage final"""
        if not self.results:
            logger.warning("⚠️ Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Dédoublonnage final par email ET nom complet
        final_results = []
        seen_identifiers = set()
        
        for lawyer in self.results:
            # Créer un identifiant unique
            if lawyer.get('email'):
                identifier = lawyer['email'].lower()
            else:
                identifier = f"{lawyer.get('nom', '')}_{lawyer.get('prenom', '')}".lower().replace(' ', '_')
            
            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                final_results.append(lawyer)
            else:
                logger.debug(f"Doublon final évité: {identifier}")
        
        self.results = final_results
        
        # JSON complet
        json_file = f"carpentras_CORRIGE_FINAL_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # CSV complet
        csv_file = f"carpentras_CORRIGE_FINAL_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['nom', 'prenom', 'email', 'telephone', 'fax', 'adresse', 
                         'ville', 'annee_inscription', 'specialisations', 'site_web']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                result_copy = result.copy()
                result_copy['specialisations'] = '; '.join(result.get('specialisations', []))
                writer.writerow(result_copy)
        
        # Emails uniques uniquement
        unique_emails = sorted(set([r['email'] for r in self.results if r.get('email')]))
        emails_file = f"carpentras_EMAILS_UNIQUES_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_emails))
        
        # Rapport détaillé
        rapport_file = f"carpentras_RAPPORT_CORRIGE_{timestamp}.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("RAPPORT EXTRACTION CARPENTRAS - VERSION CORRIGÉE\n")
            f.write("="*70 + "\n")
            f.write(f"Date extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"URL: {self.base_url}\n\n")
            
            f.write("CORRECTIONS APPORTÉES:\n")
            f.write("- ✅ Gestion correcte des noms composés (DE LEPINAU, GROS-LE MAUT, etc.)\n")
            f.write("- ✅ Séparation améliorée nom/prénom\n")
            f.write("- ✅ Dédoublonnage par email et nom complet\n")
            f.write("- ✅ Nettoyage des emails\n\n")
            
            f.write("STATISTIQUES FINALES:\n")
            f.write(f"- Total avocats uniques: {len(self.results)}\n")
            f.write(f"- Emails uniques: {len(unique_emails)}\n")
            f.write(f"- Téléphones: {len([a for a in self.results if a.get('telephone')])}\n")
            f.write(f"- Années inscription: {len([a for a in self.results if a.get('annee_inscription')])}\n")
            
            # Exemples de noms corrigés
            f.write("\nEXEMPLES DE NOMS CORRIGÉS:\n")
            f.write("-" * 40 + "\n")
            examples = [r for r in self.results if any(x in r.get('nom', '') for x in ['DE ', 'EL ', 'GROS', 'ROUGEMONT'])]
            for i, lawyer in enumerate(examples[:5], 1):
                f.write(f"{i}. {lawyer.get('nom', '')} {lawyer.get('prenom', '')}\n")
                if lawyer.get('email'):
                    f.write(f"   Email: {lawyer['email']}\n")
        
        # Affichage console
        print(f"\n🎉 EXTRACTION CARPENTRAS CORRIGÉE TERMINÉE 🎉")
        print(f"=" * 55)
        print(f"📊 {len(self.results)} avocats uniques (après dédoublonnage)")
        print(f"📧 {len(unique_emails)} emails uniques")
        print(f"🏷️ Noms composés correctement gérés")
        print(f"\n📁 Fichiers corrigés:")
        print(f"   ✅ {json_file}")
        print(f"   ✅ {csv_file}")
        print(f"   ✅ {emails_file}")
        print(f"   ✅ {rapport_file}")
        
        logger.info(f"💾 Tous les fichiers corrigés sauvegardés")
    
    def run_production(self):
        """Lancer l'extraction complète corrigée"""
        logger.info("🚀 === DÉBUT EXTRACTION CORRIGÉE CARPENTRAS ===")
        start_time = time.time()
        
        if not self.setup_driver():
            logger.error("💥 Impossible d'initialiser le driver")
            return False
        
        try:
            success = self.scrape_all_lawyers()
            
            if success:
                self.save_results()
                duration = time.time() - start_time
                logger.info(f"✅ === EXTRACTION CORRIGÉE RÉUSSIE en {duration:.1f}s ===")
                return True
            else:
                logger.error("❌ === EXTRACTION CORRIGÉE ÉCHOUÉE ===")
                return False
                
        except Exception as e:
            logger.error(f"💥 Erreur pendant l'extraction: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔒 Driver fermé")

if __name__ == "__main__":
    print("🏛️  SCRAPER CARPENTRAS - VERSION CORRIGÉE FINALE")
    print("=" * 60)
    print("🔧 Corrections:")
    print("   ✅ Gestion correcte des noms composés")
    print("   ✅ Dédoublonnage par email")
    print("   ✅ Parsing amélioré nom/prénom")
    print("   ⚡ Mode headless (sans interface)")
    print()
    
    scraper = CarpentrasScraperCorrigeFinal(headless=True)
    success = scraper.run_production()
    
    if success:
        print("\n🎊 SUCCÈS! Extraction corrigée terminée.")
        print("📋 Consultez les fichiers CORRIGE_FINAL pour les résultats.")
    else:
        print("\n💥 ÉCHEC! Consultez carpentras_corrige_final.log")