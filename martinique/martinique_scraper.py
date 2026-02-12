#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import csv
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MartiniqueLawyerScraperCorrected:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.lawyers = []
        self.base_url = "https://avocatsdemartinique.fr"
        self.directory_url = "https://avocatsdemartinique.fr/le-barreau/annuaire-des-avocats/"
        
    def setup_driver(self):
        """Configuration du driver Selenium"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def accept_cookies(self):
        """Accepter les cookies"""
        try:
            time.sleep(2)
            cookie_selectors = [
                "button[class*='accept']",
                "button[id*='cookie']",
                "button[class*='cookie']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    time.sleep(1)
                    break
                except TimeoutException:
                    continue
        except Exception:
            pass

    def clean_name_advanced(self, full_name):
        """Nettoyer et séparer correctement le nom complet"""
        try:
            # Supprimer les éléments parasites
            clean_name = full_name
            clean_name = re.sub(r'Maītre\s*', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'Maitre\s*', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s*-\s*Annuaire des avocats', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s*-\s*Barreau de Martinique', '', clean_name, flags=re.IGNORECASE)
            clean_name = clean_name.strip()
            
            # Diviser en prénom et nom
            if clean_name:
                # Séparer par espaces
                parts = clean_name.split()
                if len(parts) >= 2:
                    # Premier mot = prénom, le reste = nom
                    prenom = parts[0]
                    nom = ' '.join(parts[1:])
                    return prenom, nom, clean_name
                else:
                    return "", clean_name, clean_name
            
            return "", "", ""
                
        except Exception:
            return "", full_name, full_name

    def extract_specializations_clean(self, page_source):
        """Extraire uniquement les vraies spécialisations juridiques"""
        try:
            specializations = set()
            
            # Patterns pour trouver les spécialisations
            spec_patterns = [
                r'Droit\s+[a-zA-ZÀ-ÿ\s]+',
                r'Procédure\s+[a-zA-ZÀ-ÿ\s]*'
            ]
            
            for pattern in spec_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    # Nettoyer la spécialisation
                    spec = match.strip()
                    
                    # Filtrer les vraies spécialisations (longueur raisonnable)
                    if 5 <= len(spec) <= 50 and not any(exclude in spec.lower() for exclude in 
                        ['mention', 'politique', 'horaire', 'téléphone', 'contact', 'accès', 'aide', 'barreau']):
                        
                        # Nettoyer davantage
                        spec = re.sub(r'[,;]+$', '', spec)  # Supprimer virgules/points-virgules à la fin
                        spec = spec.strip()
                        
                        if spec:
                            specializations.add(spec)
            
            # Convertir en liste et limiter
            return list(specializations)[:10]  # Max 10 spécialisations
            
        except Exception:
            return []

    def extract_structure_info(self, page_source):
        """Extraire les informations de structure/cabinet"""
        try:
            # Chercher les mentions de cabinet, société, etc.
            structure_patterns = [
                r'Cabinet\s+[A-ZÀ-ÿ][a-zA-ZÀ-ÿ\s-]+',
                r'Société\s+[A-ZÀ-ÿ][a-zA-ZÀ-ÿ\s-]+',
                r'SCP\s+[A-ZÀ-ÿ][a-zA-ZÀ-ÿ\s-]+',
                r'SELARL\s+[A-ZÀ-ÿ][a-zA-ZÀ-ÿ\s-]+'
            ]
            
            for pattern in structure_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    if 5 <= len(match) <= 100:  # Longueur raisonnable
                        return match.strip()
            
            return ""
        except Exception:
            return ""

    def get_lawyer_links(self):
        """Extraire tous les liens vers les profils d'avocats"""
        try:
            if not self.headless:
                print("🔍 Extraction des liens...")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            lawyer_links = []
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/avocat/' in href and href not in lawyer_links:
                    lawyer_links.append(href)
            
            if not self.headless:
                print(f"📋 {len(lawyer_links)} profils trouvés")
            return lawyer_links
            
        except Exception as e:
            if not self.headless:
                print(f"❌ Erreur: {e}")
            return []

    def extract_lawyer_info(self, lawyer_url):
        """Extraire les informations d'un avocat avec nettoyage amélioré"""
        try:
            self.driver.get(lawyer_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            lawyer_info = {
                'url': lawyer_url,
                'nom': '',
                'prenom': '',
                'nom_complet': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'site_web': ''
            }
            
            # Extraire le nom depuis le titre de la page
            try:
                title = self.driver.title
                if title:
                    prenom, nom, nom_complet = self.clean_name_advanced(title)
                    lawyer_info['prenom'] = prenom
                    lawyer_info['nom'] = nom
                    lawyer_info['nom_complet'] = nom_complet
            except:
                pass
            
            # Backup: chercher dans h1 si titre vide
            if not lawyer_info['nom_complet']:
                try:
                    h1_element = self.driver.find_element(By.TAG_NAME, "h1")
                    h1_text = h1_element.text.strip()
                    if h1_text:
                        prenom, nom, nom_complet = self.clean_name_advanced(h1_text)
                        lawyer_info['prenom'] = prenom
                        lawyer_info['nom'] = nom
                        lawyer_info['nom_complet'] = nom_complet
                except:
                    pass
            
            # Extraire l'email
            try:
                email_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                for email_link in email_links:
                    email = email_link.get_attribute('href').replace('mailto:', '')
                    if '@' in email and '.' in email and len(email) > 5:
                        lawyer_info['email'] = email
                        break
            except:
                pass
            
            # Backup email dans le texte
            if not lawyer_info['email']:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, page_text)
                    if emails:
                        lawyer_info['email'] = emails[0]
                except:
                    pass
            
            # Extraire le téléphone
            try:
                phone_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
                for phone_link in phone_links:
                    phone = phone_link.get_attribute('href').replace('tel:', '')
                    if phone and len(phone) > 8:
                        lawyer_info['telephone'] = phone
                        break
            except:
                pass
            
            # Récupérer le source HTML pour analyse
            page_source = self.driver.page_source
            
            # Extraire l'année d'inscription
            year_patterns = [
                r'inscrit[e]?\s+(?:au\s+barreau\s+)?(?:en\s+)?(\d{4})',
                r'barreau\s+(?:depuis\s+)?(\d{4})',
                r'serment\s+(?:en\s+)?(\d{4})'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    year = int(match)
                    if 1970 <= year <= datetime.now().year:
                        lawyer_info['annee_inscription'] = str(year)
                        break
                if lawyer_info['annee_inscription']:
                    break
            
            # Extraire les spécialisations nettoyées
            lawyer_info['specialisations'] = self.extract_specializations_clean(page_source)
            
            # Extraire la structure
            lawyer_info['structure'] = self.extract_structure_info(page_source)
            
            if not self.headless:
                print(f"✅ {lawyer_info['prenom']} {lawyer_info['nom']}")
            return lawyer_info
            
        except Exception as e:
            if not self.headless:
                print(f"❌ Erreur pour {lawyer_url}: {e}")
            return None

    def run_test(self, max_lawyers=10):
        """Test avec un échantillon d'avocats"""
        try:
            print("🧪 Test du scraper corrigé...")
            
            self.setup_driver()
            print(f"📍 Navigation vers {self.directory_url}")
            self.driver.get(self.directory_url)
            
            self.accept_cookies()
            
            lawyer_links = self.get_lawyer_links()
            if not lawyer_links:
                print("❌ Aucun lien trouvé")
                return
            
            # Test avec les premiers avocats
            test_links = lawyer_links[:max_lawyers]
            print(f"🧪 Test avec {len(test_links)} avocats")
            
            for i, lawyer_url in enumerate(test_links, 1):
                print(f"\n--- Test {i}/{len(test_links)} ---")
                lawyer_info = self.extract_lawyer_info(lawyer_url)
                if lawyer_info:
                    self.lawyers.append(lawyer_info)
                time.sleep(1.5)
            
            self.save_results("martinique_test_corrige")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def run_complete_scraping(self):
        """Scraping complet avec corrections"""
        try:
            print("🚀 Scraping complet corrigé...")
            
            self.setup_driver()
            print(f"📍 Navigation vers {self.directory_url}")
            self.driver.get(self.directory_url)
            
            self.accept_cookies()
            
            lawyer_links = self.get_lawyer_links()
            if not lawyer_links:
                print("❌ Aucun lien trouvé")
                return
            
            print(f"🎯 Scraping de {len(lawyer_links)} avocats...")
            
            for i, lawyer_url in enumerate(lawyer_links, 1):
                if i % 20 == 0:
                    print(f"📊 Progression: {i}/{len(lawyer_links)} avocats...")
                    
                lawyer_info = self.extract_lawyer_info(lawyer_url)
                if lawyer_info:
                    self.lawyers.append(lawyer_info)
                time.sleep(1.2)
            
            self.save_results("martinique_FINAL_CORRIGE")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def save_results(self, prefix="martinique_corrige"):
        """Sauvegarder avec format amélioré"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.lawyers:
            # CSV
            csv_filename = f"{prefix}_{len(self.lawyers)}_avocats_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                             'annee_inscription', 'specialisations', 'structure', 'site_web', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers:
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer_copy['specialisations'])
                    writer.writerow(lawyer_copy)
            
            # JSON
            json_filename = f"{prefix}_{len(self.lawyers)}_avocats_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.lawyers, jsonfile, ensure_ascii=False, indent=2)
            
            # Emails uniquement
            emails_filename = f"{prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as emailsfile:
                for lawyer in self.lawyers:
                    if lawyer['email']:
                        emailsfile.write(f"{lawyer['email']}\n")
            
            # Rapport
            report_filename = f"{prefix}_RAPPORT_DETAILLE_{timestamp}.txt"
            with open(report_filename, 'w', encoding='utf-8') as reportfile:
                reportfile.write(f"RAPPORT CORRIGÉ - BARREAU DE MARTINIQUE\n")
                reportfile.write(f"=====================================\n\n")
                reportfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                reportfile.write(f"Nombre d'avocats: {len(self.lawyers)}\n\n")
                
                emails_found = sum(1 for l in self.lawyers if l['email'])
                years_found = sum(1 for l in self.lawyers if l['annee_inscription'])
                specs_found = sum(1 for l in self.lawyers if l['specialisations'])
                
                reportfile.write(f"📊 STATISTIQUES:\n")
                reportfile.write(f"  Emails: {emails_found}/{len(self.lawyers)} ({emails_found/len(self.lawyers)*100:.1f}%)\n")
                reportfile.write(f"  Années: {years_found}/{len(self.lawyers)} ({years_found/len(self.lawyers)*100:.1f}%)\n")
                reportfile.write(f"  Spécialisations: {specs_found}/{len(self.lawyers)} ({specs_found/len(self.lawyers)*100:.1f}%)\n\n")
                
                # Exemples d'extraction
                reportfile.write("📋 EXEMPLES D'EXTRACTION:\n")
                reportfile.write("-" * 30 + "\n")
                for i, lawyer in enumerate(self.lawyers[:10], 1):  # 10 premiers
                    reportfile.write(f"\nAvocat {i}:\n")
                    reportfile.write(f"  Nom complet: {lawyer['nom_complet']}\n")
                    reportfile.write(f"  Prénom: {lawyer['prenom']}\n")
                    reportfile.write(f"  Nom: {lawyer['nom']}\n")
                    reportfile.write(f"  Email: {lawyer['email']}\n")
                    reportfile.write(f"  Année: {lawyer['annee_inscription']}\n")
                    if lawyer['specialisations']:
                        reportfile.write(f"  Spécialisations: {', '.join(lawyer['specialisations'][:3])}\n")
                    reportfile.write(f"  Structure: {lawyer['structure']}\n")
            
            print(f"📊 Résultats sauvegardés:")
            print(f"  - {csv_filename}")
            print(f"  - {json_filename}") 
            print(f"  - {emails_filename}")
            print(f"  - {report_filename}")
            
            print(f"\n📈 RÉSUMÉ:")
            print(f"  Total: {len(self.lawyers)} avocats")
            print(f"  Emails: {emails_found} ({emails_found/len(self.lawyers)*100:.1f}%)")

if __name__ == "__main__":
    # Scraping complet
    scraper = MartiniqueLawyerScraperCorrected(headless=True)
    scraper.run_complete_scraping()