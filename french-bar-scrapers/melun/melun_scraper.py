#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER CORRIGÉ COMPLET - BARREAU DE MELUN
Version corrigée pour récupérer TOUS les avocats (70+ attendus)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import csv
import time
import random
import re
from datetime import datetime
import logging

class MelunCompleteFixedScraper:
    def __init__(self, headless=False):
        self.setup_logging()
        self.setup_driver(headless)
        self.base_url = "https://barreau-melun.org"
        self.lawyers_data = []
        self.processed_urls = set()
        
    def setup_logging(self):
        """Configuration logging"""
        log_filename = f"melun_fixed_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self, headless=False):
        """Configuration driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 15)
        
    def clean_text(self, text):
        """Nettoyage du texte"""
        if not text:
            return ""
        
        text = re.sub(r'if\s*\([^)]*serviceWorker[^}]*\}[^}]*\}', '', text)
        text = re.sub(r'\.[\w\-]+\s*\{[^}]*\}', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        if len(text) > 200 and any(pattern in text for pattern in ['serviceWorker', '.slick-']):
            js_positions = [text.find(p) for p in ['serviceWorker', '.slick-'] if text.find(p) != -1]
            if js_positions:
                text = text[:min(js_positions)].strip()
                
        return text.strip()
    
    def try_different_pagination_approaches(self):
        """Tester différentes approches pour accéder à tous les avocats"""
        all_lawyers = []
        
        # Approche 1: URL de base sans filtres
        self.logger.info("🔍 APPROCHE 1: URL de base")
        base_lawyers = self.extract_from_url(f"{self.base_url}/annuaire-wpbdp_category-general-2/")
        all_lawyers.extend(base_lawyers)
        self.logger.info(f"Approche 1: {len(base_lawyers)} avocats trouvés")
        
        # Approche 2: Avec la catégorie avocat-a-melun
        self.logger.info("🔍 APPROCHE 2: Catégorie avocat-a-melun")
        melun_lawyers = self.extract_from_url(f"{self.base_url}/annuaire-wpbdp_category-general-2/wpbdp_category/avocat-a-melun/")
        all_lawyers.extend(melun_lawyers)
        self.logger.info(f"Approche 2: {len(melun_lawyers)} avocats trouvés")
        
        # Approche 3: Tester différents paramètres de pagination avec JavaScript
        self.logger.info("🔍 APPROCHE 3: Navigation JavaScript")
        js_lawyers = self.try_javascript_navigation()
        all_lawyers.extend(js_lawyers)
        self.logger.info(f"Approche 3: {len(js_lawyers)} avocats trouvés")
        
        # Approche 4: Par filtres de villes
        self.logger.info("🔍 APPROCHE 4: Filtres par villes")
        cities = ["melun", "provins", "fontainebleau", "ozoir-la-ferriere", "dammarie-les-lys"]
        for city in cities:
            city_lawyers = self.extract_by_city_filter(city)
            all_lawyers.extend(city_lawyers)
            self.logger.info(f"  Ville {city}: {len(city_lawyers)} avocats")
        
        # Approche 5: Par spécialisations
        self.logger.info("🔍 APPROCHE 5: Filtres par spécialisations")
        specializations = ["droit-de-la-famille", "droit-penal", "droit-des-affaires", "droit-du-travail"]
        for spec in specializations:
            spec_lawyers = self.extract_by_specialization_filter(spec)
            all_lawyers.extend(spec_lawyers)
            self.logger.info(f"  Spécialisation {spec}: {len(spec_lawyers)} avocats")
        
        # Déduplication
        unique_lawyers = self.deduplicate_lawyers(all_lawyers)
        self.logger.info(f"\n✅ TOTAL après déduplication: {len(unique_lawyers)} avocats uniques")
        
        return unique_lawyers
    
    def extract_from_url(self, url):
        """Extraire les avocats depuis une URL"""
        try:
            self.logger.info(f"📄 Extraction depuis: {url}")
            self.driver.get(url)
            time.sleep(5)
            
            # Méthode d'extraction robuste
            lawyers = []
            
            # Chercher tous les liens d'avocats
            lawyer_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/annuaire/id-')]")
            
            for link in lawyer_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    if href and text and len(text) > 1 and text != '+' and href not in self.processed_urls:
                        lawyers.append({
                            'url': href,
                            'nom_complet': text
                        })
                        self.processed_urls.add(href)
                except:
                    continue
            
            return lawyers
            
        except Exception as e:
            self.logger.error(f"Erreur extraction {url}: {e}")
            return []
    
    def try_javascript_navigation(self):
        """Essayer la navigation JavaScript"""
        try:
            url = f"{self.base_url}/annuaire-wpbdp_category-general-2/wpbdp_category/avocat-a-melun/"
            self.driver.get(url)
            time.sleep(5)
            
            lawyers = []
            
            # Essayer de cliquer sur les liens de pagination
            for page_num in range(2, 15):  # Pages 2 à 14
                try:
                    # Chercher le lien de la page
                    page_link = self.driver.find_element(By.XPATH, f"//a[contains(@href, '/page/{page_num}/') or text()='{page_num}']")
                    
                    # Scroller vers l'élément et cliquer
                    self.driver.execute_script("arguments[0].scrollIntoView();", page_link)
                    time.sleep(1)
                    page_link.click()
                    time.sleep(3)
                    
                    # Extraire les avocats de cette page
                    current_url = self.driver.current_url
                    self.logger.info(f"  Page {page_num}: {current_url}")
                    
                    page_lawyers = self.extract_lawyers_from_current_page()
                    lawyers.extend(page_lawyers)
                    self.logger.info(f"  Page {page_num}: {len(page_lawyers)} avocats")
                    
                    if len(page_lawyers) == 0:
                        self.logger.info(f"  Page {page_num} vide, arrêt")
                        break
                    
                except Exception as e:
                    self.logger.debug(f"Page {page_num} non accessible: {e}")
                    continue
            
            return lawyers
            
        except Exception as e:
            self.logger.error(f"Erreur navigation JS: {e}")
            return []
    
    def extract_by_city_filter(self, city):
        """Extraire par filtre de ville"""
        try:
            # URL avec filtre de ville (à adapter selon la structure du site)
            url = f"{self.base_url}/annuaire-wpbdp_category-general-2/?ville={city}"
            return self.extract_from_url(url)
        except Exception as e:
            self.logger.error(f"Erreur filtre ville {city}: {e}")
            return []
    
    def extract_by_specialization_filter(self, specialization):
        """Extraire par filtre de spécialisation"""
        try:
            url = f"{self.base_url}/annuaire-wpbdp_category-general-2/?specialisation={specialization}"
            return self.extract_from_url(url)
        except Exception as e:
            self.logger.error(f"Erreur filtre spécialisation {specialization}: {e}")
            return []
    
    def extract_lawyers_from_current_page(self):
        """Extraire les avocats de la page actuelle"""
        try:
            lawyers = []
            lawyer_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/annuaire/id-')]")
            
            for link in lawyer_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    if href and text and len(text) > 1 and text != '+' and href not in self.processed_urls:
                        lawyers.append({
                            'url': href,
                            'nom_complet': text
                        })
                        self.processed_urls.add(href)
                except:
                    continue
                    
            return lawyers
            
        except Exception as e:
            self.logger.error(f"Erreur extraction page courante: {e}")
            return []
    
    def deduplicate_lawyers(self, lawyers):
        """Déduplication des avocats"""
        seen_urls = set()
        seen_names = set()
        unique_lawyers = []
        
        for lawyer in lawyers:
            url = lawyer.get('url', '')
            name = lawyer.get('nom_complet', '')
            
            if url not in seen_urls and name not in seen_names and url and name:
                unique_lawyers.append(lawyer)
                seen_urls.add(url)
                seen_names.add(name)
        
        return unique_lawyers
    
    def extract_lawyer_details(self, lawyer_url):
        """Extraire les détails d'un avocat"""
        details = {'source': lawyer_url}
        
        try:
            self.driver.get(lawyer_url)
            time.sleep(2)
            
            body = self.driver.find_element(By.TAG_NAME, "body")
            page_text = body.text
            
            # Email
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_text)
            if email_match:
                details['email'] = email_match.group(1)
            
            # Téléphone
            phone_patterns = [
                r'(\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2})',
                r'(\d{10})',
                r'(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})'
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, page_text)
                if phone_match:
                    details['telephone'] = phone_match.group(1)
                    break
            
            # Date de serment
            serment_match = re.search(r'Serment.*?(\d{2}/\d{2}/\d{4})', page_text, re.IGNORECASE)
            if serment_match:
                details['date_serment'] = serment_match.group(1)
                year = serment_match.group(1).split('/')[-1]
                if year.isdigit() and 1980 <= int(year) <= 2025:
                    details['annee_inscription'] = year
            
            # Adresse
            address_match = re.search(r'(\d+[^0-9]*?\d{5}\s+[A-Z][A-Z\s]+)', page_text)
            if address_match:
                address = self.clean_text(address_match.group(1))
                if 15 <= len(address) <= 80:
                    details['adresse'] = address
            
            # Spécialisations - Pattern élargi pour capturer toutes les spécialisations
            # Pattern 1: Droit + compléments
            droit_pattern = r'(Droit\s+(?:de\s+la\s+|des\s+|du\s+|d\'\s*)?[a-zA-Z\sàáâäèéêëìíîïòóôöùúûü]{3,80})'
            # Pattern 2: Autres spécialisations (Dommages, Contentieux, etc.)
            other_pattern = r'((?:Dommages|Contentieux|Procédures?|Recouvrement|Négociation|Médiation)\s+[a-zA-Z\sàáâäèéêëìíîïòóôöùúûü]{3,80})'
            
            specializations = []
            specializations.extend(re.findall(droit_pattern, page_text, re.IGNORECASE))
            specializations.extend(re.findall(other_pattern, page_text, re.IGNORECASE))
            if specializations:
                clean_specs = []
                for spec in specializations[:3]:
                    clean_spec = self.clean_text(spec)
                    if clean_spec and clean_spec not in clean_specs:
                        clean_specs.append(clean_spec)
                details['specialisations'] = '; '.join(clean_specs)
            
            # Structure
            structure_match = re.search(r'((?:SCP|SELARL|Cabinet)\s+[A-Z][^0-9\n]{5,40})', page_text, re.IGNORECASE)
            if structure_match:
                structure = self.clean_text(structure_match.group(1))
                if 5 <= len(structure) <= 50:
                    details['structure'] = structure
            
            return details
            
        except Exception as e:
            self.logger.error(f"Erreur détails {lawyer_url}: {e}")
            return details
    
    def run_complete_fixed_scraping(self):
        """Lancer le scraping complet corrigé"""
        start_time = datetime.now()
        self.logger.info("🚀 DÉMARRAGE SCRAPING COMPLET CORRIGÉ - BARREAU MELUN")
        self.logger.info("Objectif: Récupérer TOUS les avocats (70+ attendus)")
        self.logger.info("=" * 70)
        
        try:
            # Phase 1: Collecte avec plusieurs approches
            self.logger.info("\n📋 PHASE 1: Collecte exhaustive avec approches multiples")
            all_lawyer_links = self.try_different_pagination_approaches()
            
            if len(all_lawyer_links) < 30:
                self.logger.warning(f"⚠️  Seulement {len(all_lawyer_links)} avocats trouvés - moins que prévu")
            
            # Phase 2: Extraction des détails
            self.logger.info(f"\n📋 PHASE 2: Extraction détaillée ({len(all_lawyer_links)} avocats)")
            
            for i, link in enumerate(all_lawyer_links, 1):
                try:
                    progress = f"{i}/{len(all_lawyer_links)}"
                    eta_minutes = ((len(all_lawyer_links) - i) * 2.5) / 60
                    
                    self.logger.info(f"[{progress}] {link['nom_complet']} (ETA: {eta_minutes:.1f}min)")
                    
                    # Séparer nom/prénom avec gestion des noms composés
                    full_name = link['nom_complet']
                    
                    # Logique simple : le dernier mot en majuscule/minuscule mélangée est le prénom
                    # Tous les mots précédents (même avec espaces) forment le nom de famille
                    if ' ' in full_name:
                        name_parts = full_name.split()
                        
                        # Trouver le dernier mot qui n'est pas entièrement en majuscules
                        # (les prénoms ont souvent une majuscule + minuscules)
                        prenom_index = len(name_parts) - 1  # par défaut le dernier
                        
                        for i in range(len(name_parts) - 1, -1, -1):
                            word = name_parts[i]
                            # Si le mot a des minuscules (pas tout en majuscules), c'est probablement le prénom
                            if any(c.islower() for c in word):
                                prenom_index = i
                                break
                        
                        # Séparer nom et prénom
                        if prenom_index > 0:
                            nom = ' '.join(name_parts[:prenom_index])
                            prenom = ' '.join(name_parts[prenom_index:])
                        else:
                            # Cas particulier : tout en majuscules ou un seul mot composé
                            nom = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
                            prenom = name_parts[-1] if len(name_parts) > 1 else ""
                    else:
                        nom = full_name
                        prenom = ""
                    
                    # Extraire les détails
                    details = self.extract_lawyer_details(link['url'])
                    
                    # Construire l'avocat complet
                    lawyer = {
                        'nom': nom,
                        'prenom': prenom,
                        'nom_complet': full_name,
                        'email': details.get('email', ''),
                        'telephone': details.get('telephone', ''),
                        'date_serment': details.get('date_serment', ''),
                        'annee_inscription': details.get('annee_inscription', ''),
                        'specialisations': details.get('specialisations', ''),
                        'structure': details.get('structure', ''),
                        'adresse': details.get('adresse', ''),
                        'source': details.get('source', '')
                    }
                    
                    self.lawyers_data.append(lawyer)
                    
                    # Feedback rapide
                    email_status = "✓" if lawyer['email'] else "✗"
                    phone_status = "✓" if lawyer['telephone'] else "✗"
                    self.logger.info(f"    Email: {email_status} | Tél: {phone_status}")
                    
                    time.sleep(random.uniform(1.5, 2.5))
                    
                except Exception as e:
                    self.logger.error(f"Erreur avocat {i}: {e}")
                    continue
            
            # Résultats finaux
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info(f"\n🎉 SCRAPING CORRIGÉ TERMINÉ!")
            self.logger.info(f"Durée totale: {duration}")
            self.logger.info(f"Avocats récupérés: {len(self.lawyers_data)}")
            
            if len(self.lawyers_data) >= 50:
                self.logger.info("✅ OBJECTIF ATTEINT - Plus de 50 avocats trouvés!")
            elif len(self.lawyers_data) >= 30:
                self.logger.info("⚠️  OBJECTIF PARTIELLEMENT ATTEINT - Plus de 30 avocats")
            else:
                self.logger.warning("❌ OBJECTIF NON ATTEINT - Moins de 30 avocats")
            
            self.save_final_results()
            return len(self.lawyers_data)
            
        except Exception as e:
            self.logger.error(f"Erreur critique: {e}")
            return 0
        finally:
            self.cleanup()
    
    def save_final_results(self):
        """Sauvegarde finale"""
        if not self.lawyers_data:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_count = len(self.lawyers_data)
        
        # CSV
        csv_filename = f"MELUN_FIXED_COMPLET_{total_count}_avocats_{timestamp}.csv"
        fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                     'date_serment', 'annee_inscription', 'specialisations', 
                     'structure', 'adresse', 'source']
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for lawyer in self.lawyers_data:
                writer.writerow(lawyer)
        
        # JSON
        json_filename = f"MELUN_FIXED_COMPLET_{total_count}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, indent=2, ensure_ascii=False)
        
        # Emails
        emails_filename = f"MELUN_FIXED_COMPLET_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as emails_file:
            emails = [l['email'] for l in self.lawyers_data if l['email']]
            unique_emails = sorted(list(set(emails)))
            for email in unique_emails:
                emails_file.write(f"{email}\n")
        
        # Rapport
        rapport_filename = f"MELUN_FIXED_COMPLET_RAPPORT_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as rapport:
            rapport.write(f"RAPPORT FINAL - SCRAPING CORRIGÉ BARREAU MELUN\n")
            rapport.write(f"{'='*60}\n")
            rapport.write(f"Date: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            rapport.write(f"Objectif: Récupérer 70+ avocats\n")
            rapport.write(f"Résultat: {total_count} avocats récupérés\n\n")
            
            # Statistiques
            stats = self.calculate_stats()
            rapport.write(f"STATISTIQUES:\n")
            rapport.write(f"{'─'*30}\n")
            for key, value in stats.items():
                percentage = (value / total_count) * 100 if total_count > 0 else 0
                rapport.write(f"{key}: {value}/{total_count} ({percentage:.1f}%)\n")
            
            # Liste des emails
            unique_emails = sorted(list(set([l['email'] for l in self.lawyers_data if l['email']])))
            rapport.write(f"\nEMAILS ({len(unique_emails)} uniques):\n")
            rapport.write(f"{'─'*30}\n")
            for email in unique_emails:
                rapport.write(f"• {email}\n")
        
        self.logger.info(f"\n📁 FICHIERS SAUVEGARDÉS:")
        self.logger.info(f"  • CSV: {csv_filename}")
        self.logger.info(f"  • JSON: {json_filename}")
        self.logger.info(f"  • Emails: {emails_filename}")
        self.logger.info(f"  • Rapport: {rapport_filename}")
    
    def calculate_stats(self):
        """Calculer statistiques"""
        total = len(self.lawyers_data)
        if total == 0:
            return {}
        
        return {
            'Avec email': len([l for l in self.lawyers_data if l['email']]),
            'Avec téléphone': len([l for l in self.lawyers_data if l['telephone']]),
            'Avec date serment': len([l for l in self.lawyers_data if l['date_serment']]),
            'Avec spécialisations': len([l for l in self.lawyers_data if l['specialisations']]),
            'Avec structure': len([l for l in self.lawyers_data if l['structure']]),
            'Avec adresse': len([l for l in self.lawyers_data if l['adresse']])
        }
    
    def cleanup(self):
        """Nettoyage"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                self.logger.info("🔒 Navigateur fermé")
        except:
            pass

if __name__ == "__main__":
    print("🚀 LANCEMENT SCRAPER CORRIGÉ - OBJECTIF 70+ AVOCATS")
    print("Approches multiples pour récupérer TOUS les avocats")
    print("=" * 60)
    
    scraper = MelunCompleteFixedScraper(headless=False)  # Mode visible pour debug
    total_found = scraper.run_complete_fixed_scraping()
    
    if total_found >= 50:
        print(f"\n🎉 SUCCÈS! {total_found} avocats récupérés - Objectif atteint!")
    elif total_found >= 30:
        print(f"\n⚠️  PARTIEL: {total_found} avocats récupérés - Mieux mais pas encore optimal")
    else:
        print(f"\n❌ INSUFFISANT: {total_found} avocats seulement - Investigation supplémentaire nécessaire")