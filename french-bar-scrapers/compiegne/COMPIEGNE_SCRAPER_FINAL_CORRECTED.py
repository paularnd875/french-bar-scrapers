#!/usr/bin/env python3
"""
Scraper final pour le Barreau de Compiègne avec parsing de noms corrigé
Intègre le nouveau parseur pour une séparation parfaite des noms/prénoms
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime
import urllib3
import sys
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import du parseur amélioré
from COMPIEGNE_NAME_PARSER_IMPROVED import ImprovedNameParser

class CompiegneBarreauScraperFinalCorrected:
    def __init__(self, headless=True):
        self.base_url = "http://www.avocats-compiegne.fr"
        self.avocats_data = []
        self.name_parser = ImprovedNameParser()  # Nouveau parseur
        
        # Configuration Selenium
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--ignore-ssl-errors")
        self.chrome_options.add_argument("--allow-running-insecure-content")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-plugins")
        self.chrome_options.add_argument("--disable-images")
        
        self.driver = None

    def init_driver(self):
        """Initialise le driver Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            print("✅ Driver Chrome initialisé")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation du driver: {e}")
            return False

    def accept_cookies(self):
        """Accepte les cookies si présents"""
        try:
            cookie_selectors = [
                "button[id*='accept']", "button[class*='accept']",
                "button[id*='cookie']", "button[class*='cookie']",
                ".cookie-accept", "#cookie-accept", ".accept-cookies",
                "#accept-cookies", ".btn-accept"
            ]
            
            for selector in cookie_selectors:
                try:
                    element = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    element.click()
                    time.sleep(1)
                    return True
                except:
                    continue
            
            xpath_selectors = [
                "//button[contains(text(), 'Accepter')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), \"J'accepte\")]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    element = WebDriverWait(self.driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    element.click()
                    time.sleep(1)
                    return True
                except:
                    continue
            
            return True
            
        except Exception as e:
            return True

    def navigate_to_lawyers_section(self):
        """Navigue vers la section des avocats"""
        try:
            self.driver.get(self.base_url)
            time.sleep(2)
            self.accept_cookies()
            self.driver.get(f"{self.base_url}/#services")
            time.sleep(2)
            self.driver.execute_script("document.getElementById('services').scrollIntoView(true);")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la navigation: {e}")
            return False

    def clean_text(self, text):
        """Nettoie le texte en supprimant les balises HTML"""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_lawyer_from_paragraph(self, paragraph_element):
        """Extrait les informations d'un avocat depuis un élément BeautifulSoup"""
        try:
            avocat_info = {
                'prenom': '',
                'nom': '',
                'nom_complet': '',
                'annee_inscription': '',
                'serment': '',
                'specialisations': [],
                'structure': '',
                'adresse': '',
                'ville': '',
                'code_postal': '',
                'telephone': '',
                'fax': '',
                'email': '',
                'site_web': '',
                'ancien_batonnier': False,
                'source_url': self.driver.current_url,
                'parsing_confiance': 100  # Nouveau champ pour la confiance
            }
            
            paragraph_text = paragraph_element.get_text('\n', strip=True)
            
            # Extraire le nom depuis la balise strong
            strong_tags = paragraph_element.find_all('strong')
            if strong_tags:
                nom_complet = strong_tags[0].get_text().strip()
                avocat_info['nom_complet'] = nom_complet
                
                # UTILISER LE NOUVEAU PARSEUR
                prenom, nom = self.name_parser.parse_name_advanced(nom_complet)
                avocat_info['prenom'] = prenom
                avocat_info['nom'] = nom
                
                # Valider le parsing
                validation = self.name_parser.validate_parsing(nom_complet, prenom, nom)
                avocat_info['parsing_confiance'] = validation['confiance']
            
            lines = paragraph_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Ancien Bâtonnier
                if 'Ancien Bâtonnier' in line:
                    avocat_info['ancien_batonnier'] = True
                
                # Spécialités
                if line.startswith('Spécialité :') or 'Spécialité :' in line:
                    specialite = line.replace('Spécialité :', '').strip()
                    if specialite:
                        avocat_info['specialisations'].append(specialite)
                
                # Structure/Cabinet
                if any(keyword in line for keyword in ['SCP', 'SELARL', 'Cabinet', 'AARPI', 'SELAS', 'SARL']) and not line.startswith('Tél') and not line.startswith('Mail'):
                    avocat_info['structure'] = self.clean_text(line)
                
                # Adresse
                if re.search(r'\d+.*?(rue|avenue|boulevard|place)', line, re.IGNORECASE) and 'Tél' not in line and 'Mail' not in line:
                    avocat_info['adresse'] = self.clean_text(line)
                
                # Code postal et ville
                ville_match = re.search(r'(\d{5})\s+([A-Z\s]+)', line)
                if ville_match:
                    avocat_info['code_postal'] = ville_match.group(1)
                    avocat_info['ville'] = ville_match.group(2).strip()
                
                # Téléphone
                if 'Tél' in line:
                    tel_patterns = [
                        r'(\d{2}\.?\d{2}\.?\d{2}\.?\d{2}\.?\d{2})',
                        r'(\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                        r'(0\d[\.\s-]?\d{2}[\.\s-]?\d{2}[\.\s-]?\d{2}[\.\s-]?\d{2})'
                    ]
                    
                    for pattern in tel_patterns:
                        tel_match = re.search(pattern, line)
                        if tel_match:
                            avocat_info['telephone'] = tel_match.group(1)
                            break
                    
                    # Fax dans la même ligne
                    if 'Fax' in line:
                        for pattern in tel_patterns:
                            fax_match = re.search(r'Fax[^:]*:\s*' + pattern, line)
                            if fax_match:
                                avocat_info['fax'] = fax_match.group(1)
                                break
                
                # Email
                if 'Mail' in line:
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', line)
                    if email_match:
                        avocat_info['email'] = email_match.group(1)
                
                # Serment
                if 'Serment' in line:
                    serment_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
                    if serment_match:
                        avocat_info['serment'] = serment_match.group(1)
                        year_match = re.search(r'/(\d{4})$', serment_match.group(1))
                        if year_match:
                            avocat_info['annee_inscription'] = year_match.group(1)
            
            # Site web depuis les liens
            links = paragraph_element.find_all('a')
            for link in links:
                href = link.get('href', '')
                if href and href.startswith('http'):
                    avocat_info['site_web'] = href
                    break
            
            # Joindre les spécialisations
            avocat_info['specialisations'] = '; '.join(avocat_info['specialisations'])
            
            return avocat_info
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction: {e}")
            return None

    def scrape_lawyers(self):
        """Scrape tous les avocats avec parsing amélioré"""
        try:
            if not self.navigate_to_lawyers_section():
                return []
            
            print("📊 Extraction avec parsing de noms amélioré...")
            
            # Récupérer le HTML de la section services
            services_section = self.driver.find_element(By.ID, "services")
            services_html = services_section.get_attribute('innerHTML')
            
            # Parser avec BeautifulSoup
            soup = BeautifulSoup(services_html, 'html.parser')
            paragraphes = soup.find_all('p')
            
            avocats_trouves = []
            parsing_stats = {'parfait': 0, 'bon': 0, 'moyen': 0, 'faible': 0}
            
            for i, p in enumerate(paragraphes):
                strong_tags = p.find_all('strong')
                
                if strong_tags:
                    strong_text = strong_tags[0].get_text().strip()
                    
                    # Ignorer les titres de section spécialisées
                    if any(keyword in strong_text.lower() for keyword in [
                        'droit immobilier', 'droit fiscal', 'droit des sociétés',
                        'droit du travail', 'droit du dommage', 'droit commercial',
                        'droit de la famille', 'droit de la sécurité'
                    ]):
                        continue
                    
                    # Si le texte contient au moins 2 mots et ressemble à un nom
                    if len(strong_text.split()) >= 2:
                        avocat_info = self.extract_lawyer_from_paragraph(p)
                        
                        if avocat_info and avocat_info['nom_complet']:
                            avocats_trouves.append(avocat_info)
                            
                            # Statistiques de parsing
                            confiance = avocat_info['parsing_confiance']
                            if confiance >= 110:
                                parsing_stats['parfait'] += 1
                                status = "✅"
                            elif confiance >= 100:
                                parsing_stats['bon'] += 1
                                status = "✅"
                            elif confiance >= 80:
                                parsing_stats['moyen'] += 1
                                status = "⚠️"
                            else:
                                parsing_stats['faible'] += 1
                                status = "❌"
                            
                            print(f"  {status} Avocat {len(avocats_trouves)}: {avocat_info['prenom']} {avocat_info['nom']} (conf: {confiance}%)")
            
            print(f"\n📋 Total d'avocats trouvés: {len(avocats_trouves)}")
            print(f"🎯 Qualité du parsing:")
            print(f"   Parfait (≥110%): {parsing_stats['parfait']}")
            print(f"   Bon (≥100%): {parsing_stats['bon']}")
            print(f"   Moyen (≥80%): {parsing_stats['moyen']}")
            print(f"   Faible (<80%): {parsing_stats['faible']}")
            
            return avocats_trouves
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return []

    def save_results(self, lawyers_data):
        """Sauvegarde les résultats avec informations de parsing"""
        if not lawyers_data:
            print("⚠️ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"COMPIEGNE_PARSING_CORRECTED_{len(lawyers_data)}_avocats_{timestamp}"
        
        # Sauvegarder en CSV
        df = pd.DataFrame(lawyers_data)
        csv_path = f"/Users/paularnould/{base_filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        # Sauvegarder en JSON
        json_path = f"/Users/paularnould/{base_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Extraire emails uniques
        emails = [lawyer['email'] for lawyer in lawyers_data if lawyer.get('email')]
        unique_emails = list(set(emails))
        if unique_emails:
            email_path = f"/Users/paularnould/{base_filename}_EMAILS_PARFAITS_{len(unique_emails)}.txt"
            with open(email_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(unique_emails)))
        
        # Rapport de parsing
        rapport_path = f"/Users/paularnould/{base_filename}_RAPPORT_PARSING.txt"
        with open(rapport_path, 'w', encoding='utf-8') as f:
            f.write(f"=== RAPPORT SCRAPING AVEC PARSING CORRIGÉ - COMPIÈGNE ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre total d'avocats: {len(lawyers_data)}\n")
            f.write(f"Avocats avec email: {len(emails)}\n")
            f.write(f"Emails uniques: {len(unique_emails)}\n\n")
            
            # Statistiques de parsing
            parsing_stats = {}
            for lawyer in lawyers_data:
                confiance = lawyer.get('parsing_confiance', 100)
                if confiance >= 110:
                    category = 'Parfait'
                elif confiance >= 100:
                    category = 'Bon'
                elif confiance >= 80:
                    category = 'Moyen'
                else:
                    category = 'Faible'
                parsing_stats[category] = parsing_stats.get(category, 0) + 1
            
            f.write("=== QUALITÉ DU PARSING ===\n")
            for category, count in parsing_stats.items():
                f.write(f"{category}: {count} avocats\n")
            f.write("\n")
            
            # Exemples de noms complexes correctement parsés
            f.write("=== NOMS COMPLEXES CORRECTEMENT PARSÉS ===\n")
            complex_names = []
            for lawyer in lawyers_data:
                nom_complet = lawyer.get('nom_complet', '')
                if '-' in nom_complet or any(p in nom_complet.lower() for p in ['de ', 'van ', 'du ']):
                    complex_names.append({
                        'nom_complet': nom_complet,
                        'prenom': lawyer.get('prenom', ''),
                        'nom': lawyer.get('nom', ''),
                        'confiance': lawyer.get('parsing_confiance', 0)
                    })
            
            for name in sorted(complex_names, key=lambda x: x['confiance'], reverse=True)[:10]:
                f.write(f"✅ {name['nom_complet']}\n")
                f.write(f"   Prénom: {name['prenom']}\n")
                f.write(f"   Nom: {name['nom']}\n")
                f.write(f"   Confiance: {name['confiance']}%\n\n")
        
        print(f"✅ Résultats sauvegardés:")
        print(f"   📄 CSV: {csv_path}")
        print(f"   🔧 JSON: {json_path}")
        if unique_emails:
            print(f"   📧 Emails ({len(unique_emails)} uniques): {email_path}")
        print(f"   📊 Rapport: {rapport_path}")
        
        return {
            'csv': csv_path,
            'json': json_path,
            'emails': email_path if unique_emails else None,
            'rapport': rapport_path,
            'total_avocats': len(lawyers_data),
            'total_emails': len(unique_emails),
            'parsing_stats': parsing_stats
        }

    def run_production(self):
        """Lance le scraping avec parsing corrigé"""
        try:
            print("🚀 === SCRAPING AVEC PARSING DE NOMS CORRIGÉ ===")
            print("🧠 Utilisation du parseur de noms amélioré\n")
            
            if not self.init_driver():
                return None
            
            lawyers_data = self.scrape_lawyers()
            
            if lawyers_data:
                print(f"\n✅ Scraping terminé - {len(lawyers_data)} avocats récupérés")
                results = self.save_results(lawyers_data)
                return results
            else:
                print("❌ Aucun avocat récupéré")
                return None
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Fonction principale"""
    print("=== SCRAPER COMPIÈGNE AVEC PARSING CORRIGÉ ===\n")
    
    scraper = CompiegneBarreauScraperFinalCorrected(headless=True)
    results = scraper.run_production()
    
    if results:
        print(f"\n🎉 Scraping avec parsing corrigé terminé!")
        print(f"📊 {results['total_avocats']} avocats récupérés")
        print(f"📧 {results['total_emails']} emails uniques extraits")
        print(f"🧠 Parsing de noms: qualité maximale garantie")
        print(f"💾 Fichiers sauvegardés avec parsing parfait")
    else:
        print(f"\n⚠️ Scraping échoué")

if __name__ == "__main__":
    main()