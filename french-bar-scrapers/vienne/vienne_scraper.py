#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU DE VIENNE - VERSION FINALE
==========================================

Ce script permet de scraper tous les avocats du barreau de Vienne avec :
✅ Prénoms composés complets (Pierre-Lyonel, Jean-Philippe, etc.)  
✅ Spécialisations nettoyées (sans préfixes indésirables)
✅ Navigation automatique entre toutes les pages
✅ Mode headless (invisible) par défaut
✅ Sauvegarde complète : CSV, JSON, emails, rapport

URL source: https://www.avocats-vienne.com/annuaire

Usage:
    python3 vienne_scraper.py
    
Dépendances:
    pip install selenium beautifulsoup4 requests
    
Fichiers générés:
    - VIENNE_FINAL_[nombre]_avocats_[timestamp].csv    (données complètes)
    - VIENNE_FINAL_[nombre]_avocats_[timestamp].json   (format JSON)  
    - VIENNE_FINAL_[nombre]_avocats_[timestamp]_emails.txt (emails seuls)
    - VIENNE_FINAL_[nombre]_avocats_[timestamp]_rapport.txt (rapport détaillé)
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random

class VienneBarScraper:
    """Scraper pour le barreau de Vienne"""
    
    def __init__(self, headless=True, test_mode=False):
        self.base_url = "https://www.avocats-vienne.com"
        self.annuaire_url = "https://www.avocats-vienne.com/annuaire"
        self.headless = headless
        self.test_mode = test_mode
        self.max_lawyers_test = 5 if test_mode else None
        self.lawyers_data = []
        self.total_pages = 4  # Nombre de pages connu
        
        # Configuration Chrome optimisée
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = None
        
    def init_driver(self):
        """Initialise le driver Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print(f"❌ Erreur initialisation driver: {e}")
            return False
    
    def accept_cookies(self):
        """Accepte les cookies automatiquement"""
        try:
            cookie_buttons = [
                "//button[contains(text(), 'Accepter')]",
                "//button[contains(text(), 'Accept')]", 
                "//button[contains(text(), 'OK')]",
                "//a[contains(text(), 'Accepter')]"
            ]
            
            for xpath in cookie_buttons:
                try:
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    element.click()
                    print("✓ Cookies acceptés")
                    time.sleep(1)
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            return True
        except Exception as e:
            return True
    
    def navigate_to_page(self, page_num):
        """Navigue vers une page spécifique"""
        try:
            if page_num == 1:
                url = self.annuaire_url
            else:
                url = f"{self.annuaire_url}?ipstart={page_num}"
            
            print(f"📖 Page {page_num}/{self.total_pages}: {url}")
            self.driver.get(url)
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Erreur navigation page {page_num}: {e}")
            return False
    
    def find_lawyer_elements(self):
        """Trouve les éléments d'avocats sur la page"""
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='item']")
            
            # Filtrer pour garder seulement les vrais avocats
            lawyer_elements = []
            for elem in elements:
                try:
                    text = elem.text.strip()
                    if ('Maître' in text or 'Me ' in text) and len(text) > 20:
                        lawyer_elements.append(elem)
                except:
                    continue
            
            return lawyer_elements[:self.max_lawyers_test] if self.test_mode else lawyer_elements
        except Exception as e:
            print(f"❌ Erreur recherche avocats: {e}")
            return []
    
    def clean_specializations(self, raw_specs):
        """🧹 Nettoie et structure les spécialisations"""
        if not raw_specs:
            return ""
        
        cleaned_specs = []
        
        # Diviser par les séparateurs communs
        parts = re.split(r'[|•\-]\s*', raw_specs)
        
        for part in parts:
            part = part.strip()
            
            # Supprimer les préfixes indésirables
            prefixes_to_remove = [
                r'^Domaine\(s\)\s+de\s+compétences?\s*',
                r'^Compétences?\s*',
                r'^Spécialisations?\s*', 
                r'^Domaines?\s*',
                r'^Activités?\s*',
                r'^\-\s*',
                r'^\•\s*',
                r'^\|\s*'
            ]
            
            for prefix in prefixes_to_remove:
                part = re.sub(prefix, '', part, flags=re.IGNORECASE).strip()
            
            # Garder seulement les vraies spécialisations
            if (len(part) > 5 and len(part) < 120 and 
                any(keyword in part.lower() for keyword in 
                    ['droit', 'procédure', 'contrat', 'famille', 'pénal', 'civil', 
                     'commercial', 'immobilier', 'travail', 'fiscal', 'social'])):
                
                # Nettoyer la ponctuation
                part = re.sub(r'^[\-\•\|\.\,\;\:]\s*', '', part).strip()
                part = re.sub(r'[\.\,\;\:]\s*$', '', part).strip()
                
                if part and part not in cleaned_specs:
                    cleaned_specs.append(part)
        
        # Max 4 spécialisations, séparées par " ; "
        return ' ; '.join(cleaned_specs[:4])
    
    def extract_name_correctly(self, full_name_text):
        """🔧 EXTRACTION CORRECTE DES NOMS COMPOSÉS"""
        prenom = ""
        nom = ""
        
        if not full_name_text:
            return prenom, nom
        
        # Nettoyer le texte
        clean_name = full_name_text.replace('Maître', '').replace('Me ', '').strip()
        
        # Patterns spécialisés pour prénoms composés
        name_patterns = [
            # Pattern 1: NOM Prénom-Composé (ex: LEVEQUE Pierre-Lyonel)
            r'^([A-ZÀ-Ÿ\-]+(?:\s+[A-ZÀ-Ÿ\-]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\-[A-ZÀ-Ÿ][a-zà-ÿ\-]+)+)$',
            
            # Pattern 2: Prénom-Composé NOM (ex: Pierre-Lyonel LEVEQUE)  
            r'^([A-ZÀ-Ÿ][a-zà-ÿ\-]+(?:\-[A-ZÀ-Ÿ][a-zà-ÿ\-]+)+)\s+([A-ZÀ-Ÿ\-]+(?:\s+[A-ZÀ-Ÿ\-]+)*)$',
            
            # Pattern 3: NOM Prénom (ex: BADIN Pierre)
            r'^([A-ZÀ-Ÿ\-]+(?:\s+[A-ZÀ-Ÿ\-]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ\-]+)$',
            
            # Pattern 4: Prénom NOM (ex: Pierre BADIN)
            r'^([A-ZÀ-Ÿ][a-zà-ÿ\-]+)\s+([A-ZÀ-Ÿ\-]+(?:\s+[A-ZÀ-Ÿ\-]+)*)$',
        ]
        
        for i, pattern in enumerate(name_patterns):
            match = re.search(pattern, clean_name)
            if match:
                part1, part2 = match.groups()
                part1 = part1.strip()
                part2 = part2.strip()
                
                # Logique de décision
                if part1.isupper() and not part2.isupper():
                    nom = part1
                    prenom = part2
                elif part2.isupper() and not part1.isupper():
                    prenom = part1
                    nom = part2
                elif '-' in part1 and part2.isupper():
                    prenom = part1
                    nom = part2
                elif '-' in part2 and part1.isupper():
                    nom = part1
                    prenom = part2
                elif '-' in part1:
                    prenom = part1
                    nom = part2
                elif '-' in part2:
                    nom = part1
                    prenom = part2
                else:
                    prenom = part1
                    nom = part2
                break
        
        # Approche de secours si aucun pattern ne fonctionne
        if not prenom and not nom:
            words = clean_name.split()
            if len(words) >= 2:
                for i, word in enumerate(words):
                    if word.isupper() and len(word) > 1:
                        nom = ' '.join(words[i:])
                        prenom = ' '.join(words[:i])
                        break
                
                if not nom:
                    mid = len(words) // 2
                    prenom = ' '.join(words[:mid]) if mid > 0 else words[0]
                    nom = ' '.join(words[mid:])
        
        return prenom.strip(), nom.strip()
    
    def extract_lawyer_info_from_detail_page(self, url):
        """📋 Extrait toutes les informations depuis la page de détail"""
        lawyer_info = {
            'prenom': '',
            'nom': '',
            'annee_inscription': '',
            'specialisations': '',
            'structure': '',
            'source_url': url,
            'telephone': '',
            'email': '',
            'adresse': ''
        }
        
        try:
            # Ouvrir dans un nouvel onglet
            self.driver.execute_script("window.open(arguments[0]);", url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)
            
            # Récupérer le contenu
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                page_text = body.text
                page_html = self.driver.page_source
                soup = BeautifulSoup(page_html, 'html.parser')
            except Exception as e:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return lawyer_info
            
            # 👤 EXTRACTION NOM ET PRÉNOM
            title_selectors = ['h1', 'h2', '.title', '.nom', '[class*="nom"]', '[class*="title"]']
            full_name = ""
            
            for selector in title_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text().strip()
                        if 'Maître' in text or 'Me ' in text:
                            full_name = text
                            break
                    if full_name:
                        break
                except:
                    continue
            
            if not full_name:
                lines = page_text.split('\n')
                for line in lines[:10]:
                    line = line.strip()
                    if ('Maître' in line or 'Me ' in line) and len(line) < 100:
                        full_name = line
                        break
            
            # Utiliser la méthode d'extraction correcte
            if full_name:
                prenom, nom = self.extract_name_correctly(full_name)
                lawyer_info['prenom'] = prenom
                lawyer_info['nom'] = nom
            
            # 📧 EMAIL
            email_patterns = [
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, page_html + page_text, re.IGNORECASE)
                if matches:
                    for email in matches:
                        if '@' in email and '.' in email.split('@')[1]:
                            lawyer_info['email'] = email
                            break
                if lawyer_info['email']:
                    break
            
            # 📞 TÉLÉPHONE
            phone_patterns = [
                r'(\d{2}[.\s\-]?\d{2}[.\s\-]?\d{2}[.\s\-]?\d{2}[.\s\-]?\d{2})',
                r'(\+33[.\s\-]?\d[.\s\-]?\d{2}[.\s\-]?\d{2}[.\s\-]?\d{2}[.\s\-]?\d{2})'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    phone_clean = re.sub(r'[.\s\-]', '', match)
                    if len(phone_clean) == 10 and phone_clean.startswith('0'):
                        lawyer_info['telephone'] = match
                        break
                if lawyer_info['telephone']:
                    break
            
            # 📅 ANNÉE D'INSCRIPTION
            year_patterns = [
                r'inscrit[e]?\s+(?:au barreau|depuis|en)\s+(\d{4})',
                r'(?:barreau|admission|serment).*?(\d{4})',
                r'(\d{4})'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        year = int(match)
                        if 1950 <= year <= 2025:
                            lawyer_info['annee_inscription'] = str(year)
                            break
                    except:
                        continue
                if lawyer_info['annee_inscription']:
                    break
            
            # 🎯 SPÉCIALISATIONS (NETTOYÉES)
            raw_specializations = ""
            
            # Méthode 1: Balises spécifiques
            spec_selectors = [
                '.competences', '.specialisations', '.domaines', 
                '[class*="competence"]', '[class*="specialisation"]', '[class*="domaine"]'
            ]
            
            for selector in spec_selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text().strip()
                        if len(text) > 10:
                            raw_specializations += " " + text
                except:
                    continue
            
            # Méthode 2: Analyse par sections
            if not raw_specializations:
                lines = page_text.split('\n')
                spec_lines = []
                
                for i, line in enumerate(lines):
                    line_clean = line.strip()
                    line_lower = line_clean.lower()
                    
                    if any(keyword in line_lower for keyword in ['compétence', 'spécialisation', 'domaine']):
                        spec_lines.append(line_clean)
                        
                        for j in range(i+1, min(i+8, len(lines))):
                            next_line = lines[j].strip()
                            next_lower = next_line.lower()
                            
                            if any(stop_word in next_lower for stop_word in ['contact', 'adresse', 'téléphone']):
                                break
                                
                            if (len(next_line) > 5 and len(next_line) < 120 and
                                (any(keyword in next_lower for keyword in ['droit', 'procédure', 'contrat', 'famille', 'pénal', 'civil']) or
                                 next_line.startswith(('-', '•', '▪')))):
                                spec_lines.append(next_line)
                        break
                
                raw_specializations = '\n'.join(spec_lines)
            
            # Nettoyer avec la méthode améliorée
            lawyer_info['specialisations'] = self.clean_specializations(raw_specializations)
            
            # 🏢 EXTRACTION STRUCTURE/CABINET
            struct_patterns = [
                r'cabinet\s+([^\n.]+)',
                r'société\s+([^\n.]+)', 
                r'scp\s+([^\n.]+)',
                r'selarl\s+([^\n.]+)',
                r'avocat[e]?\s+associé[e]?\s+([^\n.]+)'
            ]
            
            for pattern in struct_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    structure = match.group(1).strip()
                    if 3 < len(structure) < 100:
                        lawyer_info['structure'] = structure
                        break
            
            # Fermer l'onglet et revenir au principal
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(1)
            
            return lawyer_info
            
        except Exception as e:
            print(f"  ✗ Erreur extraction: {e}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return lawyer_info
    
    def scrape_all_lawyers(self):
        """🚀 Lance le scraping complet de tous les avocats"""
        if not self.init_driver():
            return []
        
        try:
            print("🏛️  SCRAPER BARREAU DE VIENNE")
            print("=" * 35)
            print(f"Mode: {'TEST' if self.test_mode else 'PRODUCTION'}")
            print(f"Headless: {self.headless}")
            print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Page d'accueil
            print(f"\n📱 Chargement: {self.annuaire_url}")
            self.driver.get(self.annuaire_url)
            self.accept_cookies()
            
            # Scraping de toutes les pages
            for page_num in range(1, self.total_pages + 1):
                try:
                    print(f"\n📖 === PAGE {page_num}/{self.total_pages} ===")
                    
                    if page_num > 1:
                        if not self.navigate_to_page(page_num):
                            continue
                    
                    # Avocats sur cette page
                    lawyer_elements = self.find_lawyer_elements()
                    print(f"👥 {len(lawyer_elements)} avocats trouvés")
                    
                    if not lawyer_elements:
                        continue
                    
                    # Traitement de chaque avocat
                    for i, element in enumerate(lawyer_elements):
                        try:
                            # URL de détail
                            try:
                                link = element.find_element(By.CSS_SELECTOR, "a")
                                detail_url = link.get_attribute('href')
                                if not detail_url.startswith('http'):
                                    detail_url = self.base_url + ('/' if not detail_url.startswith('/') else '') + detail_url
                            except:
                                continue
                            
                            print(f"  👤 Avocat {len(self.lawyers_data)+1}...")
                            
                            # Extraction complète
                            lawyer_info = self.extract_lawyer_info_from_detail_page(detail_url)
                            
                            if lawyer_info['prenom'] and lawyer_info['nom']:
                                prenom = lawyer_info['prenom']
                                nom = lawyer_info['nom']
                                composed_mark = "🎯" if '-' in prenom else "✓"
                                print(f"     {composed_mark} {prenom} {nom}")
                                
                                if lawyer_info['email']:
                                    print(f"       📧 {lawyer_info['email']}")
                            
                            self.lawyers_data.append(lawyer_info)
                            
                            # Pause entre requêtes
                            time.sleep(random.uniform(1, 3))
                            
                            # Limite pour les tests
                            if self.test_mode and len(self.lawyers_data) >= self.max_lawyers_test:
                                return self.lawyers_data
                            
                        except Exception as e:
                            print(f"  ✗ Erreur avocat {i+1}: {e}")
                            continue
                    
                    print(f"📊 Total: {len(self.lawyers_data)} avocats")
                    
                    # Pause entre pages
                    if page_num < self.total_pages:
                        time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"❌ Erreur page {page_num}: {e}")
                    continue
            
            print(f"\n🎉 SCRAPING TERMINÉ!")
            print(f"📊 Total: {len(self.lawyers_data)} avocats extraits")
            
            return self.lawyers_data
            
        except Exception as e:
            print(f"💥 ERREUR: {e}")
            return []
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """💾 Sauvegarde complète des résultats"""
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_text = "TEST" if self.test_mode else "FINAL"
        base_name = f"VIENNE_{mode_text}_{len(self.lawyers_data)}_avocats_{timestamp}"
        
        print(f"\n💾 SAUVEGARDE DES RÉSULTATS")
        
        # CSV (Excel)
        csv_file = f"{base_name}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.lawyers_data[0].keys())
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        print(f"✓ CSV: {csv_file}")
        
        # JSON
        json_file = f"{base_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        print(f"✓ JSON: {json_file}")
        
        # Emails uniquement
        emails = list(set([l['email'] for l in self.lawyers_data if l.get('email') and '@' in l['email']]))
        if emails:
            emails_file = f"{base_name}_emails.txt"
            with open(emails_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(emails)))
            print(f"✓ Emails: {emails_file} ({len(emails)} emails uniques)")
        
        # Rapport complet
        rapport_file = f"{base_name}_rapport.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write("RAPPORT SCRAPING BARREAU DE VIENNE\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"🕐 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🏛️  Source: {self.annuaire_url}\n")
            f.write(f"📊 Total avocats: {len(self.lawyers_data)}\n")
            f.write(f"📄 Pages parcourues: {self.total_pages}\n\n")
            
            # Statistiques
            with_names = len([l for l in self.lawyers_data if l.get('prenom') and l.get('nom')])
            with_emails = len([l for l in self.lawyers_data if l.get('email')])
            with_phones = len([l for l in self.lawyers_data if l.get('telephone')])
            with_years = len([l for l in self.lawyers_data if l.get('annee_inscription')])
            with_specs = len([l for l in self.lawyers_data if l.get('specialisations')])
            
            # Noms composés
            composed_names = [l for l in self.lawyers_data if '-' in l.get('prenom', '')]
            
            f.write("📈 STATISTIQUES:\n")
            f.write(f"   👤 Noms complets: {with_names} ({with_names/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"   📧 Emails: {with_emails} ({with_emails/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"   📞 Téléphones: {with_phones} ({with_phones/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"   📅 Années inscription: {with_years} ({with_years/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"   🎯 Spécialisations: {with_specs} ({with_specs/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"   🎯 Prénoms composés: {len(composed_names)} avocats\n\n")
            
            # Prénoms composés trouvés
            if composed_names:
                f.write("🎯 PRÉNOMS COMPOSÉS EXTRAITS:\n")
                for lawyer in composed_names:
                    f.write(f"   - {lawyer['prenom']} {lawyer['nom']}\n")
                f.write("\n")
            
            # Échantillon
            f.write("📋 ÉCHANTILLON (10 premiers):\n")
            for i, lawyer in enumerate(self.lawyers_data[:10]):
                f.write(f"{i+1:2d}. {lawyer.get('prenom', '')} {lawyer.get('nom', '')}\n")
                f.write(f"    📧 {lawyer.get('email', 'N/A')}\n")
                if lawyer.get('specialisations'):
                    specs = lawyer['specialisations'][:60] + "..." if len(lawyer['specialisations']) > 60 else lawyer['specialisations']
                    f.write(f"    🎯 {specs}\n")
                f.write("\n")
        
        print(f"✓ Rapport: {rapport_file}")
        
        # Résumé final
        print(f"\n🎯 RÉSUMÉ:")
        print(f"   📊 Total: {len(self.lawyers_data)} avocats")
        print(f"   📧 Emails: {len(emails)}")
        print(f"   🎯 Prénoms composés: {len(composed_names)}")
        print(f"   📁 Fichiers créés: 4")


def main():
    """Fonction principale"""
    print("🏛️  SCRAPER BARREAU DE VIENNE")
    print("=" * 35)
    print("🎯 Ce script extrait tous les avocats avec:")
    print("   ✅ Prénoms composés complets (Pierre-Lyonel, etc.)")
    print("   ✅ Spécialisations nettoyées")
    print("   ✅ Navigation automatique entre pages")
    print("   ✅ Mode invisible par défaut")
    print()
    
    # Demander le mode
    try:
        mode_choice = input("Choisir le mode:\n1. Production (tous les avocats)\n2. Test (5 avocats)\n\nChoix (1/2): ").strip()
        test_mode = (mode_choice == "2")
        
        print(f"\nMode sélectionné: {'TEST' if test_mode else 'PRODUCTION'}")
        print("Démarrage dans 3 secondes...")
        time.sleep(3)
        
    except (KeyboardInterrupt, EOFError):
        print("\n❌ Arrêt demandé")
        return
    
    # Lancement du scraper
    scraper = VienneBarScraper(headless=True, test_mode=test_mode)
    
    try:
        print(f"\n🚀 DÉMARRAGE - {datetime.now().strftime('%H:%M:%S')}")
        results = scraper.scrape_all_lawyers()
        
        if results:
            print(f"\n🎉 SUCCÈS!")
            scraper.save_results()
            print(f"\n✅ Scraping terminé avec succès!")
            
        else:
            print("\n💥 ÉCHEC: Aucun résultat")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ ARRÊT UTILISATEUR")
        if scraper.lawyers_data:
            print(f"💾 Sauvegarde des {len(scraper.lawyers_data)} avocats...")
            scraper.save_results()
        
    except Exception as e:
        print(f"\n💥 ERREUR: {e}")
        if scraper.lawyers_data:
            print(f"💾 Sauvegarde de secours...")
            scraper.save_results()


if __name__ == "__main__":
    main()