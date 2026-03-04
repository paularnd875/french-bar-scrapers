#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver(headless=False):
    """Configuration du driver Chrome"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def accept_cookies(driver):
    """Accepte les cookies sur le site"""
    try:
        print("🍪 Recherche des boutons de cookies...")
        
        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).wait(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Attendre un peu pour que les scripts de cookies se chargent
        time.sleep(3)
        
        # Essayer différents sélecteurs pour les cookies
        cookie_selectors = [
            "button[data-axeptio-cookie='all']",  # Axeptio "Tout accepter"
            "button[id*='accept']",
            "button[class*='accept']",
            "button[class*='cookie']",
            ".axeptio-button--accept-all",
            "#axeptio-widget button",
            "[data-action='accept']"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                cookie_button.click()
                print(f"✅ Cookies acceptés avec le sélecteur: {selector}")
                time.sleep(2)
                return True
            except TimeoutException:
                continue
        
        print("⚠️ Aucun bouton de cookies trouvé - continuons sans")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors de l'acceptation des cookies: {e}")
        return False

def extract_lawyer_info(driver, lawyer_url):
    """Extrait les informations d'un avocat depuis sa page de profil"""
    try:
        print(f"📄 Extraction des données de: {lawyer_url}")
        driver.get(lawyer_url)
        
        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).wait(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        lawyer_data = {}
        
        # Nom et prénom
        try:
            name_element = driver.find_element(By.CSS_SELECTOR, "h1, .entry-title, .lawyer-name, .avocat-name")
            full_name = name_element.text.strip()
            lawyer_data['nom_complet'] = full_name
            
            # Essayer de séparer prénom et nom
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                lawyer_data['prenom'] = name_parts[0]
                lawyer_data['nom'] = ' '.join(name_parts[1:])
            else:
                lawyer_data['prenom'] = ""
                lawyer_data['nom'] = full_name
                
        except NoSuchElementException:
            lawyer_data['nom_complet'] = "Non trouvé"
            lawyer_data['prenom'] = ""
            lawyer_data['nom'] = ""
        
        # Email
        try:
            email_element = driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:'], .email")
            email = email_element.get_attribute('href').replace('mailto:', '') if email_element.get_attribute('href') else email_element.text
            lawyer_data['email'] = email.strip()
        except NoSuchElementException:
            lawyer_data['email'] = "Non trouvé"
        
        # Adresse
        try:
            address_element = driver.find_element(By.CSS_SELECTOR, ".address, .avocat-address, p:contains('49')")
            lawyer_data['adresse'] = address_element.text.strip()
        except NoSuchElementException:
            lawyer_data['adresse'] = "Non trouvé"
        
        # Année d'inscription au barreau
        try:
            # Rechercher différents patterns pour l'année
            inscription_element = driver.find_element(By.XPATH, "//text()[contains(., 'Inscription')] | //text()[contains(., 'inscription')] | //text()[contains(., 'Barreau')]")
            lawyer_data['annee_inscription'] = inscription_element.text.strip()
        except NoSuchElementException:
            lawyer_data['annee_inscription'] = "Non trouvé"
        
        # Spécialisations
        try:
            specializations = []
            spec_elements = driver.find_elements(By.CSS_SELECTOR, ".specialization, .domaine, .competence, ul li")
            for element in spec_elements:
                text = element.text.strip()
                if text and text not in specializations:
                    specializations.append(text)
            lawyer_data['specialisations'] = specializations if specializations else ["Non trouvé"]
        except:
            lawyer_data['specialisations'] = ["Non trouvé"]
        
        # Structure/Cabinet
        try:
            structure_element = driver.find_element(By.CSS_SELECTOR, ".cabinet, .structure, .firm")
            lawyer_data['structure'] = structure_element.text.strip()
        except NoSuchElementException:
            lawyer_data['structure'] = "Non trouvé"
        
        # URL de la page
        lawyer_data['url'] = lawyer_url
        lawyer_data['extraction_date'] = datetime.now().isoformat()
        
        return lawyer_data
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        return None

def test_scraper():
    """Test du scraper sur quelques avocats"""
    driver = None
    
    try:
        print("🚀 Démarrage du test du scraper Angers...")
        
        # Configuration du driver (mode visible pour le test)
        driver = setup_driver(headless=False)
        
        # Aller sur la page d'annuaire
        annuaire_url = "https://barreau-angers.org/annuaire-des-avocats/?recherche=&lieu=&domaine="
        print(f"📋 Accès à l'annuaire: {annuaire_url}")
        driver.get(annuaire_url)
        
        # Accepter les cookies
        accept_cookies(driver)
        
        # Attendre que la page soit complètement chargée
        time.sleep(5)
        
        # Récupérer les premiers liens d'avocats pour le test
        print("🔍 Recherche des liens d'avocats...")
        lawyer_links = []
        
        try:
            # Chercher les liens vers les fiches d'avocats
            link_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/avocat/']")
            
            for element in link_elements[:3]:  # Test sur 3 avocats seulement
                href = element.get_attribute('href')
                if href and href not in lawyer_links:
                    lawyer_links.append(href)
            
            print(f"✅ {len(lawyer_links)} liens d'avocats trouvés pour le test")
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des liens: {e}")
            return
        
        # Extraire les données de chaque avocat
        lawyers_data = []
        
        for i, lawyer_url in enumerate(lawyer_links):
            print(f"\n--- Test {i+1}/{len(lawyer_links)} ---")
            lawyer_data = extract_lawyer_info(driver, lawyer_url)
            
            if lawyer_data:
                lawyers_data.append(lawyer_data)
                print(f"✅ Données extraites pour: {lawyer_data.get('nom_complet', 'Nom inconnu')}")
                
                # Afficher les données extraites
                print(f"   📧 Email: {lawyer_data.get('email', 'N/A')}")
                print(f"   🏠 Adresse: {lawyer_data.get('adresse', 'N/A')}")
                print(f"   📅 Inscription: {lawyer_data.get('annee_inscription', 'N/A')}")
                print(f"   🏢 Structure: {lawyer_data.get('structure', 'N/A')}")
                print(f"   ⚖️ Spécialisations: {', '.join(lawyer_data.get('specialisations', []))}")
            else:
                print(f"❌ Échec de l'extraction pour: {lawyer_url}")
            
            time.sleep(2)  # Pause entre les requêtes
        
        # Sauvegarder les résultats du test
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"angers_test_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎯 Test terminé!")
        print(f"📊 {len(lawyers_data)} avocats traités avec succès")
        print(f"💾 Résultats sauvegardés dans: {filename}")
        
        return lawyers_data
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return []
        
    finally:
        if driver:
            input("\n⏸️ Appuyez sur Entrée pour fermer le navigateur...")
            driver.quit()

if __name__ == "__main__":
    test_scraper()