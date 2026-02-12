#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper PRODUCTION pour le Barreau de Laval
Extraction complète de tous les avocats en mode headless
"""

import time
import re
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    """Configuration du driver Chrome en mode headless"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def handle_cookies(driver):
    """Gestion simple de l'acceptation des cookies"""
    try:
        print("🍪 Recherche de la bannière de cookies...")
        
        # Attendre un peu et chercher les boutons courants
        time.sleep(2)
        
        # Essayer différents sélecteurs CSS simples
        simple_selectors = [
            "button[id*='axeptio']",
            "button[class*='axeptio']",
            "#axeptio_btn_accepter",
            ".axeptio-widget button",
            "[data-axeptio-widget] button"
        ]
        
        for selector in simple_selectors:
            try:
                cookies_button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Bouton cookies trouvé: {selector}")
                cookies_button.click()
                print("✅ Cookies acceptés avec succès")
                time.sleep(1)
                return True
            except TimeoutException:
                continue
        
        print("⚠️ Aucun bouton de cookies trouvé - continuons...")
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur lors de la gestion des cookies : {e}")
        return False

def separate_name(full_name):
    """Sépare le prénom et le nom de famille avec logique améliorée"""
    if not full_name or full_name.strip() == "":
        return "", ""
    
    # Nettoyer et normaliser
    full_name = full_name.strip()
    
    # Supprimer les titres courants
    titles_to_remove = ['Me ', 'Maître ', 'M. ', 'Mme ', 'Mr ', 'Mrs ', 'Dr ', 'Pr ']
    for title in titles_to_remove:
        if full_name.startswith(title):
            full_name = full_name[len(title):].strip()
    
    # Diviser en mots
    parts = full_name.split()
    
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return "", parts[0]  # Considérer comme nom de famille
    elif len(parts) == 2:
        return parts[0], parts[1]  # Prénom, Nom
    else:
        # Pour plus de 2 parties, analyser la structure
        first_part = parts[0]
        remaining_parts = parts[1:]
        
        # Vérifier les prénoms composés courants
        compound_first_names = ['Jean-', 'Marie-', 'Anne-', 'Pierre-', 'Paul-', 'Louis-', 'Michel-']
        
        if any(first_part.startswith(prefix) for prefix in compound_first_names):
            if len(remaining_parts) >= 2:
                # Prénom composé possible
                first_name = f"{first_part}{remaining_parts[0]}"
                last_name = " ".join(remaining_parts[1:])
            else:
                first_name = f"{first_part}{remaining_parts[0]}" if remaining_parts else first_part
                last_name = ""
        else:
            # Cas général : premier mot = prénom, reste = nom de famille
            first_name = first_part
            last_name = " ".join(remaining_parts)
        
        return first_name, last_name

def extract_lawyer_info(driver, card_element, index):
    """Extrait les informations d'un avocat depuis sa carte"""
    info = {
        'index': index,
        'prenom': '',
        'nom': '',
        'nom_complet': '',
        'email': '',
        'annee_inscription': '',
        'specialisations': '',
        'structure': '',
        'telephone': '',
        'adresse': '',
        'site_web': ''
    }
    
    try:
        # Récupérer le nom complet
        try:
            name_element = card_element.find_element(By.CSS_SELECTOR, ".listing-title h3 a")
            full_name = name_element.text.strip()
        except NoSuchElementException:
            try:
                name_element = card_element.find_element(By.CSS_SELECTOR, "h3 a")
                full_name = name_element.text.strip()
            except NoSuchElementException:
                print(f"  ⚠️ {index}: Nom non trouvé")
                return info
        
        info['nom_complet'] = full_name
        
        # Séparer prénom et nom
        first_name, last_name = separate_name(full_name)
        info['prenom'] = first_name
        info['nom'] = last_name
        
        print(f"  📝 {index}: {first_name} {last_name}")
        
        # Récupérer l'email
        try:
            email_element = card_element.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
            info['email'] = email_element.get_attribute('href').replace('mailto:', '')
        except NoSuchElementException:
            pass
        
        # Récupérer les spécialisations
        try:
            specializations = []
            spec_elements = card_element.find_elements(By.CSS_SELECTOR, ".listing-details a[href*='/wpbdp_category/']")
            for spec_element in spec_elements:
                spec_text = spec_element.text.strip()
                if spec_text:
                    specializations.append(spec_text)
            
            info['specialisations'] = ", ".join(specializations)
        except Exception:
            pass
        
        # Récupérer les informations textuelles
        try:
            card_text = card_element.text
            
            # Téléphone
            phone_match = re.search(r'Téléphone\s*:?\s*([\d\s\.\-\+]+)', card_text)
            if phone_match:
                info['telephone'] = phone_match.group(1).strip()
            
            # Adresse
            address_match = re.search(r'Adresse\s*:?\s*([^\n]+)', card_text)
            if address_match:
                info['adresse'] = address_match.group(1).strip()
            
            # Année d'inscription
            year_match = re.search(r'\b(19|20)\d{2}\b', card_text)
            if year_match:
                info['annee_inscription'] = year_match.group(0)
                
        except Exception:
            pass
        
        # Site web
        try:
            website_elements = card_element.find_elements(By.CSS_SELECTOR, ".listing-details a[href^='http']")
            for website_element in website_elements:
                href = website_element.get_attribute('href')
                if 'mailto' not in href and href:
                    info['site_web'] = href
                    break
        except Exception:
            pass
            
    except Exception as e:
        print(f"  ❌ {index}: Erreur extraction : {e}")
    
    return info

