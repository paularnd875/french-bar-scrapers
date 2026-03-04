#!/usr/bin/env python3
"""
Script de test pour scraper l'annuaire des avocats d'Arras
Test initial avec acceptation des cookies et extraction d'un avocat
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

class ArrasLawyerScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.base_url = "https://avocatsarras.com/annuaire/"
        self.lawyers_data = []
        
    def setup_driver(self):
        """Configure le driver Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if self.headless:
            chrome_options.add_argument("--headless")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def accept_cookies(self):
        """Accepte les cookies sur le site"""
        try:
            print("🍪 Recherche du banner de cookies...")
            # Attendre que la page se charge
            time.sleep(3)
            
            # Chercher différents sélecteurs possibles pour les cookies
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']", 
                "button[class*='cookie']",
                "#tarteaucitronPersonalize",
                "#tarteaucitronAllAllowed",
                "button[onclick*='tarteaucitron']",
                "[id*='cookie'] button",
                "[class*='consent'] button",
                "button:contains('Accepter')",
                "button:contains('Accept')",
                "button:contains('J'accepte')"
            ]
            
            for selector in cookie_selectors:
                try:
                    if ":contains(" in selector:
                        # Utiliser XPath pour les sélecteurs contains
                        text_to_find = selector.split("'")[1]
                        xpath = f"//button[contains(text(), '{text_to_find}')]"
                        cookie_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                    else:
                        cookie_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    print(f"✅ Bouton cookies trouvé avec sélecteur: {selector}")
                    cookie_button.click()
                    time.sleep(2)
                    print("✅ Cookies acceptés avec succès")
                    return True
                    
                except TimeoutException:
                    continue
                except Exception as e:
                    continue
            
            print("⚠️ Aucun bouton de cookies trouvé, continuons...")
            return False
            
        except Exception as e:
            print(f"❌ Erreur lors de l'acceptation des cookies: {e}")
            return False
    
    def get_lawyer_links(self, max_test=3):
        """Récupère les liens vers les profils d'avocats (limité pour les tests)"""
        try:
            print("🔍 Recherche des liens d'avocats...")
            
            # Attendre que les éléments se chargent
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Sélecteurs possibles pour les liens d'avocats
            link_selectors = [
                "a[href*='/annuaire/avocats/']",
                ".lawyer-card a",
                ".avocat a",
                ".profile-link",
                "a[href*='avocat']",
                ".directory-item a"
            ]
            
            lawyer_links = []
            
            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if links:
                        print(f"✅ Trouvé {len(links)} liens avec sélecteur: {selector}")
                        for link in links[:max_test]:
                            href = link.get_attribute("href")
                            if href and "/annuaire/avocats/" in href:
                                lawyer_links.append(href)
                        break
                except Exception as e:
                    continue
            
            # Si aucun lien trouvé avec les sélecteurs CSS, essayons XPath
            if not lawyer_links:
                try:
                    links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/annuaire/avocats/')]")
                    print(f"✅ Trouvé {len(links)} liens avec XPath")
                    for link in links[:max_test]:
                        href = link.get_attribute("href")
                        if href:
                            lawyer_links.append(href)
                except Exception as e:
                    print(f"❌ Erreur XPath: {e}")
            
            # Dédupliquer les liens
            lawyer_links = list(set(lawyer_links))
            print(f"📋 Total de {len(lawyer_links)} liens uniques d'avocats trouvés")
            
            return lawyer_links[:max_test]
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des liens: {e}")
            return []
    
    def extract_lawyer_info(self, lawyer_url):
        """Extrait les informations d'un avocat depuis son profil"""
        try:
            print(f"🔍 Extraction des données de: {lawyer_url}")
            self.driver.get(lawyer_url)
            time.sleep(3)
            
            lawyer_data = {
                "url": lawyer_url,
                "prenom": "",
                "nom": "",
                "email": "",
                "annee_inscription": "",
                "specialisations": [],
                "structure": "",
                "adresse": "",
                "telephone": "",
                "fax": ""
            }
            
            # Extraction du nom complet
            name_selectors = [
                "h1",
                ".lawyer-name",
                ".avocat-nom",
                ".profile-name",
                "[class*='name']",
                "[class*='title']"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    full_name = name_element.text.strip()
                    if full_name and len(full_name) > 3:
                        # Tenter de séparer prénom et nom
                        name_parts = full_name.split()
                        if len(name_parts) >= 2:
                            lawyer_data["prenom"] = " ".join(name_parts[:-1])
                            lawyer_data["nom"] = name_parts[-1]
                        else:
                            lawyer_data["nom"] = full_name
                        print(f"✅ Nom trouvé: {full_name}")
                        break
                except:
                    continue
            
            # Extraction de l'email
            email_selectors = [
                "a[href*='mailto:']",
                "[class*='email']",
                "[class*='mail']"
            ]
            
            for selector in email_selectors:
                try:
                    email_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email = email_element.get_attribute("href")
                    if email and "mailto:" in email:
                        lawyer_data["email"] = email.replace("mailto:", "")
                        print(f"✅ Email trouvé: {lawyer_data['email']}")
                        break
                    elif email_element.text and "@" in email_element.text:
                        lawyer_data["email"] = email_element.text.strip()
                        print(f"✅ Email trouvé: {lawyer_data['email']}")
                        break
                except:
                    continue
            
            # Recherche de l'année d'inscription
            try:
                page_text = self.driver.page_source
                import re
                year_patterns = [
                    r"inscription[^0-9]*([1-2][0-9]{3})",
                    r"barreau[^0-9]*([1-2][0-9]{3})",
                    r"inscrit[^0-9]*([1-2][0-9]{3})",
                    r"([1-2][0-9]{3})[^0-9]*inscription"
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        year = matches[0]
                        if 1950 <= int(year) <= 2024:
                            lawyer_data["annee_inscription"] = year
                            print(f"✅ Année d'inscription trouvée: {year}")
                            break
            except:
                pass
            
            # Extraction des spécialisations
            specialization_selectors = [
                "[class*='specialisation']",
                "[class*='specialite']",
                "[class*='domaine']",
                ".expertise",
                ".competences"
            ]
            
            for selector in specialization_selectors:
                try:
                    spec_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in spec_elements:
                        text = elem.text.strip()
                        if text and len(text) > 2:
                            lawyer_data["specialisations"].append(text)
                    if lawyer_data["specialisations"]:
                        print(f"✅ Spécialisations trouvées: {lawyer_data['specialisations']}")
                        break
                except:
                    continue
            
            # Extraction de la structure/cabinet
            structure_selectors = [
                "[class*='cabinet']",
                "[class*='structure']",
                "[class*='societe']",
                "[class*='entreprise']"
            ]
            
            for selector in structure_selectors:
                try:
                    structure_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    structure = structure_element.text.strip()
                    if structure and len(structure) > 2:
                        lawyer_data["structure"] = structure
                        print(f"✅ Structure trouvée: {structure}")
                        break
                except:
                    continue
            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction de {lawyer_url}: {e}")
            return None
    
    def run_test(self):
        """Lance le test du scraper"""
        try:
            print("🚀 Démarrage du scraper de test pour Arras")
            self.setup_driver()
            
            # Naviguer vers la page d'accueil
            print(f"📂 Navigation vers: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Récupérer quelques liens d'avocats pour le test
            lawyer_links = self.get_lawyer_links(max_test=3)
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                return False
            
            # Extraire les données des avocats de test
            for i, link in enumerate(lawyer_links, 1):
                print(f"\n📄 Traitement de l'avocat {i}/{len(lawyer_links)}")
                lawyer_data = self.extract_lawyer_info(link)
                
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                    print(f"✅ Données extraites pour {lawyer_data.get('nom', 'Inconnu')}")
                else:
                    print("❌ Échec de l'extraction")
            
            # Sauvegarder les résultats de test
            self.save_test_results()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur durant le test: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_test_results(self):
        """Sauvegarde les résultats du test"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_file = f"arras_test_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde CSV
        csv_file = f"arras_test_results_{timestamp}.csv"
        if self.lawyers_data:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.lawyers_data[0].keys())
                writer.writeheader()
                for lawyer in self.lawyers_data:
                    # Convertir la liste des spécialisations en chaîne
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = "; ".join(lawyer['specialisations'])
                    writer.writerow(lawyer_copy)
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")
        print(f"   📈 Total avocats traités: {len(self.lawyers_data)}")

def main():
    """Fonction principale"""
    scraper = ArrasLawyerScraper(headless=False)  # Mode visuel pour le test
    success = scraper.run_test()
    
    if success:
        print("\n🎉 Test terminé avec succès!")
        print("Vérifiez les fichiers de résultats pour valider les données extraites.")
    else:
        print("\n❌ Le test a échoué.")

if __name__ == "__main__":
    main()