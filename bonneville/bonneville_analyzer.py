#!/usr/bin/env python3
"""
Analyseur pour le site du Barreau de Bonneville
Analyse la structure de la page et teste l'acceptation des cookies
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

class BonnevilleAnalyzer:
    def __init__(self, headless=False):
        self.base_url = "https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/"
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Configure le driver Chrome"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def analyze_page_structure(self):
        """Analyse la structure de la page principale"""
        print("=== ANALYSE DE LA STRUCTURE DE LA PAGE ===")
        
        try:
            print(f"Chargement de la page : {self.base_url}")
            self.driver.get(self.base_url)
            
            # Attendre que la page se charge
            time.sleep(3)
            
            # Chercher et gérer les cookies
            self.handle_cookies()
            
            # Analyser la structure après cookies
            print("\n--- Structure de la page ---")
            
            # Chercher les avocats sur la page
            lawyer_elements = self.find_lawyer_elements()
            
            if lawyer_elements:
                print(f"✅ Trouvé {len(lawyer_elements)} éléments d'avocats")
                # Analyser le premier avocat
                if len(lawyer_elements) > 0:
                    self.analyze_lawyer_element(lawyer_elements[0])
            else:
                print("❌ Aucun élément d'avocat trouvé")
                
            # Chercher la pagination
            self.analyze_pagination()
            
            # Sauvegarder le HTML pour analyse
            self.save_page_source()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse : {e}")
            
    def handle_cookies(self):
        """Gère l'acceptation des cookies"""
        print("\n--- Gestion des cookies ---")
        
        cookie_selectors = [
            "button[id*='cookie']",
            "button[class*='cookie']",
            "button[id*='accept']",
            "button[class*='accept']",
            ".cookie-consent button",
            "#cookie-consent button",
            "[data-cookie] button",
            "button:contains('Accepter')",
            "button:contains('J'accepte')",
            "button:contains('Accept')"
        ]
        
        for selector in cookie_selectors:
            try:
                if 'contains' in selector:
                    # Pour les sélecteurs avec :contains, utiliser XPath
                    text = selector.split(':contains(')[1].rstrip(')")').strip("'")
                    elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    print(f"✅ Trouvé bouton cookie avec sélecteur : {selector}")
                    elements[0].click()
                    print("✅ Cookie accepté")
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                continue
                
        print("ℹ️ Aucun bannière de cookies trouvée ou déjà acceptée")
        return False
        
    def find_lawyer_elements(self):
        """Trouve les éléments représentant les avocats"""
        print("\n--- Recherche des avocats ---")
        
        # Sélecteurs possibles pour les avocats
        lawyer_selectors = [
            ".avocat",
            ".lawyer",
            ".member",
            ".attorney",
            "[class*='avocat']",
            "[class*='lawyer']",
            "[class*='member']",
            ".et_pb_text",
            ".et_pb_module",
            "article",
            ".post",
            "[class*='card']",
            "[class*='profile']"
        ]
        
        for selector in lawyer_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 1:  # Au moins 2 pour confirmer qu'il s'agit d'une liste
                    print(f"✅ Trouvé {len(elements)} éléments avec sélecteur : {selector}")
                    return elements
            except:
                continue
                
        # Si pas d'éléments spécifiques, chercher des liens ou textes qui pourraient être des noms
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            name_links = [link for link in links if len(link.text.strip()) > 3 and 
                         ' ' in link.text.strip() and 
                         link.text.strip().replace(' ', '').replace('-', '').isalpha()]
            
            if name_links:
                print(f"✅ Trouvé {len(name_links)} liens potentiels de noms d'avocats")
                return name_links[:10]  # Limiter pour l'analyse
        except:
            pass
            
        return []
        
    def analyze_lawyer_element(self, element):
        """Analyse un élément d'avocat pour comprendre sa structure"""
        print(f"\n--- Analyse de l'élément avocat ---")
        
        try:
            # Texte de l'élément
            text = element.text.strip()
            print(f"Texte : {text[:100]}...")
            
            # HTML de l'élément
            html = element.get_attribute('outerHTML')
            print(f"HTML : {html[:200]}...")
            
            # Chercher des liens dans l'élément
            links = element.find_elements(By.TAG_NAME, "a")
            if links:
                print(f"✅ Trouvé {len(links)} lien(s) dans l'élément")
                for i, link in enumerate(links[:3]):
                    href = link.get_attribute('href')
                    link_text = link.text.strip()
                    print(f"  Lien {i+1}: {link_text} -> {href}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Erreur analyse élément : {e}")
            return False
            
    def analyze_pagination(self):
        """Analyse la pagination"""
        print(f"\n--- Analyse pagination ---")
        
        pagination_selectors = [
            ".pagination",
            ".page-numbers", 
            "[class*='pag']",
            ".next",
            ".prev",
            "[rel='next']",
            "[rel='prev']"
        ]
        
        for selector in pagination_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Trouvé pagination avec sélecteur : {selector}")
                    for elem in elements[:3]:
                        print(f"  Texte: {elem.text} | Href: {elem.get_attribute('href')}")
                    return True
            except:
                continue
                
        print("ℹ️ Pas de pagination détectée")
        return False
        
    def save_page_source(self):
        """Sauvegarde le code source pour analyse"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bonneville_page_source_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
                
            print(f"✅ Page source sauvegardée : {filename}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde : {e}")
            
    def test_lawyer_detail_access(self):
        """Teste l'accès aux détails d'un avocat"""
        print(f"\n=== TEST ACCÈS DÉTAILS AVOCAT ===")
        
        try:
            # Chercher un lien vers une fiche avocat
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in links:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                # Vérifier si c'est un lien vers une fiche avocat
                if (href and 'avocat' in href.lower() and len(text) > 3 and ' ' in text):
                    print(f"✅ Test avec l'avocat : {text}")
                    print(f"   Lien : {href}")
                    
                    # Cliquer sur le lien
                    link.click()
                    time.sleep(3)
                    
                    # Analyser la page de détail
                    self.analyze_lawyer_detail_page()
                    
                    # Revenir à la page précédente
                    self.driver.back()
                    time.sleep(2)
                    
                    return True
                    
            print("❌ Aucun lien vers fiche avocat trouvé")
            return False
            
        except Exception as e:
            print(f"❌ Erreur test accès détails : {e}")
            return False
            
    def analyze_lawyer_detail_page(self):
        """Analyse une page de détail d'avocat"""
        print(f"\n--- Analyse page détail ---")
        
        # Informations à chercher
        info_patterns = {
            'email': ['email', 'mail', '@'],
            'phone': ['tél', 'tel', 'phone', '+33', '04', '05', '01', '02', '03'],
            'specialization': ['spécial', 'domaine', 'compétence'],
            'year': ['inscr', 'année', 'depuis'],
            'structure': ['cabinet', 'société', 'sarl', 'scp']
        }
        
        page_text = self.driver.page_source.lower()
        found_info = {}
        
        for info_type, patterns in info_patterns.items():
            for pattern in patterns:
                if pattern in page_text:
                    found_info[info_type] = True
                    print(f"✅ {info_type} trouvé (pattern: {pattern})")
                    break
                    
        return found_info
        
    def run_analysis(self):
        """Lance l'analyse complète"""
        try:
            self.setup_driver()
            print("🚀 Démarrage de l'analyse du Barreau de Bonneville")
            
            # Analyse de la structure
            self.analyze_page_structure()
            
            # Test d'accès aux détails
            self.test_lawyer_detail_access()
            
            print("\n✅ Analyse terminée")
            
        except Exception as e:
            print(f"❌ Erreur générale : {e}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    # Lancement en mode visuel pour l'analyse
    analyzer = BonnevilleAnalyzer(headless=False)
    analyzer.run_analysis()