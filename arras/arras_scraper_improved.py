#!/usr/bin/env python3
"""
Script amélioré pour scraper l'annuaire des avocats d'Arras
Version avec debugging et timeout améliorés
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ArrasLawyerScraperImproved:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://avocatsarras.com/annuaire/"
        self.lawyers_data = []
        
    def setup_driver(self):
        """Configure le driver Chrome avec timeout réduit"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--page-load-strategy=eager")  # Ne pas attendre que tout soit chargé
        
        if self.headless:
            chrome_options.add_argument("--headless")
            
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)  # Timeout réduit
        self.driver.set_page_load_timeout(30)  # Timeout page load
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def accept_cookies(self):
        """Accepte les cookies avec timeout réduit"""
        try:
            print("🍪 Recherche du banner de cookies...")
            
            # Attendre un peu que la page se charge
            time.sleep(2)
            
            # Sélecteurs simples et efficaces
            cookie_selectors = [
                "#tarteaucitronAllAllowed",
                "#tarteaucitronPersonalize2",
                "button[onclick*='tarteaucitronAllAllowed']",
                "button:contains('Accepter tous')",
                "button:contains('Tout accepter')",
                "button:contains('Accepter')"
            ]
            
            for selector in cookie_selectors:
                try:
                    if "contains(" in selector:
                        # Utiliser XPath
                        text = selector.split("'")[1]
                        xpath = f"//button[contains(text(), '{text}')]"
                        cookie_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                    else:
                        cookie_button = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    cookie_button.click()
                    time.sleep(1)
                    print(f"✅ Cookies acceptés avec: {selector}")
                    return True
                    
                except TimeoutException:
                    continue
                except Exception as e:
                    continue
            
            print("⚠️ Pas de banner de cookies trouvé, on continue")
            return True  # On continue même sans cookies
            
        except Exception as e:
            print(f"⚠️ Erreur cookies (on continue): {e}")
            return True
    
    def get_page_source_info(self):
        """Analyse le code source pour comprendre la structure"""
        try:
            print("🔍 Analyse de la structure de la page...")
            
            # Sauvegarder le code source pour analyse
            with open("arras_page_source.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print("📄 Code source sauvegardé dans arras_page_source.html")
            
            # Rechercher des éléments possibles
            potential_elements = [
                "//a[contains(@href, 'avocat')]",
                "//div[contains(@class, 'lawyer')]",
                "//div[contains(@class, 'avocat')]",
                "//article",
                "//div[contains(@class, 'card')]"
            ]
            
            for xpath in potential_elements:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    if elements:
                        print(f"✅ Trouvé {len(elements)} éléments avec: {xpath}")
                        # Afficher quelques exemples
                        for i, elem in enumerate(elements[:3]):
                            try:
                                print(f"   Exemple {i+1}: {elem.text[:100]}...")
                            except:
                                pass
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"❌ Erreur analyse page: {e}")
    
    def get_lawyer_links(self):
        """Récupère les liens vers les profils avec approche simple"""
        try:
            print("🔍 Recherche des liens d'avocats...")
            
            # Attendre que la page soit chargée
            time.sleep(3)
            
            # Recherche simple de tous les liens
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            lawyer_links = []
            
            print(f"📋 Total de {len(all_links)} liens trouvés sur la page")
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and ("/avocat" in href.lower() or "/annuaire" in href.lower()):
                        if href not in lawyer_links and "avocatsarras.com" in href:
                            lawyer_links.append(href)
                            text = link.text.strip()[:50]
                            print(f"   🔗 Lien trouvé: {href} - {text}")
                            
                            if len(lawyer_links) >= 3:  # Limiter pour le test
                                break
                except Exception as e:
                    continue
            
            print(f"✅ {len(lawyer_links)} liens d'avocats sélectionnés pour le test")
            return lawyer_links
            
        except Exception as e:
            print(f"❌ Erreur récupération liens: {e}")
            return []
    
    def extract_lawyer_info_simple(self, lawyer_url):
        """Extraction simplifiée avec timeout"""
        try:
            print(f"\n🔍 Test extraction: {lawyer_url}")
            
            # Navigation avec timeout
            self.driver.set_page_load_timeout(20)
            self.driver.get(lawyer_url)
            time.sleep(2)
            
            # Structure de données simple
            lawyer_data = {
                "url": lawyer_url,
                "nom_complet": "",
                "email": "",
                "texte_complet": ""
            }
            
            # Récupérer le titre de la page
            try:
                title = self.driver.title
                lawyer_data["nom_complet"] = title
                print(f"📋 Titre page: {title}")
            except:
                pass
            
            # Rechercher des emails avec méthode simple
            try:
                page_source = self.driver.page_source.lower()
                import re
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_source)
                if emails:
                    lawyer_data["email"] = emails[0]
                    print(f"📧 Email trouvé: {emails[0]}")
            except:
                pass
            
            # Récupérer tout le texte visible
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                lawyer_data["texte_complet"] = body_text[:500]  # Limiter la taille
                print(f"📄 Texte récupéré: {len(body_text)} caractères")
            except:
                pass
            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur extraction {lawyer_url}: {e}")
            return None
    
    def run_test(self):
        """Test rapide et efficace"""
        try:
            print("🚀 Test du scraper Arras - version rapide")
            
            self.setup_driver()
            
            print(f"📂 Navigation vers: {self.base_url}")
            self.driver.get(self.base_url)
            
            self.accept_cookies()
            
            # Analyse de la page
            self.get_page_source_info()
            
            # Récupération des liens
            lawyer_links = self.get_lawyer_links()
            
            if not lawyer_links:
                print("⚠️ Aucun lien trouvé, testons avec une URL directe...")
                # Test avec une URL d'avocat direct si possible
                test_urls = [
                    "https://avocatsarras.com/annuaire/avocats/droit-penal/maitre-dumont-avocat-arras/",
                    "https://avocatsarras.com/annuaire/avocats/"
                ]
                
                for url in test_urls:
                    print(f"🔄 Test avec URL: {url}")
                    result = self.extract_lawyer_info_simple(url)
                    if result:
                        self.lawyers_data.append(result)
                        break
            else:
                # Traitement des liens trouvés
                for i, link in enumerate(lawyer_links, 1):
                    print(f"\n📄 Test {i}/{len(lawyer_links)}")
                    result = self.extract_lawyer_info_simple(link)
                    if result:
                        self.lawyers_data.append(result)
            
            self.save_results()
            return True
            
        except Exception as e:
            print(f"❌ Erreur test: {e}")
            return False
        finally:
            if self.driver:
                print("🔚 Fermeture du navigateur")
                self.driver.quit()
    
    def save_results(self):
        """Sauvegarde simple des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f"arras_test_simple_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   📄 {json_file}")
        print(f"   📈 {len(self.lawyers_data)} entrées")
        
        # Affichage résumé
        for i, data in enumerate(self.lawyers_data, 1):
            print(f"\n📋 Avocat {i}:")
            print(f"   URL: {data['url']}")
            print(f"   Nom: {data['nom_complet']}")
            print(f"   Email: {data['email'] or 'Non trouvé'}")

def main():
    scraper = ArrasLawyerScraperImproved(headless=False)
    success = scraper.run_test()
    
    if success:
        print("\n🎉 Test terminé!")
    else:
        print("\n❌ Échec du test")

if __name__ == "__main__":
    main()