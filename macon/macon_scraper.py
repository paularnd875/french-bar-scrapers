#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL pour le Barreau de Macon - AVEC SPÉCIALISATIONS
Version corrigée pour récupérer les compétences/spécialisations
"""

import time
import csv
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

class MaconBarScraperFinal:
    def __init__(self, test_mode=False, max_lawyers=None):
        self.base_url = "https://avocatsmacon.fr/avocat/"
        self.test_mode = test_mode
        self.max_lawyers = max_lawyers
        self.lawyers_data = []
        self.errors_log = []
        
    def setup_driver(self):
        """Configure le driver Chrome"""
        chrome_options = Options()
        
        if not self.test_mode:  # Mode headless seulement en production
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Options anti-détection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Masquer les signes d'automatisation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def accept_cookies(self, driver):
        """Accepte les cookies"""
        try:
            print("🍪 Acceptation des cookies...")
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='accept']"))
            )
            cookie_button.click()
            print("✅ Cookies acceptés")
            time.sleep(2)
            return True
        except TimeoutException:
            print("ℹ️ Pas de banner de cookies ou déjà accepté")
            return True

    def extract_basic_info(self, lawyer_item):
        """Extrait les informations de base d'un avocat depuis l'item de la liste"""
        lawyer_data = {
            'prenom': '',
            'nom': '',
            'nom_complet': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'annee_inscription': '',
            'specialisations': '',
            'structure': '',
            'distinctions': '',
            'source_url': self.base_url
        }
        
        try:
            # Prénom et nom séparés
            try:
                lastname_elem = lawyer_item.find_element(By.CSS_SELECTOR, ".lastname")
                firstname_elem = lawyer_item.find_element(By.CSS_SELECTOR, ".firstname")
                
                lawyer_data['nom'] = lastname_elem.text.strip()
                lawyer_data['prenom'] = firstname_elem.text.strip()
                lawyer_data['nom_complet'] = f"{lawyer_data['prenom']} {lawyer_data['nom']}"
            except:
                return None  # Si on ne peut pas récupérer le nom, on skip
            
            # Cabinet/Structure
            try:
                cabinet_elem = lawyer_item.find_element(By.CSS_SELECTOR, ".item__cabinet")
                lawyer_data['structure'] = cabinet_elem.text.strip()
            except:
                pass
            
            # Année de serment
            try:
                serment_elem = lawyer_item.find_element(By.CSS_SELECTOR, ".item__serment")
                serment_text = serment_elem.text.strip()
                # Extraire l'année avec regex
                year_match = re.search(r'\b(19|20)\d{2}\b', serment_text)
                if year_match:
                    lawyer_data['annee_inscription'] = year_match.group()
            except:
                pass
                
        except Exception as e:
            self.errors_log.append(f"Erreur extraction infos de base: {e}")
            return None
        
        return lawyer_data

    def extract_modal_details(self, driver, modal_id, lawyer_data):
        """Extrait les détails depuis la modal - VERSION CORRIGÉE POUR LES SPÉCIALISATIONS"""
        try:
            # Attendre que la modal soit visible
            modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, modal_id))
            )
            
            # Attendre un peu que le contenu se charge
            time.sleep(1)
            
            # Email
            try:
                email_link = modal.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                email = email_link.get_attribute('href').replace('mailto:', '')
                lawyer_data['email'] = email.strip()
            except:
                pass
            
            # Téléphone
            try:
                phone_link = modal.find_element(By.CSS_SELECTOR, "a.phone, a[href^='tel:']")
                if phone_link.get_attribute('href'):
                    phone = phone_link.get_attribute('href').replace('tel:', '')
                else:
                    phone = phone_link.text
                lawyer_data['telephone'] = phone.strip()
            except:
                pass
            
            # Adresse
            try:
                address_parts = []
                street_elem = modal.find_element(By.CSS_SELECTOR, ".street")
                if street_elem:
                    address_parts.append(street_elem.text.strip())
                
                city_elem = modal.find_element(By.CSS_SELECTOR, ".city")
                if city_elem:
                    address_parts.append(city_elem.text.strip())
                
                if address_parts:
                    lawyer_data['adresse'] = ", ".join(address_parts)
            except:
                pass
            
            # SPÉCIALISATIONS - CORRECTION MAJEURE ICI
            try:
                # Chercher la section des compétences
                skills_section = modal.find_element(By.CSS_SELECTOR, ".modal__infos__skills")
                if skills_section:
                    # Récupérer toutes les compétences dans la liste
                    skill_items = skills_section.find_elements(By.CSS_SELECTOR, "ul li")
                    specializations = []
                    
                    for skill_item in skill_items:
                        skill_text = skill_item.text.strip()
                        if skill_text and skill_text not in specializations:
                            specializations.append(skill_text)
                    
                    if specializations:
                        lawyer_data['specialisations'] = "; ".join(specializations)
                        if not self.test_mode:
                            print(f"    🎯 Spécialisations trouvées: {lawyer_data['specialisations']}")
            except:
                # Si pas de section spécialisée, chercher dans d'autres endroits
                try:
                    modal_text = modal.text
                    # Patterns pour identifier les spécialisations dans le texte libre
                    spec_patterns = [
                        r'Spécialité(?:s)?\s*:([^\n]+)',
                        r'Domaine(?:s)?\s*:([^\n]+)',
                        r'Compétence(?:s)?\s*:([^\n]+)',
                        r'Expertise(?:s)?\s*:([^\n]+)'
                    ]
                    
                    specializations = []
                    for pattern in spec_patterns:
                        matches = re.findall(pattern, modal_text, re.IGNORECASE)
                        for match in matches:
                            spec = match.strip()
                            if spec and spec not in specializations:
                                specializations.append(spec)
                    
                    if specializations:
                        lawyer_data['specialisations'] = "; ".join(specializations)
                except:
                    pass
                
        except Exception as e:
            self.errors_log.append(f"Erreur extraction modal {modal_id}: {e}")

    def close_modal(self, driver):
        """Ferme la modal ouverte"""
        try:
            close_button = driver.find_element(By.CSS_SELECTOR, ".modal__close, .close-modal, [data-dismiss='modal']")
            close_button.click()
            time.sleep(0.5)
            return True
        except:
            # Essayer d'appuyer sur Escape
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                return True
            except:
                return False

    def save_progress(self, batch_number):
        """Sauvegarde les résultats intermédiaires"""
        if not self.lawyers_data:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde partielle
        prefix = "macon_test" if self.test_mode else "macon_final"
        csv_filename = f"{prefix}_partial_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 
                         'annee_inscription', 'specialisations', 'structure', 'distinctions', 'source_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        print(f"📄 Sauvegarde partielle: {csv_filename}")

    def scrape_lawyers(self):
        """Fonction principale de scraping"""
        driver = self.setup_driver()
        
        try:
            mode_text = "TEST" if self.test_mode else "PRODUCTION FINALE"
            print(f"🔍 SCRAPING {mode_text} - AVEC SPÉCIALISATIONS")
            print(f"🔍 Accès au site: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(3)
            
            # Accepter les cookies
            self.accept_cookies(driver)
            
            # Attendre que la page se charge
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("🔍 Recherche des fiches d'avocats...")
            
            # Recherche des items d'avocats
            lawyer_items = driver.find_elements(By.CSS_SELECTOR, ".am__result__list__item")
            
            if not lawyer_items:
                print("❌ Aucune fiche d'avocat trouvée")
                return
            
            total_lawyers = len(lawyer_items)
            
            # Limiter si en mode test
            if self.test_mode and self.max_lawyers:
                lawyer_items = lawyer_items[:self.max_lawyers]
                total_lawyers = len(lawyer_items)
                print(f"✅ {total_lawyers} avocats sélectionnés pour le test")
            else:
                print(f"✅ {total_lawyers} avocats trouvés - TRAITEMENT EN COURS...")
            
            # Traitement de chaque avocat
            for i, lawyer_item in enumerate(lawyer_items, 1):
                if self.test_mode:
                    print(f"\n👨‍⚖️ Traitement avocat {i}/{total_lawyers}")
                else:
                    print(f"👨‍⚖️ Traitement avocat {i}/{total_lawyers}", end="")
                
                try:
                    # Scroll vers l'élément
                    driver.execute_script("arguments[0].scrollIntoView(true);", lawyer_item)
                    time.sleep(0.5)
                    
                    # Extraction des informations de base
                    lawyer_data = self.extract_basic_info(lawyer_item)
                    if not lawyer_data:
                        print(" - ⚠️ Skip (données manquantes)")
                        continue
                    
                    if self.test_mode:
                        print(f"  ✅ Informations de base: {lawyer_data.get('nom_complet', 'Nom inconnu')}")
                    else:
                        print(f" - {lawyer_data.get('nom_complet', 'Nom inconnu')}", end="")
                    
                    # Cliquer sur le bouton "Voir +" pour ouvrir la modal
                    try:
                        voir_plus_btn = lawyer_item.find_element(By.CSS_SELECTOR, ".item__cta")
                        modal_target = voir_plus_btn.get_attribute('data-modal-target')
                        
                        # Clic sur le bouton
                        voir_plus_btn.click()
                        time.sleep(1)  # Attendre que la modal s'ouvre
                        
                        # Extraire les détails de la modal
                        self.extract_modal_details(driver, modal_target, lawyer_data)
                        
                        # Fermer la modal
                        self.close_modal(driver)
                        
                    except Exception as e:
                        self.errors_log.append(f"Erreur modal avocat {i}: {e}")
                    
                    # Validation et ajout des données
                    if lawyer_data['nom'] and lawyer_data['prenom']:
                        self.lawyers_data.append(lawyer_data)
                        if self.test_mode:
                            print(f"  ✅ Avocat ajouté: {lawyer_data['nom_complet']} - {lawyer_data.get('email', 'Pas de e-mail')}")
                            if lawyer_data['specialisations']:
                                print(f"  🎯 Spécialisations: {lawyer_data['specialisations']}")
                        else:
                            print(f" - ✅ OK ({lawyer_data.get('email', 'pas email')})")
                    else:
                        print(" - ⚠️ Skip (validation échouée)")
                
                except Exception as e:
                    self.errors_log.append(f"Erreur générale avocat {i}: {e}")
                    if self.test_mode:
                        print(f"  ❌ Erreur: {e}")
                    else:
                        print(f" - ❌ Erreur: {e}")
                    continue
                
                # Sauvegarde intermédiaire (seulement en mode production)
                if not self.test_mode and i % 25 == 0:
                    self.save_progress(i // 25)
                
                # Pause courte pour ne pas surcharger le serveur
                time.sleep(0.3)
            
            print(f"\n📊 RÉSUMÉ FINAL:")
            print(f"   - Total traité: {len(self.lawyers_data)}/{total_lawyers} avocats")
            print(f"   - Erreurs: {len(self.errors_log)}")
            
            # Compter les spécialisations récupérées
            with_specializations = len([l for l in self.lawyers_data if l['specialisations']])
            print(f"   - Avec spécialisations: {with_specializations}/{len(self.lawyers_data)}")
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            self.errors_log.append(f"Erreur générale: {e}")
        
        finally:
            driver.quit()

    def save_results(self):
        """Sauvegarde les résultats finaux"""
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "MACON_TEST" if self.test_mode else "MACON_FINAL_AVEC_SPECIALITES"
        
        # Sauvegarde CSV
        csv_filename = f"{prefix}_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 
                         'annee_inscription', 'specialisations', 'structure', 'distinctions', 'source_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        # Sauvegarde JSON
        json_filename = f"{prefix}_{len(self.lawyers_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, indent=2, ensure_ascii=False)
        
        # Sauvegarde des emails uniquement
        emails_filename = f"{prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
        emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in emails:
                emailfile.write(f"{email}\n")
        
        # Rapport détaillé
        rapport_filename = f"{prefix}_RAPPORT_COMPLET_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as rapportfile:
            rapportfile.write(f"RAPPORT DE SCRAPING FINAL - BARREAU DE MACON (AVEC SPÉCIALISATIONS)\n")
            rapportfile.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            rapportfile.write(f"URL: {self.base_url}\n")
            rapportfile.write(f"Mode: {'TEST' if self.test_mode else 'PRODUCTION FINALE'}\n")
            rapportfile.write(f"Nombre d'avocats traités: {len(self.lawyers_data)}\n")
            rapportfile.write(f"Emails récupérés: {len(emails)}\n")
            rapportfile.write(f"Erreurs rencontrées: {len(self.errors_log)}\n")
            
            # Stats spécialisations
            with_specializations = len([l for l in self.lawyers_data if l['specialisations']])
            rapportfile.write(f"Avec spécialisations: {with_specializations}\n\n")
            
            if self.errors_log:
                rapportfile.write("ERREURS RENCONTRÉES:\n")
                rapportfile.write("-" * 30 + "\n")
                for error in self.errors_log:
                    rapportfile.write(f"- {error}\n")
                rapportfile.write("\n")
            
            rapportfile.write("DÉTAIL DES AVOCATS:\n")
            rapportfile.write("-" * 50 + "\n")
            for i, lawyer in enumerate(self.lawyers_data, 1):
                rapportfile.write(f"\n{i}. {lawyer.get('nom_complet', 'N/A')}\n")
                rapportfile.write(f"   Prénom: {lawyer.get('prenom', 'N/A')}\n")
                rapportfile.write(f"   Nom: {lawyer.get('nom', 'N/A')}\n")
                rapportfile.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                rapportfile.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\n")
                rapportfile.write(f"   Adresse: {lawyer.get('adresse', 'N/A')}\n")
                rapportfile.write(f"   Structure: {lawyer.get('structure', 'N/A')}\n")
                rapportfile.write(f"   Année inscription: {lawyer.get('annee_inscription', 'N/A')}\n")
                rapportfile.write(f"   Spécialisations: {lawyer.get('specialisations', 'N/A')}\n")
        
        print(f"\n✅ FICHIERS FINAUX SAUVEGARDÉS:")
        print(f"   📊 CSV: {csv_filename}")
        print(f"   🗂️  JSON: {json_filename}")
        print(f"   📧 Emails: {emails_filename}")
        print(f"   📋 Rapport: {rapport_filename}")

def main():
    print("🔧 CHOISISSEZ LE MODE D'EXÉCUTION:")
    print("1. TEST (5 avocats avec fenêtre visible)")
    print("2. PRODUCTION (75 avocats en mode headless)")
    
    choice = input("\nVotre choix (1 ou 2): ").strip()
    
    if choice == "1":
        print("\n🧪 MODE TEST - 5 avocats avec spécialisations")
        print("=" * 50)
        scraper = MaconBarScraperFinal(test_mode=True, max_lawyers=5)
    else:
        print("\n🚀 MODE PRODUCTION - 75 avocats avec spécialisations")
        print("=" * 60)
        print("⚠️  MODE HEADLESS: Aucune fenêtre ne s'ouvrira")
        print("=" * 60)
        scraper = MaconBarScraperFinal(test_mode=False)
    
    scraper.scrape_lawyers()
    scraper.save_results()
    
    print("\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS !")

if __name__ == "__main__":
    main()