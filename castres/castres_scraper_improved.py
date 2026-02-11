#!/usr/bin/env python3
"""
Script amélioré pour scraper le barreau de Castres
Phase 2: Extraction complète des informations d'avocats
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CastresScraperImproved:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.lawyers = []
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent pour éviter la détection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
        
    def accept_cookies(self):
        """Gestion de l'acceptation des cookies"""
        print("🍪 Recherche du bandeau de cookies...")
        
        try:
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Rechercher différents sélecteurs possibles pour les cookies
            cookie_selectors = [
                '[id*="cookie"]',
                '[class*="cookie"]',
                '[id*="consent"]',
                '[class*="consent"]',
                '[id*="tarteaucitron"]',
                '[class*="tarteaucitron"]',
                'button[class*="accept"]',
                'button[id*="accept"]',
                'a[class*="accept"]'
            ]
            
            cookie_found = False
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Trouvé élément cookie avec sélecteur: {selector}")
                        for element in elements:
                            if element.is_displayed():
                                print(f"   Texte: {element.text[:100]}")
                                # Chercher un bouton d'acceptation
                                if any(word in element.text.lower() for word in ['accept', 'accepter', 'ok', 'valider']):
                                    try:
                                        element.click()
                                        print("✅ Cookies acceptés!")
                                        cookie_found = True
                                        time.sleep(2)
                                        break
                                    except Exception as e:
                                        print(f"   Erreur clic: {e}")
                        if cookie_found:
                            break
                except Exception as e:
                    continue
            
            if not cookie_found:
                print("ℹ️  Aucun bandeau de cookies trouvé ou déjà accepté")
                
        except Exception as e:
            print(f"❌ Erreur gestion cookies: {e}")
            
        time.sleep(3)
        
    def get_lawyer_links(self):
        """Récupération des liens vers les fiches d'avocats"""
        print("📋 Récupération des liens d'avocats...")
        
        lawyer_links = []
        
        try:
            # Attendre que les éléments soient chargés
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Différents sélecteurs pour trouver les liens des avocats
            selectors = [
                'a[href*="avocat"]',
                'a[href*="profil"]', 
                'a[href*="fiche"]',
                '.lawyer-card a',
                '.avocat-card a',
                '.profile-card a'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"✅ Trouvé {len(elements)} liens avec sélecteur: {selector}")
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and 'avocat' in href.lower() and '/avocat/' in href:
                                lawyer_links.append(href)
                        break
                except Exception as e:
                    continue
            
            # Si pas de liens spécifiques, chercher tous les liens de la page
            if not lawyer_links:
                print("🔍 Recherche de tous les liens de la page...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and '/avocat/' in href and href.count('/') > 3:
                        lawyer_links.append(href)
            
            # Nettoyer et dédupliquer
            lawyer_links = list(set([link for link in lawyer_links if link]))
            
            print(f"📊 Total de {len(lawyer_links)} liens d'avocats trouvés")
            
            return lawyer_links
            
        except Exception as e:
            print(f"❌ Erreur récupération liens: {e}")
            return []
    
    def extract_lawyer_info(self, url):
        """Extraction des informations d'un avocat"""
        print(f"👤 Extraction des infos de: {url}")
        
        lawyer_info = {
            'url': url,
            'nom': '',
            'prenom': '',
            'email': '',
            'annee_inscription': '',
            'date_serment': '',
            'specialisations': [],
            'structure': '',
            'adresse': '',
            'telephone': '',
            'telecopie': '',
            'mobile': ''
        }
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Obtenir tout le texte de la page
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source
            
            # Extraction du nom/prénom depuis le titre
            try:
                title_element = self.driver.find_element(By.TAG_NAME, "h1")
                if not title_element:
                    title_element = self.driver.find_element(By.TAG_NAME, "title")
                
                full_name = title_element.text.strip()
                if not full_name and title_element.tag_name == "title":
                    full_name = title_element.get_attribute("textContent").strip()
                    
                # Nettoyer le titre
                full_name = re.sub(r' - Ordre des Avocats.*', '', full_name)
                
                print(f"   Nom depuis titre: {full_name}")
                
                # Séparer nom/prénom
                if full_name:
                    name_parts = full_name.split()
                    if len(name_parts) >= 2:
                        lawyer_info['nom'] = name_parts[0]
                        lawyer_info['prenom'] = ' '.join(name_parts[1:])
                    else:
                        lawyer_info['nom'] = full_name
                        
            except Exception as e:
                print(f"   Erreur extraction nom: {e}")
            
            # Extraction des métadonnées (très efficace pour ce site)
            try:
                meta_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                if meta_description:
                    desc_content = meta_description.get_attribute("content")
                    print(f"   Meta description: {desc_content}")
                    
                    # Extraire structure
                    if 'SELARL' in desc_content or 'SARL' in desc_content or 'SCP' in desc_content:
                        structure_match = re.search(r'(SELARL|SARL|SCP)[^0-9]*', desc_content)
                        if structure_match:
                            structure_end = desc_content.find('23', structure_match.end())
                            if structure_end > 0:
                                lawyer_info['structure'] = desc_content[structure_match.start():structure_end].strip()
                            else:
                                lawyer_info['structure'] = structure_match.group(0).strip()
                    
                    # Extraire téléphone
                    phone_match = re.search(r'Téléphone[^:]*:\s*([\d\s\.]+)', desc_content)
                    if phone_match:
                        lawyer_info['telephone'] = phone_match.group(1).strip()
                    
                    # Extraire télécopie  
                    fax_match = re.search(r'Télécopie[^:]*:\s*([\d\s\.]+)', desc_content)
                    if fax_match:
                        lawyer_info['telecopie'] = fax_match.group(1).strip()
                        
            except Exception as e:
                print(f"   Erreur meta: {e}")
            
            # Extraction depuis le contenu de la page
            try:
                content_blocks = self.driver.find_elements(By.CSS_SELECTOR, '.content-block p')
                for block in content_blocks:
                    text = block.text.strip()
                    
                    # Structure/Cabinet
                    if 'SELARL' in text or 'SARL' in text or 'SCP' in text:
                        lawyer_info['structure'] = text
                        print(f"   Structure trouvée: {text}")
                    
                    # Téléphone
                    if 'Téléphone' in text and 'mobile' not in text.lower():
                        phone_match = re.search(r'([\d\s\.]+)$', text)
                        if phone_match:
                            lawyer_info['telephone'] = phone_match.group(1).strip()
                            print(f"   Téléphone: {lawyer_info['telephone']}")
                    
                    # Mobile
                    if 'mobile' in text.lower():
                        mobile_match = re.search(r'([\d\s\.]+)$', text)
                        if mobile_match:
                            lawyer_info['mobile'] = mobile_match.group(1).strip()
                            print(f"   Mobile: {lawyer_info['mobile']}")
                    
                    # Télécopie
                    if 'Télécopie' in text:
                        fax_match = re.search(r'([\d\s\.]+)$', text)
                        if fax_match:
                            lawyer_info['telecopie'] = fax_match.group(1).strip()
                            print(f"   Télécopie: {lawyer_info['telecopie']}")
                    
                    # Email
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                    if email_match:
                        lawyer_info['email'] = email_match.group(1)
                        print(f"   Email: {lawyer_info['email']}")
                    
                    # Date de serment
                    if 'serment' in text.lower() or 'prestation' in text.lower():
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
                        if date_match:
                            lawyer_info['date_serment'] = date_match.group(1)
                            # Extraire l'année
                            year_match = re.search(r'(\d{4})', lawyer_info['date_serment'])
                            if year_match:
                                lawyer_info['annee_inscription'] = year_match.group(1)
                            print(f"   Date serment: {lawyer_info['date_serment']}")
                    
                    # Adresse (recherche des éléments d'adresse)
                    if re.search(r'\d+.*rue|avenue|boulevard|place', text, re.IGNORECASE):
                        if not lawyer_info['adresse']:
                            lawyer_info['adresse'] = text
                            print(f"   Adresse: {text}")
                        elif text not in lawyer_info['adresse']:
                            lawyer_info['adresse'] += f", {text}"
                            
            except Exception as e:
                print(f"   Erreur contenu: {e}")
            
            # Recherche spécialisations dans tout le texte
            try:
                specialization_keywords = [
                    'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
                    'droit de la famille', 'droit immobilier', 'droit des sociétés',
                    'droit public', 'droit fiscal', 'spécialisation', 'spécialité',
                    'domaine de compétence', 'pratique'
                ]
                
                for keyword in specialization_keywords:
                    if keyword.lower() in page_text.lower():
                        # Chercher le contexte autour du mot-clé
                        pattern = f".{{0,50}}{re.escape(keyword)}.{{0,50}}"
                        matches = re.findall(pattern, page_text, re.IGNORECASE)
                        for match in matches[:3]:  # Limiter à 3 matches
                            clean_match = re.sub(r'\s+', ' ', match).strip()
                            if clean_match not in lawyer_info['specialisations']:
                                lawyer_info['specialisations'].append(clean_match)
                                print(f"   Spécialisation: {clean_match}")
                                
            except Exception as e:
                print(f"   Erreur spécialisations: {e}")
            
            print(f"✅ Extraction terminée pour {lawyer_info.get('prenom', '')} {lawyer_info.get('nom', 'Inconnu')}")
            
        except Exception as e:
            print(f"❌ Erreur extraction {url}: {e}")
        
        return lawyer_info
    
    def run_improved_test(self):
        """Exécution du test amélioré"""
        print("🚀 Démarrage du test amélioré scraper Castres")
        print("=" * 60)
        
        try:
            # Configuration
            self.setup_driver()
            print("✅ Driver configuré")
            
            # Accès à la page
            print("🌐 Accès à la page d'annuaire...")
            self.driver.get("https://avocats-castres.fr/annuaire-avocats/")
            time.sleep(5)
            
            # Gestion cookies
            self.accept_cookies()
            
            # Récupération des liens
            lawyer_links = self.get_lawyer_links()
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                return
            
            # Pour le test, prendre seulement les 5 premiers
            test_links = lawyer_links[:5]
            print(f"📋 Test sur {len(test_links)} avocats")
            
            # Test extraction
            for i, link in enumerate(test_links, 1):
                print(f"\n--- Test {i}/{len(test_links)} ---")
                lawyer_info = self.extract_lawyer_info(link)
                self.lawyers.append(lawyer_info)
                time.sleep(2)  # Pause entre les requêtes
            
            # Sauvegarde résultats
            self.save_results()
            
            print("\n" + "=" * 60)
            print("✅ Test amélioré terminé avec succès!")
            print(f"📊 {len(self.lawyers)} avocats traités")
            
            # Affichage résumé
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Erreur durant le test: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fermé")
    
    def print_summary(self):
        """Affichage d'un résumé des résultats"""
        print("\n📈 RÉSUMÉ DES EXTRACTIONS:")
        print("-" * 40)
        
        for i, lawyer in enumerate(self.lawyers, 1):
            print(f"{i}. {lawyer.get('prenom', '')} {lawyer.get('nom', 'N/A')}")
            print(f"   Email: {lawyer.get('email', 'Non trouvé')}")
            print(f"   Tél: {lawyer.get('telephone', 'N/A')}")
            print(f"   Structure: {lawyer.get('structure', 'N/A')}")
            print(f"   Année: {lawyer.get('annee_inscription', 'N/A')}")
            if lawyer.get('specialisations'):
                print(f"   Spécialisations: {len(lawyer['specialisations'])} trouvée(s)")
            print()
    
    def save_results(self):
        """Sauvegarde des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f'castres_improved_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_file = f'castres_improved_{timestamp}.csv'
        if self.lawyers:
            fieldnames = self.lawyers[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in self.lawyers:
                    # Convertir les listes en string pour CSV
                    row = lawyer.copy()
                    row['specialisations'] = '; '.join(row['specialisations']) if row['specialisations'] else ''
                    writer.writerow(row)
        
        print(f"💾 Résultats sauvegardés: {json_file} et {csv_file}")

if __name__ == "__main__":
    # Test amélioré en mode visuel d'abord
    scraper = CastresScraperImproved(headless=False)
    scraper.run_improved_test()