def scrape_all_lawyers():
    """Scraping complet de tous les avocats du Barreau de Laval"""
    print("🚀 SCRAPING COMPLET - Barreau de Laval")
    print("🔇 Mode headless activé")
    
    # Créer le timestamp pour les fichiers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    driver = setup_driver(headless=True)
    
    try:
        # Charger la page
        url = "https://barreau-de-laval.com/annuaire-professionnel/"
        print(f"🌐 Chargement: {url}")
        driver.get(url)
        
        # Gérer les cookies
        handle_cookies(driver)
        
        # Attendre le chargement
        print("⏳ Attente du chargement complet...")
        time.sleep(5)
        
        # Attendre et récupérer toutes les cartes
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wpbdp-listing"))
            )
            print("✅ Contenu chargé")
        except TimeoutException:
            print("⚠️ Timeout - tentative de continuation...")
        
        # Récupérer toutes les cartes d'avocats
        lawyer_cards = driver.find_elements(By.CSS_SELECTOR, ".wpbdp-listing")
        total_lawyers = len(lawyer_cards)
        
        print(f"📊 {total_lawyers} avocats détectés")
        
        if not lawyer_cards:
            print("❌ Aucune carte d'avocat trouvée")
            return False
        
        lawyers_data = []
        successful_extractions = 0
        
        # Traitement de chaque avocat
        for i, card in enumerate(lawyer_cards, 1):
            try:
                info = extract_lawyer_info(driver, card, i)
                
                # Vérifier si on a au moins le nom
                if info['nom_complet'] and info['nom_complet'].strip():
                    lawyers_data.append(info)
                    successful_extractions += 1
                else:
                    print(f"  ⚠️ {i}: Données insuffisantes")
                    
            except Exception as e:
                print(f"  ❌ {i}: Erreur traitement: {e}")
            
            # Progress update every 10 lawyers
            if i % 10 == 0:
                print(f"📈 Progression: {i}/{total_lawyers} ({successful_extractions} réussis)")
            
            # Petite pause pour éviter la surcharge
            time.sleep(0.5)
        
        print(f"\n✅ Extraction terminée!")
        print(f"📊 {successful_extractions}/{total_lawyers} avocats extraits avec succès")
        
        # Sauvegarde des résultats
        if lawyers_data:
            # Fichier CSV
            csv_filename = f"/Users/paularnould/LAVAL_COMPLET_{successful_extractions}_avocats_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['index', 'prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 'specialisations', 'annee_inscription', 'structure', 'site_web']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(lawyers_data)
            
            # Fichier JSON
            json_filename = f"/Users/paularnould/LAVAL_COMPLET_{successful_extractions}_avocats_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(lawyers_data, f, indent=2, ensure_ascii=False)
            
            # Rapport détaillé
            report_filename = f"/Users/paularnould/LAVAL_RAPPORT_COMPLET_{timestamp}.txt"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(f"RAPPORT COMPLET - Barreau de Laval\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL source: {url}\n")
                f.write(f"Total avocats détectés: {total_lawyers}\n")
                f.write(f"Avocats extraits avec succès: {successful_extractions}\n")
                f.write(f"Taux de réussite: {(successful_extractions/total_lawyers)*100:.1f}%\n\n")
                
                # Statistiques
                emails_count = len([l for l in lawyers_data if l['email']])
                phones_count = len([l for l in lawyers_data if l['telephone']])
                specializations_count = len([l for l in lawyers_data if l['specialisations']])
                
                f.write(f"STATISTIQUES:\n")
                f.write(f"- Avocats avec email: {emails_count} ({(emails_count/successful_extractions)*100:.1f}%)\n")
                f.write(f"- Avocats avec téléphone: {phones_count} ({(phones_count/successful_extractions)*100:.1f}%)\n")
                f.write(f"- Avocats avec spécialisations: {specializations_count} ({(specializations_count/successful_extractions)*100:.1f}%)\n\n")
                
                f.write(f"LISTE COMPLÈTE:\n")
                f.write(f"{'-'*60}\n")
                for lawyer in lawyers_data:
                    f.write(f"\n{lawyer['index']}. {lawyer['prenom']} {lawyer['nom']}\n")
                    f.write(f"   Email: {lawyer['email'] if lawyer['email'] else 'Non renseigné'}\n")
                    f.write(f"   Téléphone: {lawyer['telephone'] if lawyer['telephone'] else 'Non renseigné'}\n")
                    f.write(f"   Spécialisations: {lawyer['specialisations'] if lawyer['specialisations'] else 'Non renseignées'}\n")
                    if lawyer['adresse']:
                        f.write(f"   Adresse: {lawyer['adresse']}\n")
            
            # Fichier emails uniquement
            emails_filename = f"/Users/paularnould/LAVAL_EMAILS_SEULEMENT_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as f:
                f.write("EMAILS - Barreau de Laval\n")
                f.write("="*40 + "\n\n")
                for lawyer in lawyers_data:
                    if lawyer['email']:
                        f.write(f"{lawyer['email']}\n")
            
            print(f"\n💾 Fichiers générés:")
            print(f"   📄 CSV: {csv_filename}")
            print(f"   📄 JSON: {json_filename}")
            print(f"   📄 Rapport: {report_filename}")
            print(f"   📧 Emails: {emails_filename}")
            
            return True
        else:
            print("❌ Aucune donnée extraite")
            return False
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False
        
    finally:
        print("🔄 Fermeture du navigateur...")
        driver.quit()

if __name__ == "__main__":
    print(f"⏰ Début d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = scrape_all_lawyers()
    
    print(f"⏰ Fin d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("\n🎉 EXTRACTION COMPLÈTE TERMINÉE AVEC SUCCÈS!")
        print("📊 Tous les fichiers de résultats sont prêts.")
    else:
        print("\n⚠️ Extraction échouée. Vérifiez les logs ci-dessus.")
        
    print(f"\nℹ️ Le script s'est exécuté en mode headless (pas de fenêtres ouvertes)")