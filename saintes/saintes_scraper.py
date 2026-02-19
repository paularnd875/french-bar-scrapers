#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper complet pour le Barreau de Saintes
Site: https://www.avocats-saintes.com/annuaire-des-avocats.html

Ce script extrait tous les avocats de l'annuaire avec pagination automatique.
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from urllib.parse import urljoin

class SaintesLawyerScraper:
    def __init__(self, headless=True):
        self.base_url = "https://www.avocats-saintes.com"
        self.directory_url = "https://www.avocats-saintes.com/annuaire-des-avocats.html"
        self.lawyers = []
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
        
    def accept_cookies(self):
        """Accepter les cookies si nécessaire"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    "[data-accept-cookies], .cookie-accept, #cookie-accept, .accept-cookies"))
            )
            cookie_button.click()
            print("✅ Cookies acceptés")
            time.sleep(1)
        except TimeoutException:
            print("ℹ️ Pas de bannière de cookies détectée")
    
    def navigate_to_page(self, page_num):
        """Naviguer vers une page spécifique de l'annuaire"""
        if page_num == 1:
            url = self.directory_url
        else:
            start = (page_num - 1) * 22
            url = f"{self.directory_url}?start={start}"
        
        print(f"📄 Navigation vers la page {page_num}: {url}")
        self.driver.get(url)
        time.sleep(2)
        
        if page_num == 1:
            self.accept_cookies()
        
        return url
    
    def extract_lawyers_from_page(self, page_num):
        """Extraire tous les avocats d'une page"""
        page_lawyers = []
        
        try:
            # Attendre que la liste se charge
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".item-page"))
            )
            
            # Trouver tous les liens d'avocats
            lawyer_links = self.driver.find_elements(By.CSS_SELECTOR, "h2 a[href*='avocat']")
            
            print(f"📋 Trouvé {len(lawyer_links)} avocats sur la page {page_num}")
            
            for i, link in enumerate(lawyer_links):
                try:
                    lawyer_url = link.get_attribute('href')
                    lawyer_name = link.text.strip()
                    
                    print(f"   {i+1}. Extraction: {lawyer_name}")
                    
                    # Extraire les détails de cet avocat
                    lawyer_data = self.extract_lawyer_details(lawyer_url, lawyer_name)
                    if lawyer_data:
                        page_lawyers.append(lawyer_data)
                    
                    time.sleep(1)  # Politesse
                    
                except Exception as e:
                    print(f"❌ Erreur lors de l'extraction de l'avocat {i+1}: {e}")
                    continue
        
        except TimeoutException:
            print(f"❌ Timeout sur la page {page_num}")
        
        return page_lawyers
    
    def extract_lawyer_details(self, lawyer_url, lawyer_name):
        """Extraire les détails d'un avocat spécifique"""
        try:
            # Ouvrir la page de l'avocat dans un nouvel onglet
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(lawyer_url)
            
            time.sleep(2)
            
            # Initialiser les données
            lawyer_data = {
                'nom_complet': lawyer_name,
                'prenom': '',
                'nom': '',
                'url': lawyer_url,
                'specialisations': '',
                'structure': '',
                'date_inscription': '',
                'emails': ''
            }
            
            # Séparer prénom et nom
            name_parts = lawyer_name.split()
            if len(name_parts) >= 2:
                lawyer_data['nom'] = name_parts[-1]  # Dernier mot = nom
                lawyer_data['prenom'] = ' '.join(name_parts[:-1])  # Reste = prénom
            
            # Extraire spécialisations
            try:
                specializations = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".field-name-field-specialisation .field-item, .specialisation, .field-specialisation")
                if specializations:
                    specs = [spec.text.strip() for spec in specializations if spec.text.strip()]
                    lawyer_data['specialisations'] = '; '.join(specs)
            except:
                pass
            
            # Extraire structure/cabinet
            try:
                structure_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    ".field-name-field-structure .field-item, .structure, .cabinet")
                lawyer_data['structure'] = structure_elem.text.strip()
            except:
                pass
            
            # Extraire date d'inscription
            try:
                date_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    ".field-name-field-date-inscription .field-item, .date-inscription")
                lawyer_data['date_inscription'] = date_elem.text.strip()
            except:
                pass
            
            # Extraire emails depuis le HTML de la page
            page_source = self.driver.page_source
            emails = self.extract_emails_from_html(page_source)
            if emails:
                lawyer_data['emails'] = '; '.join(emails)
            
            # Fermer l'onglet et revenir à l'annuaire
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des détails: {e}")
            # S'assurer de fermer l'onglet en cas d'erreur
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return None
    
    def extract_emails_from_html(self, html_content):
        """Extraire les emails du contenu HTML"""
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}'
        ]
        
        found_emails = set()
        for pattern in email_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    found_emails.add(match[0])
                else:
                    found_emails.add(match)
        
        # Filtrer les emails invalides
        valid_emails = []
        for email in found_emails:
            email = email.strip()
            if email and '@' in email and '.' in email.split('@')[-1]:
                # Exclure les emails génériques connus
                if email != 'biblibarreau@orange.fr':
                    valid_emails.append(email)
        
        return sorted(valid_emails)
    
    def scrape_all_pages(self, max_pages=6):
        """Scraper toutes les pages de l'annuaire"""
        print("🚀 Démarrage du scraping complet...")
        
        self.setup_driver()
        
        try:
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 === PAGE {page_num} ===")
                
                self.navigate_to_page(page_num)
                page_lawyers = self.extract_lawyers_from_page(page_num)
                
                if not page_lawyers:
                    print(f"🏁 Aucun avocat trouvé sur la page {page_num}, arrêt du scraping")
                    break
                
                self.lawyers.extend(page_lawyers)
                print(f"✅ Page {page_num}: {len(page_lawyers)} avocats extraits")
                print(f"📊 Total cumulé: {len(self.lawyers)} avocats")
                
                # Backup intermédiaire
                if len(self.lawyers) % 50 == 0:
                    self.save_backup()
        
        finally:
            if self.driver:
                self.driver.quit()
        
        print(f"\n🎉 Scraping terminé! Total: {len(self.lawyers)} avocats extraits")
        return self.lawyers
    
    def save_backup(self):
        """Sauvegarder les données en cours"""
        timestamp = datetime.now().strftime("%H%M%S")
        backup_file = f"backup_{len(self.lawyers)}_avocats_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
        print(f"💾 Backup: {backup_file}")
    
    def save_results(self, base_filename="SAINTES_COMPLET"):
        """Sauvegarder les résultats finaux"""
        if not self.lawyers:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_file = f"{base_filename}_{len(self.lawyers)}_avocats_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.lawyers:
                writer = csv.DictWriter(f, fieldnames=self.lawyers[0].keys())
                writer.writeheader()
                writer.writerows(self.lawyers)
        
        # JSON
        json_file = f"{base_filename}_{len(self.lawyers)}_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        all_emails = []
        for lawyer in self.lawyers:
            if lawyer.get('emails'):
                emails = [e.strip() for e in lawyer['emails'].split(';')]
                all_emails.extend(emails)
        
        unique_emails = sorted(list(set(all_emails)))
        if unique_emails:
            emails_file = f"{base_filename}_EMAILS_{len(unique_emails)}uniques_{timestamp}.txt"
            with open(emails_file, 'w', encoding='utf-8') as f:
                for email in unique_emails:
                    f.write(email + '\n')
        
        # Rapport
        report_file = f"{base_filename}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT DE SCRAPING - BARREAU DE SAINTES - {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"RÉSULTATS:\n")
            f.write(f"- Total avocats: {len(self.lawyers)}\n")
            f.write(f"- Emails uniques trouvés: {len(unique_emails)}\n")
            f.write(f"- Avocats avec emails: {sum(1 for l in self.lawyers if l.get('emails'))}\n\n")
            
            if unique_emails:
                f.write("EMAILS TROUVÉS:\n")
                for i, email in enumerate(unique_emails, 1):
                    f.write(f"{i}. {email}\n")
            
            f.write(f"\nFICHIERS GÉNÉRÉS:\n")
            f.write(f"- {csv_file}\n")
            f.write(f"- {json_file}\n")
            if unique_emails:
                f.write(f"- {emails_file}\n")
            f.write(f"- {report_file}\n")
        
        print(f"💾 Fichiers sauvegardés:")
        print(f"   📊 CSV: {csv_file}")
        print(f"   📋 JSON: {json_file}")
        if unique_emails:
            print(f"   📧 Emails: {emails_file}")
        print(f"   📄 Rapport: {report_file}")
        
        return csv_file, json_file

def main():
    """Fonction principale"""
    scraper = SaintesLawyerScraper(headless=True)
    
    # Scraper toutes les pages
    lawyers = scraper.scrape_all_pages()
    
    if lawyers:
        # Sauvegarder les résultats
        scraper.save_results()
        
        print(f"\n🎯 SUCCÈS!")
        print(f"📊 {len(lawyers)} avocats extraits du Barreau de Saintes")
        
        # Afficher quelques exemples
        print(f"\n📋 Exemples d'avocats extraits:")
        for i, lawyer in enumerate(lawyers[:5]):
            print(f"   {i+1}. {lawyer['nom_complet']}")
            if lawyer.get('emails'):
                print(f"      📧 {lawyer['emails']}")
    
    else:
        print("❌ Aucun avocat extrait")

if __name__ == "__main__":
    main()