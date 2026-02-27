#!/usr/bin/env python3
"""
SCRAPER PRODUCTION AUTOMATIQUE - BARREAU DE BAYONNE
=================================================
Version finale optimisée pour extraction complète de tous les avocats
du barreau de Bayonne en mode headless.

URL cible: https://www.avocats-bayonne.org/annuaire-des-avocats.html

DONNÉES EXTRAITES:
- Nom et prénom (gestion des noms composés)
- Année d'inscription au barreau
- Spécialisations juridiques
- Adresse complète
- Structure/Cabinet
- Emails et téléphones (si disponibles)

USAGE:
    python3 bayonne_scraper_production.py

SORTIE:
- CSV (format tableur)
- JSON (format programmation)
- TXT emails seuls
- Rapport détaillé avec statistiques

Auteur: Claude Code Assistant
Date: Février 2026
"""

import time
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BayonneLawyerScraper:
    """
    Scraper pour le Barreau de Bayonne
    Extrait automatiquement tous les avocats avec leurs informations détaillées
    """
    
    def __init__(self):
        self.base_url = "https://www.avocats-bayonne.org"
        self.start_url = "https://www.avocats-bayonne.org/annuaire-des-avocats.html?limitstart=0"
        self.driver = None
        self.wait = None
        self.lawyers_data = []
        self.processed_urls = set()
        
    def setup_driver(self):
        """Configure le driver Chrome en mode headless optimisé"""
        chrome_options = Options()
        
        # Configuration headless pour exécution en arrière-plan
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        
        # User-Agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Optimisations pour la vitesse
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Driver Chrome headless initialisé")
            return True
        except Exception as e:
            print(f"❌ Erreur driver: {e}")
            print("💡 Vérifiez que ChromeDriver est installé et dans le PATH")
            return False
    
    def accept_cookies(self):
        """Accepte automatiquement les cookies si présents"""
        try:
            cookie_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepter') or contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            print("✅ Cookies acceptés")
            time.sleep(1)
        except TimeoutException:
            pass  # Pas de bannière cookies
    
    def scan_all_directory_pages(self) -> List[str]:
        """
        Scanne toutes les pages de l'annuaire pour récupérer 
        tous les liens vers les profils d'avocats
        """
        all_profile_links = []
        
        try:
            page_offset = 0
            
            while True:
                # URL de la page courante
                page_url = f"{self.start_url.split('?')[0]}?limitstart={page_offset}"
                print(f"📄 Scan page: limitstart={page_offset}")
                
                self.driver.get(page_url)
                time.sleep(2)
                
                # Récupérer tous les liens CB (Community Builder)
                page_links = []
                try:
                    cb_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='cb-profile']")
                    for link in cb_links:
                        href = link.get_attribute('href')
                        if href and href not in page_links and href not in all_profile_links:
                            page_links.append(href)
                except:
                    pass
                
                if not page_links:
                    print(f"ℹ️  Fin de l'annuaire à limitstart={page_offset}")
                    break
                
                print(f"✅ {len(page_links)} nouveaux profils trouvés")
                all_profile_links.extend(page_links)
                
                # Page suivante (increment de 50)
                page_offset += 50
                
                # Sécurité: maximum 50 pages
                if page_offset > 2500:
                    print("⚠️  Arrêt de sécurité après 50 pages")
                    break
            
            print(f"🎯 TOTAL: {len(all_profile_links)} profils d'avocats détectés")
            return all_profile_links
            
        except Exception as e:
            print(f"❌ Erreur lors du scan: {e}")
            return all_profile_links
    
    def extract_lawyer_details(self, profile_url: str, index: int, total: int) -> Optional[Dict]:
        """
        Extrait toutes les informations disponibles d'un avocat
        depuis sa page de profil individuelle
        """
        try:
            if profile_url in self.processed_urls:
                return None
                
            self.processed_urls.add(profile_url)
            
            # Affichage du progrès
            if index % 10 == 0 or index <= 10:
                print(f"🔍 [{index:3d}/{total}] Extraction: {profile_url.split('/')[-1]}")
            
            self.driver.get(profile_url)
            time.sleep(1.5)
            
            # Structure de données pour un avocat
            lawyer_data = {
                'url_source': profile_url,
                'prenom': '',
                'nom': '',
                'annee_inscription': '',
                'specialisations': '',
                'competences': '',
                'activites_dominantes': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'email': '',
                'site_web': ''
            }
            
            # Récupération du contenu de la page
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                page_html = self.driver.page_source
            except:
                return None
            
            # === EXTRACTION NOM ET PRÉNOM ===
            name_selectors = ["h1", "h2", ".cb_userProfileName", ".cbUserProfileName"]
            full_name = ""
            
            for selector in name_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    full_name = elem.text.strip()
                    if full_name and len(full_name) > 2:
                        break
                except:
                    continue
            
            if full_name:
                # Nettoyer le nom (enlever les titres)
                clean_name = re.sub(r'^(Maître|Me|M\.|Mme)\.?\s*', '', full_name, flags=re.IGNORECASE)
                words = clean_name.split()
                
                if len(words) >= 2:
                    # Détecter si le premier mot est un nom de famille (majuscules)
                    if words[0].isupper() or words[0].replace('-', '').replace(' ', '').isupper():
                        lawyer_data['nom'] = words[0]
                        lawyer_data['prenom'] = ' '.join(words[1:])
                    else:
                        lawyer_data['prenom'] = words[0]
                        lawyer_data['nom'] = ' '.join(words[1:])
            
            # === EXTRACTION EMAIL ===
            email_patterns = [
                r'[\w\.-]+@[\w\.-]+\.\w+',
                r'[\w\.-]+\s*@\s*[\w\.-]+\s*\.\s*\w+'
            ]
            
            for source in [page_text, page_html]:
                for pattern in email_patterns:
                    matches = re.findall(pattern, source, re.IGNORECASE)
                    for match in matches:
                        clean_email = match.replace(' ', '').lower()
                        if '@' in clean_email and '.' in clean_email.split('@')[1]:
                            # Filtrer les faux emails
                            if not any(fake in clean_email for fake in ['example', 'test', 'noreply', 'javascript']):
                                lawyer_data['email'] = clean_email
                                break
                    if lawyer_data['email']:
                        break
                if lawyer_data['email']:
                    break
            
            # === EXTRACTION TÉLÉPHONE ===
            phone_patterns = [
                r'(\+33|0)[1-9](?:[.\s-]?\d{2}){4}',
                r'\b0[1-9](?:\s?\d{2}){4}\b'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    clean_phone = re.sub(r'[^\d+]', '', match)
                    if len(clean_phone) >= 10:
                        lawyer_data['telephone'] = match.strip()
                        break
                if lawyer_data['telephone']:
                    break
            
            # === EXTRACTION ADRESSE ===
            # Chercher code postal français + ville
            address_matches = re.findall(r'\d{5}\s+[A-Za-zÀ-ÿ\s\-]+', page_text)
            if address_matches:
                lawyer_data['adresse'] = address_matches[0].strip()
            
            # === EXTRACTION ANNÉE D'INSCRIPTION ===
            year_patterns = [
                r'inscrit.{0,20}(\d{4})',
                r'barreau.{0,30}(\d{4})',
                r'serment.{0,20}(\d{4})',
                r'admission.{0,20}(\d{4})'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for year_str in matches:
                    year = int(year_str)
                    if 1950 <= year <= 2024:
                        lawyer_data['annee_inscription'] = year_str
                        break
                if lawyer_data['annee_inscription']:
                    break
            
            # === EXTRACTION SPÉCIALISATIONS ===
            specialization_keywords = [
                'spécialisé', 'spécialité', 'spécialisations', 'domaines',
                'droit civil', 'droit commercial', 'droit pénal', 'droit de la famille',
                'droit immobilier', 'droit du travail', 'droit des affaires', 'droit social'
            ]
            
            lines = page_text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in specialization_keywords):
                    if len(line.strip()) > 15:
                        lawyer_data['specialisations'] = line.strip()
                        break
            
            # === EXTRACTION STRUCTURE/CABINET ===
            structure_keywords = ['cabinet', 'société', 'scp', 'selarl', 'avocat associé']
            for line in lines:
                if any(keyword in line.lower() for keyword in structure_keywords):
                    if len(line.strip()) > 5:
                        lawyer_data['structure'] = line.strip()
                        break
            
            return lawyer_data
            
        except Exception as e:
            if index <= 5:  # Afficher les erreurs pour les premiers profils seulement
                print(f"❌ Erreur extraction {profile_url}: {e}")
            return None
    
    def run_complete_scraping(self):
        """
        Lance le processus complet de scraping :
        1. Scan de toutes les pages de l'annuaire
        2. Extraction individuelle de chaque profil
        """
        print("🚀 DÉMARRAGE SCRAPING PRODUCTION - BARREAU DE BAYONNE")
        print("🎯 Mode: HEADLESS (arrière-plan)")
        print("=" * 60)
        
        if not self.setup_driver():
            return False
        
        try:
            # === PHASE 1: SCAN DE L'ANNUAIRE ===
            print("\n📡 PHASE 1: Scan de toutes les pages de l'annuaire...")
            self.driver.get(self.start_url)
            time.sleep(3)
            self.accept_cookies()
            
            all_profile_links = self.scan_all_directory_pages()
            
            if not all_profile_links:
                print("❌ Aucun profil d'avocat trouvé")
                return False
            
            # === PHASE 2: EXTRACTION INDIVIDUELLE ===
            print(f"\n🎯 PHASE 2: Extraction individuelle de {len(all_profile_links)} profils...")
            start_time = datetime.now()
            
            for index, profile_url in enumerate(all_profile_links, 1):
                lawyer_data = self.extract_lawyer_details(profile_url, index, len(all_profile_links))
                
                if lawyer_data and lawyer_data['nom']:
                    self.lawyers_data.append(lawyer_data)
                    
                    # Affichage périodique du progrès
                    if index % 25 == 0:
                        elapsed = datetime.now() - start_time
                        rate = index / elapsed.total_seconds() * 60  # profils/minute
                        remaining_minutes = (len(all_profile_links) - index) / rate if rate > 0 else 0
                        print(f"📈 Progrès: {index}/{len(all_profile_links)} ({index/len(all_profile_links)*100:.1f}%) - "
                              f"Vitesse: {rate:.1f}/min - ETA: {remaining_minutes:.0f}min")
                
                # Pause courte entre profils
                time.sleep(0.3)
            
            total_time = datetime.now() - start_time
            print(f"\n🎉 SCRAPING TERMINÉ!")
            print(f"⏱️  Temps total: {total_time}")
            print(f"📊 Avocats extraits: {len(self.lawyers_data)}")
            
            # Statistiques rapides
            emails_count = len([l for l in self.lawyers_data if l['email']])
            phones_count = len([l for l in self.lawyers_data if l['telephone']])
            print(f"📧 Avec email: {emails_count}")
            print(f"📞 Avec téléphone: {phones_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fermé")
    
    def save_all_data(self):
        """
        Sauvegarde toutes les données extraites dans différents formats
        avec génération d'un rapport détaillé
        """
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(self.lawyers_data)
        
        print(f"\n💾 SAUVEGARDE DE {count} AVOCATS...")
        
        # === FICHIER CSV ===
        csv_filename = f"BAYONNE_PRODUCTION_{count}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = self.lawyers_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        print(f"✅ CSV généré: {csv_filename}")
        
        # === FICHIER JSON ===
        json_filename = f"BAYONNE_PRODUCTION_{count}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, indent=2, ensure_ascii=False)
        print(f"✅ JSON généré: {json_filename}")
        
        # === EMAILS UNIQUEMENT ===
        emails = list(set([lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]))
        if emails:
            emails_filename = f"BAYONNE_EMAILS_SEULEMENT_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as emailfile:
                emailfile.write('\n'.join(sorted(emails)))
            print(f"✅ {len(emails)} emails uniques: {emails_filename}")
        
        # === RAPPORT COMPLET ===
        report_filename = f"BAYONNE_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"=== BARREAU DE BAYONNE - SCRAPING COMPLET ===\n")
            reportfile.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"URL source: {self.start_url}\n")
            reportfile.write(f"Mode: PRODUCTION HEADLESS\n\n")
            
            # Statistiques globales
            reportfile.write(f"STATISTIQUES GÉNÉRALES:\n")
            reportfile.write(f"- Nombre total d'avocats: {count}\n")
            
            emails_count = len([l for l in self.lawyers_data if l['email']])
            reportfile.write(f"- Avec email: {emails_count} ({emails_count/count*100:.1f}%)\n")
            
            phones_count = len([l for l in self.lawyers_data if l['telephone']])
            reportfile.write(f"- Avec téléphone: {phones_count} ({phones_count/count*100:.1f}%)\n")
            
            addresses_count = len([l for l in self.lawyers_data if l['adresse']])
            reportfile.write(f"- Avec adresse: {addresses_count} ({addresses_count/count*100:.1f}%)\n")
            
            specs_count = len([l for l in self.lawyers_data if l['specialisations']])
            reportfile.write(f"- Avec spécialisations: {specs_count} ({specs_count/count*100:.1f}%)\n")
            
            years_count = len([l for l in self.lawyers_data if l['annee_inscription']])
            reportfile.write(f"- Avec année inscription: {years_count} ({years_count/count*100:.1f}%)\n\n")
            
            # Répartition géographique
            cities = {}
            for lawyer in self.lawyers_data:
                if lawyer['adresse']:
                    for city in ['BAYONNE', 'BIARRITZ', 'ANGLET', 'SAINT-JEAN-DE-LUZ', 'PAU']:
                        if city in lawyer['adresse'].upper():
                            cities[city] = cities.get(city, 0) + 1
                            break
            
            if cities:
                reportfile.write(f"RÉPARTITION GÉOGRAPHIQUE:\n")
                for city, city_count in sorted(cities.items(), key=lambda x: x[1], reverse=True):
                    reportfile.write(f"- {city}: {city_count} avocats ({city_count/count*100:.1f}%)\n")
                reportfile.write(f"\n")
            
            # Liste détaillée
            reportfile.write(f"LISTE COMPLÈTE DES AVOCATS:\n")
            reportfile.write(f"=" * 80 + "\n")
            
            for i, lawyer in enumerate(self.lawyers_data, 1):
                reportfile.write(f"\n{i:3d}. {lawyer['prenom']} {lawyer['nom']}\n")
                
                if lawyer['email']:
                    reportfile.write(f"     📧 Email: {lawyer['email']}\n")
                if lawyer['telephone']:
                    reportfile.write(f"     📞 Téléphone: {lawyer['telephone']}\n")
                if lawyer['adresse']:
                    reportfile.write(f"     🏠 Adresse: {lawyer['adresse']}\n")
                if lawyer['annee_inscription']:
                    reportfile.write(f"     📅 Inscription: {lawyer['annee_inscription']}\n")
                if lawyer['specialisations']:
                    spec_text = lawyer['specialisations'][:200] + "..." if len(lawyer['specialisations']) > 200 else lawyer['specialisations']
                    reportfile.write(f"     ⚖️  Spécialisations: {spec_text}\n")
                if lawyer['structure']:
                    reportfile.write(f"     🏢 Structure: {lawyer['structure']}\n")
                
                reportfile.write(f"     🔗 Source: {lawyer['url_source']}\n")
        
        print(f"✅ Rapport complet: {report_filename}")
        
        print(f"\n🎯 RÉSUMÉ DES FICHIERS GÉNÉRÉS:")
        print(f"   📊 {csv_filename} (format Excel/tableur)")
        print(f"   📋 {json_filename} (format programmation)")
        if emails:
            print(f"   📧 {emails_filename} (emails seuls)")
        print(f"   📄 {report_filename} (rapport détaillé)")

def main():
    """
    Fonction principale - Lance automatiquement le scraping complet
    du barreau de Bayonne
    """
    print("🏛️  SCRAPER PRODUCTION - BARREAU DE BAYONNE")
    print("=" * 80)
    print("🎯 OBJECTIF: Extraire TOUS les avocats du barreau")
    print("🚀 MODE: Headless (arrière-plan)")
    print("📊 DONNÉES: Nom, prénom, email, téléphone, adresse, spécialisations")
    print("💾 SORTIE: CSV, JSON, emails, rapport détaillé")
    print("=" * 80)
    
    # Initialisation et lancement du scraper
    scraper = BayonneLawyerScraper()
    
    if scraper.run_complete_scraping():
        scraper.save_all_data()
        print("\n" + "=" * 80)
        print("🎉 MISSION ACCOMPLIE!")
        print("✅ Scraping complet réussi")
        print("📁 Consultez les fichiers générés pour les résultats")
        print("💡 Les données sont prêtes pour vos analyses et traitements")
        print("=" * 80)
        return True
    else:
        print("\n❌ ÉCHEC DU SCRAPING")
        print("💡 Vérifiez votre connexion internet et ChromeDriver")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)