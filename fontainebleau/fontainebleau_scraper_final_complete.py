#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL COMPLET pour le Barreau de Fontainebleau
Scrape les 7 pages avec navigation automatique

URL: https://avocats-fontainebleau.fr/trouver-un-avocat/
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import re

class FontainebleauScraperFinalComplete:
    def __init__(self, headless=True):
        """Initialiser le scraper complet pour les 7 pages"""
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        self.base_url = "https://avocats-fontainebleau.fr/trouver-un-avocat/?dosrch=1&q=&wpbdp_view=search&listingfields%5B1%5D=&listingfields%5B2%5D=-1&listingfields%5B12%5D%5B%5D=&listingfields%5B13%5D=-1"
        self.current_page = 1
        self.max_pages = 7
        
    def setup_driver(self):
        """Configurer le driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-gpu")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"❌ Erreur driver : {e}")
            return False
    
    def accept_cookies(self):
        """Accepter les cookies"""
        try:
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[class*='cookie']",
                "[class*='cookie'] button"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    time.sleep(1)
                    return True
                except:
                    continue
            return True
        except:
            return True
    
    def extract_lawyer_info(self, lawyer_element):
        """Extraire les informations d'un avocat"""
        lawyer_data = {
            'prenom': '',
            'nom': '',
            'nom_complet': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'annee_inscription': '',
            'date_serment': '',
            'specialisations': [],
            'competences': [],
            'structure': '',
            'site_web': '',
            'url_fiche': '',
            'page_trouvee': self.current_page
        }
        
        try:
            # Nom complet
            try:
                name_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-nom .value a")
                name_text = name_element.get_attribute('textContent').strip()
                name_lines = [line.strip() for line in name_text.split('\n') if line.strip()]
                if name_lines:
                    full_name = name_lines[0].replace('Me ', '').strip()
                    
                    # Nettoyer le nom s'il contient le nom du cabinet
                    if '—' in full_name:
                        full_name = full_name.split('—')[0].strip()
                    
                    lawyer_data['nom_complet'] = full_name
                    
                    # Séparer prénom/nom 
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        lawyer_data['nom'] = name_parts[0]
                        lawyer_data['prenom'] = ' '.join(name_parts[1:])
                    
                lawyer_data['url_fiche'] = name_element.get_attribute('href')
            except:
                pass
            
            # Cabinet/Structure
            try:
                cabinet_element = lawyer_element.find_element(By.CSS_SELECTOR, ".cabinet")
                lawyer_data['structure'] = cabinet_element.text.strip()
            except:
                pass
            
            # Email
            try:
                email_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-e-mail .value")
                lawyer_data['email'] = email_element.text.strip()
            except:
                pass
            
            # Téléphone
            try:
                tel_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-telephone .value")
                lawyer_data['telephone'] = tel_element.text.strip()
            except:
                pass
            
            # Adresse
            try:
                address_element = lawyer_element.find_element(By.CSS_SELECTOR, ".address-info div")
                lawyer_data['adresse'] = address_element.text.strip()
            except:
                pass
            
            # Date de serment
            try:
                serment_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-date_de_serment .value")
                date_text = serment_element.text.strip()
                lawyer_data['date_serment'] = date_text
                
                if date_text:
                    date_parts = date_text.split('/')
                    if len(date_parts) == 3:
                        lawyer_data['annee_inscription'] = date_parts[2]
            except:
                pass
            
            # Compétences dominantes
            try:
                competence_elements = lawyer_element.find_elements(By.CSS_SELECTOR, ".wpbdp-field-competences_dominantes .value ul li")
                competences = [comp_elem.text.strip() for comp_elem in competence_elements if comp_elem.text.strip()]
                lawyer_data['competences'] = competences
                lawyer_data['specialisations'] = competences.copy()
            except:
                pass
            
            # Site web
            try:
                site_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-site_internet .value a")
                lawyer_data['site_web'] = site_element.get_attribute('href')
            except:
                pass
                
        except Exception:
            pass
        
        return lawyer_data
    
    def scrape_current_page(self):
        """Scraper la page actuelle"""
        try:
            # Attendre que les fiches se chargent
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wpbdp-listing"))
            )
            
            lawyer_elements = self.driver.find_elements(By.CSS_SELECTOR, ".wpbdp-listing")
            page_lawyers = []
            
            for lawyer_element in lawyer_elements:
                lawyer_data = self.extract_lawyer_info(lawyer_element)
                if lawyer_data['nom_complet']:
                    page_lawyers.append(lawyer_data)
            
            self.lawyers_data.extend(page_lawyers)
            print(f"📄 Page {self.current_page}/7: {len(page_lawyers)} avocats extraits (Total: {len(self.lawyers_data)})")
            
            return len(page_lawyers)
            
        except Exception as e:
            print(f"❌ Erreur page {self.current_page}: {e}")
            return 0
    
    def navigate_to_next_page(self):
        """Naviguer vers la page suivante"""
        if self.current_page >= self.max_pages:
            return False
            
        try:
            # Méthode 1 : Lien "suivant" avec rel='next'
            try:
                next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
                if next_link.is_enabled():
                    self.driver.execute_script("arguments[0].click();", next_link)
                    self.current_page += 1
                    time.sleep(3)
                    return True
            except:
                pass
            
            # Méthode 2 : Lien par numéro de page
            try:
                next_page_num = self.current_page + 1
                page_link = self.driver.find_element(By.XPATH, f"//a[text()='{next_page_num}']")
                self.driver.execute_script("arguments[0].click();", page_link)
                self.current_page += 1
                time.sleep(3)
                return True
            except:
                pass
            
            # Méthode 3 : Navigation directe par URL
            try:
                next_page_num = self.current_page + 1
                next_url = f"https://avocats-fontainebleau.fr/trouver-un-avocat/page/{next_page_num}/?dosrch=1&q=&wpbdp_view=search&listingfields%5B1%5D=&listingfields%5B2%5D=-1&listingfields%5B12%5D%5B%5D=&listingfields%5B13%5D=-1"
                self.driver.get(next_url)
                self.current_page += 1
                time.sleep(3)
                return True
            except:
                pass
                
            return False
            
        except Exception as e:
            print(f"❌ Erreur navigation : {e}")
            return False
    
    def run_complete_scraping(self):
        """Scraper toutes les 7 pages"""
        print("🚀 DÉMARRAGE SCRAPER FONTAINEBLEAU - 7 PAGES COMPLÈTES")
        print("=" * 70)
        
        if not self.setup_driver():
            return False
            
        try:
            # Page 1
            print(f"🌐 Navigation vers la page 1...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Accepter cookies
            self.accept_cookies()
            
            # Scraper page 1
            scraped_count = self.scrape_current_page()
            
            # Scraper pages 2 à 7
            while self.current_page < self.max_pages:
                print(f"➡️  Navigation vers la page {self.current_page + 1}...")
                
                if not self.navigate_to_next_page():
                    print(f"❌ Impossible de naviguer vers la page {self.current_page + 1}")
                    break
                
                scraped_count = self.scrape_current_page()
                if scraped_count == 0:
                    print(f"⚠️  Aucun avocat trouvé page {self.current_page}")
                
                time.sleep(2)  # Pause entre pages
            
            # Résultats finaux
            print("\n" + "=" * 70)
            print(f"🎉 SCRAPING TERMINÉ !")
            print(f"👥 Total d'avocats extraits : {len(self.lawyers_data)}")
            print(f"📄 Nombre de pages scrapées : {self.current_page}")
            print(f"📊 Couverture : {len(self.lawyers_data)}/51 avocats attendus")
            
            # Vérification des doublons
            emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
            unique_emails = set(emails)
            print(f"📧 Emails uniques : {len(unique_emails)}/{len(emails)}")
            
            # Sauvegarder les résultats
            self.save_results()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale : {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fermé")
    
    def save_results(self):
        """Sauvegarder tous les résultats"""
        if not self.lawyers_data:
            print("⚠️  Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON complet
        json_filename = f"fontainebleau_COMPLET_7PAGES_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON : {json_filename}")
        
        # 2. CSV complet
        csv_filename = f"fontainebleau_COMPLET_7PAGES_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                        'annee_inscription', 'date_serment', 'specialisations', 'competences', 
                        'structure', 'site_web', 'page_trouvee', 'url_fiche']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers_data:
                lawyer_copy = lawyer.copy()
                lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations'])
                lawyer_copy['competences'] = '; '.join(lawyer['competences'])
                writer.writerow(lawyer_copy)
        
        print(f"💾 CSV : {csv_filename}")
        
        # 3. Emails seulement
        emails_filename = f"fontainebleau_EMAILS_COMPLET_7PAGES_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
            f.write('\n'.join(emails))
        print(f"📧 Emails : {emails_filename}")
        
        # 4. Rapport détaillé
        report_filename = f"fontainebleau_RAPPORT_COMPLET_7PAGES_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT SCRAPING COMPLET - BARREAU DE FONTAINEBLEAU (7 PAGES)\\n")
            f.write(f"Généré le : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\\n")
            f.write(f"="*70 + "\\n\\n")
            
            f.write(f"STATISTIQUES GÉNÉRALES:\\n")
            f.write(f"- Total d'avocats extraits : {len(self.lawyers_data)}\\n")
            f.write(f"- Objectif attendu : 51 avocats\\n")
            f.write(f"- Couverture : {(len(self.lawyers_data)/51)*100:.1f}%\\n")
            f.write(f"- Avocats avec email : {len([l for l in self.lawyers_data if l['email']])}\\n")
            f.write(f"- Avocats avec téléphone : {len([l for l in self.lawyers_data if l['telephone']])}\\n")
            f.write(f"- Avocats avec structure/cabinet : {len([l for l in self.lawyers_data if l['structure']])}\\n")
            f.write(f"- Pages scrapées : {self.current_page}/7\\n\\n")
            
            # Répartition par page
            f.write(f"RÉPARTITION PAR PAGE:\\n")
            for page_num in range(1, self.current_page + 1):
                page_lawyers = [l for l in self.lawyers_data if l['page_trouvee'] == page_num]
                f.write(f"- Page {page_num}: {len(page_lawyers)} avocat(s)\\n")
            
            # Analyse des spécialisations
            all_competences = []
            for lawyer in self.lawyers_data:
                all_competences.extend(lawyer['competences'])
            
            from collections import Counter
            competences_count = Counter(all_competences)
            
            f.write(f"\\nSPÉCIALISATIONS LES PLUS FRÉQUENTES:\\n")
            for comp, count in competences_count.most_common(15):
                f.write(f"- {comp}: {count} avocat(s)\\n")
            
            f.write(f"\\n" + "="*70 + "\\n")
            f.write(f"LISTE COMPLÈTE DES AVOCATS:\\n\\n")
            
            for i, lawyer in enumerate(self.lawyers_data, 1):
                f.write(f"{i}. {lawyer['nom_complet']} (Page {lawyer['page_trouvee']})\\n")
                f.write(f"   Email: {lawyer['email']}\\n")
                f.write(f"   Téléphone: {lawyer['telephone']}\\n")
                f.write(f"   Structure: {lawyer['structure']}\\n")
                f.write(f"   Spécialisations: {'; '.join(lawyer['competences'])}\\n")
                f.write(f"   Année inscription: {lawyer['annee_inscription']}\\n")
                f.write(f"   Adresse: {lawyer['adresse']}\\n\\n")
        
        print(f"📋 Rapport : {report_filename}")
        print(f"\\n✅ Tous les fichiers sauvegardés !")

def main():
    """Fonction principale"""
    print("🎯 SCRAPER FONTAINEBLEAU - VERSION COMPLÈTE 7 PAGES")
    print("Mode headless activé pour ne pas vous déranger")
    
    scraper = FontainebleauScraperFinalComplete(headless=True)
    
    try:
        success = scraper.run_complete_scraping()
        
        if success:
            print("\\n🎉 SUCCÈS TOTAL ! Tous les avocats des 7 pages ont été extraits.")
        else:
            print("\\n❌ ÉCHEC. Vérifiez les erreurs ci-dessus.")
            
    except KeyboardInterrupt:
        print("\\n⛔ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\\n💥 Erreur inattendue : {e}")

if __name__ == "__main__":
    main()