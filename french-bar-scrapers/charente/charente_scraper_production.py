#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper COMPLET pour tous les avocats du Barreau de Charente
Version production basée sur le test validé à 100%
"""

import time
import json
import csv
import re
import html
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CharenteCompletScraper:
    def __init__(self, headless=True):
        self.base_url = "https://www.avocats-charente.com/annuaire-des-avocats"
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        self.total_pages = 9  # 132 avocats répartis sur 9 pages
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Driver Chrome configuré avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la configuration du driver: {e}")
            raise
    
    def accept_cookies(self):
        """Accepter les cookies"""
        try:
            time.sleep(3)
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    button_text = button.text.lower()
                    if any(word in button_text for word in ['accepter', 'accept', 'ok', 'continuer']):
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            time.sleep(2)
                            logger.info("Cookies acceptés")
                            return True
                except Exception:
                    continue
            return False
        except Exception as e:
            logger.error(f"Erreur cookies: {e}")
            return False
    
    def navigate_to_page(self, page_num):
        """Naviguer vers une page spécifique"""
        try:
            if page_num == 1:
                self.driver.get(self.base_url)
            else:
                page_url = f"{self.base_url}?limitstart={(page_num-1)*15}"
                self.driver.get(page_url)
            
            time.sleep(5)
            
            if page_num == 1:
                self.accept_cookies()
                time.sleep(3)
            
            logger.info(f"Navigué vers la page {page_num}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur navigation page {page_num}: {e}")
            return False
    
    def collect_basic_info_from_page(self, page_num):
        """Collecter les infos de base d'une page"""
        try:
            logger.info(f"=== COLLECTE PAGE {page_num} ===")
            
            # Naviguer vers la page
            if not self.navigate_to_page(page_num):
                return []
            
            # Extraire les cartes des avocats
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".cbUserListRow")
            
            if not cards:
                logger.warning(f"Aucune carte d'avocat trouvée page {page_num}")
                return []
            
            logger.info(f"Trouvé {len(cards)} avocats sur la page {page_num}")
            
            # Collecter les infos de base
            lawyers_basic = []
            for i, card in enumerate(cards):
                try:
                    lawyer_data = {}
                    
                    # Prénom et nom
                    col1 = card.find_element(By.CSS_SELECTOR, ".cbUserListRowCol1")
                    prenom_element = col1.find_element(By.CSS_SELECTOR, ".cbUserListFC_firstname a")
                    nom_element = col1.find_element(By.CSS_SELECTOR, ".cbUserListFC_lastname a")
                    
                    lawyer_data['prenom'] = prenom_element.text.strip()
                    lawyer_data['nom'] = nom_element.text.strip()
                    lawyer_data['nom_complet'] = f"{lawyer_data['prenom']} {lawyer_data['nom']}"
                    lawyer_data['url_profil'] = prenom_element.get_attribute('href')
                    
                    # Adresse
                    col2 = card.find_element(By.CSS_SELECTOR, ".cbUserListRowCol2")
                    try:
                        lawyer_data['code_postal'] = col2.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_codepostal").text.strip()
                    except:
                        lawyer_data['code_postal'] = ''
                    
                    try:
                        lawyer_data['ville'] = col2.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_ville").text.strip()
                    except:
                        lawyer_data['ville'] = ''
                    
                    try:
                        lawyer_data['adresse'] = col2.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_adresse1").text.strip()
                    except:
                        lawyer_data['adresse'] = ''
                    
                    # Téléphone
                    col3 = card.find_element(By.CSS_SELECTOR, ".cbUserListRowCol3")
                    try:
                        lawyer_data['telephone'] = col3.find_element(By.CSS_SELECTOR, ".cbUserListFC_cb_telephone").text.strip()
                    except:
                        lawyer_data['telephone'] = ''
                    
                    # Spécialités
                    col4 = card.find_element(By.CSS_SELECTOR, ".cbUserListRowCol4")
                    lawyer_data['specialites'] = col4.text.strip()
                    
                    lawyers_basic.append(lawyer_data)
                    logger.info(f"Page {page_num} - Avocat {i+1}/{len(cards)}: {lawyer_data['nom_complet']}")
                    
                except Exception as e:
                    logger.error(f"Erreur extraction avocat {i+1} page {page_num}: {e}")
                    continue
            
            logger.info(f"Page {page_num} - Collecté {len(lawyers_basic)} avocats")
            return lawyers_basic
            
        except Exception as e:
            logger.error(f"Erreur collecte page {page_num}: {e}")
            return []
    
    def extract_all_emails_from_profile(self, profile_url, lawyer_name):
        """Extraire TOUS les emails d'une page de profil - méthode validée"""
        try:
            # Aller sur la page de profil
            self.driver.get(profile_url)
            time.sleep(4)
            
            emails_found = []
            
            # Méthode 1: Liens mailto directs
            mailto_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
            for link in mailto_links:
                href = link.get_attribute('href')
                email = href.replace('mailto:', '').strip()
                if email and email not in emails_found:
                    emails_found.append(email)
            
            # Méthode 2: Analyse du code source pour déobfuscation
            page_source = self.driver.page_source
            
            # Pattern pour emails obfusqués dans le JavaScript
            js_email_patterns = [
                r"var\s+addy\d*\s*=\s*['\"]([^'\"]+)['\"]",
                r"addy\d*\s*=\s*['\"]([^'\"]+)['\"]",
                r"['\"]([a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]*)['\"]",
            ]
            
            for pattern in js_email_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    # Déobfusquer les entités HTML
                    decoded_email = html.unescape(match)
                    # Vérifier si c'est un email valide
                    if re.match(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", decoded_email):
                        if decoded_email not in emails_found:
                            emails_found.append(decoded_email)
            
            # Méthode 3: Recherche dans le texte visible (après JavaScript)
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(2)
                
                # Chercher tous les éléments contenant @
                elements_with_at = self.driver.find_elements(By.XPATH, "//*[contains(text(), '@')]")
                for elem in elements_with_at:
                    text = elem.text.strip()
                    email_matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
                    for email in email_matches:
                        if email not in emails_found:
                            emails_found.append(email)
                            
            except Exception as e:
                logger.warning(f"Erreur recherche texte visible: {e}")
            
            # Méthode 4: Éléments cloak
            try:
                cloak_elements = self.driver.find_elements(By.CSS_SELECTOR, "[id*='cloak']")
                for elem in cloak_elements:
                    try:
                        self.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(1)
                        text = elem.text.strip()
                        email_matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
                        for email in email_matches:
                            if email not in emails_found:
                                emails_found.append(email)
                    except:
                        pass
            except Exception as e:
                logger.warning(f"Erreur éléments cloak: {e}")
            
            # Méthode 5: Regex avancée sur le code source
            advanced_patterns = [
                r"([a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,})",
                r"([a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,})",
            ]
            
            for pattern in advanced_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for email in matches:
                    email = re.sub(r'\s+', '', email)
                    if email and email not in emails_found:
                        emails_found.append(email)
            
            # Filtrer et nettoyer
            valid_emails = []
            for email in emails_found:
                email = email.strip().lower()
                if (email and 
                    '@' in email and 
                    '.' in email and 
                    not email.startswith('noreply') and
                    not email.startswith('no-reply') and
                    not 'example' in email and
                    not 'test' in email and
                    len(email) > 5):
                    valid_emails.append(email)
            
            # Supprimer les doublons
            final_emails = []
            for email in valid_emails:
                if email not in final_emails:
                    final_emails.append(email)
            
            return final_emails
            
        except Exception as e:
            logger.error(f"Erreur extraction emails pour {lawyer_name}: {e}")
            return []
    
    def scrape_all_lawyers(self):
        """Scraper complet de tous les avocats"""
        try:
            logger.info("=== DÉBUT SCRAPING COMPLET - 132 AVOCATS ===")
            
            # Étape 1: Collecter toutes les infos de base page par page
            all_lawyers_basic = []
            
            for page in range(1, self.total_pages + 1):
                logger.info(f"\n=== TRAITEMENT PAGE {page}/{self.total_pages} ===")
                
                page_lawyers = self.collect_basic_info_from_page(page)
                if page_lawyers:
                    all_lawyers_basic.extend(page_lawyers)
                    logger.info(f"Page {page} terminée: {len(page_lawyers)} avocats collectés")
                    
                    # Sauvegarde intermédiaire
                    if page % 3 == 0:  # Toutes les 3 pages
                        self.save_intermediate_backup(all_lawyers_basic, f"partial_p{page}")
                else:
                    logger.warning(f"Aucun avocat collecté page {page}")
                
                # Délai entre les pages
                time.sleep(3)
            
            logger.info(f"=== COLLECTE TERMINÉE: {len(all_lawyers_basic)} AVOCATS ===")
            
            # Étape 2: Enrichir avec les emails
            logger.info(f"\n=== EXTRACTION DES EMAILS ===")
            
            for i, lawyer in enumerate(all_lawyers_basic):
                try:
                    logger.info(f"\n--- Avocat {i+1}/{len(all_lawyers_basic)}: {lawyer['nom_complet']} ---")
                    
                    if lawyer.get('url_profil'):
                        emails = self.extract_all_emails_from_profile(lawyer['url_profil'], lawyer['nom_complet'])
                        
                        # Séparer les types d'emails
                        email_personnel = ''
                        email_generique = ''
                        autres_emails = []
                        
                        for email in emails:
                            if 'avocats-charente.com' in email:
                                email_generique = email
                            elif email:
                                if not email_personnel:
                                    email_personnel = email
                                else:
                                    autres_emails.append(email)
                        
                        lawyer['email_personnel'] = email_personnel
                        lawyer['email_generique'] = email_generique  
                        lawyer['autres_emails'] = ', '.join(autres_emails) if autres_emails else ''
                        lawyer['total_emails_trouves'] = len(emails)
                        
                        # Log des résultats
                        if email_personnel:
                            logger.info(f"  ✓ Email personnel: {email_personnel}")
                        else:
                            logger.info(f"  ✗ Aucun email personnel trouvé")
                        
                        if email_generique:
                            logger.info(f"  ✓ Email générique: {email_generique}")
                        
                    else:
                        logger.warning(f"  ✗ Pas d'URL de profil pour {lawyer['nom_complet']}")
                        lawyer['email_personnel'] = ''
                        lawyer['email_generique'] = ''
                        lawyer['autres_emails'] = ''
                        lawyer['total_emails_trouves'] = 0
                    
                    self.lawyers_data.append(lawyer)
                    
                    # Sauvegarde intermédiaire tous les 25 avocats
                    if (i + 1) % 25 == 0:
                        self.save_intermediate_backup(self.lawyers_data, f"partial_{i+1}")
                    
                    # Délai respectueux
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Erreur traitement avocat {i+1} ({lawyer.get('nom_complet', 'Inconnu')}): {e}")
                    continue
            
            return self.lawyers_data
            
        except Exception as e:
            logger.error(f"Erreur scraping complet: {e}")
            return self.lawyers_data
    
    def save_intermediate_backup(self, data, suffix):
        """Sauvegarder une copie intermédiaire"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"charente_{suffix}_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Sauvegarde intermédiaire: {filename}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde intermédiaire: {e}")
    
    def save_final_results(self):
        """Sauvegarder les résultats finaux"""
        if not self.lawyers_data:
            logger.error("Aucune donnée à sauvegarder")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_filename = f"charente_COMPLET_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = f"charente_COMPLET_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = self.lawyers_data[0].keys()
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # CSV emails seulement
        emails_csv = f"charente_EMAILS_COMPLET_{timestamp}.csv"
        with open(emails_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email_personnel', 'nom_complet', 'ville', 'telephone'])
            for lawyer in self.lawyers_data:
                if lawyer.get('email_personnel'):
                    writer.writerow([
                        lawyer['email_personnel'], 
                        lawyer['nom_complet'], 
                        lawyer.get('ville', ''), 
                        lawyer.get('telephone', '')
                    ])
        
        # Fichier emails uniquement (txt)
        emails_txt = f"charente_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_txt, 'w', encoding='utf-8') as f:
            f.write("EMAILS PERSONNELS - BARREAU DE CHARENTE\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for lawyer in self.lawyers_data:
                if lawyer.get('email_personnel'):
                    f.write(f"{lawyer['email_personnel']} - {lawyer['nom_complet']}\n")
        
        # Rapport complet
        report_filename = f"charente_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT EXTRACTION COMPLÈTE - BARREAU DE CHARENTE\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 60 + "\n\n")
            
            # Statistiques globales
            total = len(self.lawyers_data)
            with_personal = sum(1 for l in self.lawyers_data if l.get('email_personnel'))
            with_generic = sum(1 for l in self.lawyers_data if l.get('email_generique'))
            with_phone = sum(1 for l in self.lawyers_data if l.get('telephone'))
            
            f.write("STATISTIQUES GLOBALES:\n")
            f.write(f"- Total avocats extraits: {total}\n")
            f.write(f"- Avec email personnel: {with_personal} ({with_personal/total*100:.1f}%)\n")
            f.write(f"- Avec email générique: {with_generic} ({with_generic/total*100:.1f}%)\n")
            f.write(f"- Avec téléphone: {with_phone} ({with_phone/total*100:.1f}%)\n")
            f.write(f"- Taux de réussite emails personnels: {with_personal/total*100:.1f}%\n\n")
            
            # Répartition par ville
            villes = {}
            for lawyer in self.lawyers_data:
                ville = lawyer.get('ville', 'Non spécifiée')
                villes[ville] = villes.get(ville, 0) + 1
            
            f.write("RÉPARTITION PAR VILLE:\n")
            for ville, count in sorted(villes.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- {ville}: {count} avocats\n")
            f.write("\n")
            
            # Liste des emails personnels
            f.write("EMAILS PERSONNELS TROUVÉS:\n")
            f.write("-" * 40 + "\n")
            for lawyer in self.lawyers_data:
                if lawyer.get('email_personnel'):
                    f.write(f"{lawyer['email_personnel']} - {lawyer['nom_complet']}\n")
            f.write(f"\nTotal: {with_personal} emails personnels\n")
        
        logger.info(f"Résultats finaux sauvegardés:")
        logger.info(f"  - JSON complet: {json_filename}")
        logger.info(f"  - CSV complet: {csv_filename}")
        logger.info(f"  - Emails CSV: {emails_csv}")
        logger.info(f"  - Emails TXT: {emails_txt}")
        logger.info(f"  - Rapport: {report_filename}")
        
        return {
            'json': json_filename,
            'csv': csv_filename,
            'emails_csv': emails_csv,
            'emails_txt': emails_txt,
            'report': report_filename,
            'stats': {
                'total': total,
                'emails_personnels': with_personal,
                'emails_generiques': with_generic,
                'taux_reussite': with_personal/total*100 if total > 0 else 0
            }
        }
    
    def close(self):
        if self.driver:
            self.driver.quit()

def main():
    print("=== SCRAPER PRODUCTION - BARREAU DE CHARENTE ===")
    print("Extraction complète de tous les avocats (132 avocats sur 9 pages)")
    print("=" * 60)
    
    headless = input("Mode headless? (y/n, défaut=y): ").strip().lower() != 'n'
    
    confirm = input("Lancer l'extraction complète? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Extraction annulée.")
        return
    
    scraper = CharenteCompletScraper(headless=headless)
    
    try:
        start_time = datetime.now()
        print(f"Début de l'extraction: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        scraper.setup_driver()
        lawyers = scraper.scrape_all_lawyers()
        
        if lawyers:
            files = scraper.save_final_results()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print(f"\n" + "="*60)
            print(f"EXTRACTION COMPLÈTE TERMINÉE !")
            print(f"="*60)
            print(f"✓ Durée totale: {duration}")
            print(f"✓ Total avocats extraits: {files['stats']['total']}")
            print(f"✓ Emails personnels trouvés: {files['stats']['emails_personnels']}")
            print(f"✓ Emails génériques trouvés: {files['stats']['emails_generiques']}")
            print(f"✓ Taux de réussite emails personnels: {files['stats']['taux_reussite']:.1f}%")
            print(f"="*60)
            
            print(f"\nFichiers générés:")
            print(f"  📄 Rapport complet: {files['report']}")
            print(f"  📊 Données JSON: {files['json']}")
            print(f"  📊 Données CSV: {files['csv']}")
            print(f"  📧 Emails CSV: {files['emails_csv']}")
            print(f"  📧 Emails TXT: {files['emails_txt']}")
            
        else:
            print("❌ Aucun avocat extrait.")
    
    except KeyboardInterrupt:
        print("\n⚠️  Extraction interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        scraper.close()
        print("Driver fermé.")

if __name__ == "__main__":
    main()