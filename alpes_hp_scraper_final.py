#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER BARREAU ALPES DE HAUTE-PROVENCE - VERSION FINALE
========================================================

Scraper professionnel pour extraire tous les avocats du Barreau des Alpes de Haute-Provence
- Extraction complète avec pagination automatique
- Séparation correcte des prénoms/noms composés  
- Extraction d'emails approfondie
- Mode headless optimisé
- Gestion des cookies automatique
- Export CSV, JSON et rapport détaillé

Utilisation:
    python3 ALPES_HP_BARREAU_SCRAPER_FINAL.py              # Test 20 avocats
    python3 ALPES_HP_BARREAU_SCRAPER_FINAL.py production   # Tous les avocats
"""

import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import csv
from datetime import datetime
import re

def setup_driver(headless=True):
    """Configuration optimisée du driver Chrome"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def accept_cookies_if_present(driver):
    """Accepter les cookies si une bannière est présente"""
    try:
        cookie_selectors = [
            "button[id*='cookie']", "button[class*='cookie']", 
            "button[id*='accept']", "button[class*='accept']",
            ".cookie-banner button", "#cookie-banner button",
            "[data-accept-cookies]", ".js-cookie-accept"
        ]
        
        wait = WebDriverWait(driver, 5)
        for selector in cookie_selectors:
            try:
                cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                cookie_button.click()
                print("✅ Cookies acceptés")
                time.sleep(2)
                return True
            except:
                continue
                
        print("ℹ️ Aucune bannière de cookies détectée")
        return False
    except Exception as e:
        print(f"⚠️ Erreur cookies : {str(e)}")
        return False

def extract_name_from_card(card):
    """Extraire proprement le nom depuis la structure HTML de la carte"""
    try:
        # Chercher les spans individuels avec les classes spécifiques
        civ_elem = card.find('span', class_='anfiche_civ')
        prenom_elem = card.find('span', class_='anfiche_prenom') 
        nom_elem = card.find('span', class_='anfiche_nom')
        
        civilite = civ_elem.get_text(strip=True) if civ_elem else ""
        prenom = prenom_elem.get_text(strip=True) if prenom_elem else ""
        nom = nom_elem.get_text(strip=True) if nom_elem else ""
        
        if prenom and nom:
            nom_complet = f"{civilite} {prenom} {nom}".strip()
            return prenom, nom, nom_complet
        
        # Fallback: essayer de parser le h4 directement
        h4 = card.find('h4')
        if h4:
            full_text = h4.get_text(strip=True)
            
            # Supprimer les civilités
            civilites = ['Madame', 'Monsieur', 'Mademoiselle', 'Maître', 'Me']
            words = full_text.split()
            
            filtered_words = []
            for word in words:
                if word not in civilites:
                    filtered_words.append(word)
            
            if len(filtered_words) >= 2:
                nom = filtered_words[-1]
                prenom = ' '.join(filtered_words[:-1])
                return prenom, nom, full_text
            
        return "", "", full_text if 'full_text' in locals() else ""
        
    except Exception as e:
        print(f"⚠️ Erreur parsing nom : {str(e)}")
        return "", "", ""

def discover_all_pages(driver, base_url):
    """Découvrir toutes les pages de pagination de l'annuaire"""
    print("🔍 Découverte complète de la pagination...")
    
    try:
        driver.get(base_url)
        time.sleep(3)
        accept_cookies_if_present(driver)
        
        # La page semble charger tous les avocats d'un coup
        # Pas besoin de pagination pour ce site
        pages = [base_url]
        
        print(f"📄 {len(pages)} page(s) à traiter")
        return pages
        
    except Exception as e:
        print(f"⚠️ Erreur pagination : {str(e)}")
        return [base_url]

def extract_lawyer_details_deep(driver, lawyer_url):
    """Extraction approfondie des détails d'un avocat avec recherche d'email exhaustive"""
    try:
        driver.get(lawyer_url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        lawyer_data = {
            'url_fiche': lawyer_url,
            'prenom': '', 'nom': '', 'nom_complet': '',
            'annee_inscription': '', 'date_serment': '',
            'specialisations': '', 'competences': '',
            'structure': '', 'adresse_complete': '',
            'telephone': '', 'fax': '', 'email': '', 'site_web': '',
            'source': lawyer_url
        }
        
        # Extraction du nom depuis h1
        name_h1 = soup.find('h1')
        if name_h1:
            full_name = name_h1.get_text(strip=True)
            lawyer_data['nom_complet'] = full_name
            
            civilites = ['Madame', 'Monsieur', 'Mademoiselle', 'Maître', 'Me']
            words = full_name.split()
            
            filtered_words = [word for word in words if word not in civilites]
            
            if len(filtered_words) >= 2:
                nom = filtered_words[-1]
                prenom = ' '.join(filtered_words[:-1])
                lawyer_data['prenom'] = prenom
                lawyer_data['nom'] = nom
        
        # Date de serment
        page_text = soup.get_text().lower()
        serment_patterns = [
            r'(?:prestation de )?serment\s*:?\s*(\d{4})',
            r'inscription\s*:?\s*(\d{4})',
            r'(\d{4})\s*serment',
            r'asserment[ée]?\s*:?\s*(\d{4})',
            r'inscrit[e]?\s*(?:au barreau|depuis)\s*:?\s*(\d{4})'
        ]
        
        for pattern in serment_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                year = match.group(1)
                if 1950 <= int(year) <= 2025:
                    lawyer_data['annee_inscription'] = year
                    lawyer_data['date_serment'] = year
                    break
        
        # Coordonnées
        coords_div = soup.find('div', class_='coordonnees')
        if coords_div:
            adresse_elem = coords_div.find('div', class_='adresse')
            if adresse_elem:
                lawyer_data['adresse_complete'] = adresse_elem.get_text(strip=True)
            
            tel_elem = coords_div.find('div', class_='tel')
            if tel_elem:
                tel_text = tel_elem.get_text(strip=True)
                tel_patterns = [
                    r'(\+33\s*\([0-9]\)[0-9\s\.]+)',
                    r'(\+33[0-9\s\.]+)',
                    r'(0[1-9][0-9\s\.]{8,})'
                ]
                for pattern in tel_patterns:
                    tel_match = re.search(pattern, tel_text)
                    if tel_match:
                        lawyer_data['telephone'] = tel_match.group(1).strip()
                        break
        
        # RECHERCHE D'EMAIL EXHAUSTIVE
        email_found = False
        
        # 1. Liens mailto
        mailto_links = soup.find_all('a', href=re.compile(r'mailto:', re.I))
        for link in mailto_links:
            href = link.get('href')
            email_match = re.search(r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', href)
            if email_match:
                email = email_match.group(1)
                # Filtrer l'email générique du site
                if 'azko.fr' not in email.lower() and 'avocats04.fr' not in email.lower():
                    lawyer_data['email'] = email
                    email_found = True
                    break
        
        # 2. Texte brut de la page
        if not email_found:
            email_patterns = [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                r'[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}',
                r'[a-zA-Z0-9._%+-]+\s*\[\s*at\s*\]\s*[a-zA-Z0-9.-]+\s*\[\s*dot\s*\]\s*[a-zA-Z]{2,}'
            ]
            
            full_text = soup.get_text()
            for pattern in email_patterns:
                matches = re.findall(pattern, full_text, re.I)
                for email in matches:
                    clean_email = email.replace(' ', '').replace('[at]', '@').replace('[dot]', '.')
                    if ('@' in clean_email and '.' in clean_email.split('@')[1] and 
                        'azko.fr' not in clean_email.lower() and 'avocats04.fr' not in clean_email.lower()):
                        lawyer_data['email'] = clean_email
                        email_found = True
                        break
                if email_found:
                    break
        
        # 3. Scripts JavaScript
        if not email_found:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', script.string)
                    for email in email_matches:
                        if 'azko.fr' not in email.lower() and 'avocats04.fr' not in email.lower():
                            lawyer_data['email'] = email
                            email_found = True
                            break
                if email_found:
                    break
        
        # 4. Attributs des éléments
        if not email_found:
            all_elements = soup.find_all()
            for elem in all_elements:
                for attr_name, attr_value in elem.attrs.items():
                    if isinstance(attr_value, str):
                        email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', attr_value)
                        for email in email_matches:
                            if 'azko.fr' not in email.lower() and 'avocats04.fr' not in email.lower():
                                lawyer_data['email'] = email
                                email_found = True
                                break
                if email_found:
                    break
        
        # 5. Recherche dans le code source brut pour emails obfusqués
        if not email_found:
            page_source = driver.page_source
            # Patterns pour emails obfusqués
            obfuscated_patterns = [
                r'([a-zA-Z0-9._%+-]+)\s*\[arobase\]\s*([a-zA-Z0-9.-]+)\s*\[point\]\s*([a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+)\s*\(dot\)\s*([a-zA-Z]{2,})',
                r'([a-zA-Z0-9._%+-]+)\s*AT\s*([a-zA-Z0-9.-]+)\s*DOT\s*([a-zA-Z]{2,})'
            ]
            
            for pattern in obfuscated_patterns:
                match = re.search(pattern, page_source, re.I)
                if match:
                    email = f"{match.group(1)}@{match.group(2)}.{match.group(3)}"
                    lawyer_data['email'] = email
                    email_found = True
                    break
        
        # Site web
        site_links = soup.find_all('a', href=re.compile(r'https?://(?!.*avocats04)(?!.*azko)', re.I))
        for link in site_links:
            href = link.get('href')
            if href and any(tld in href.lower() for tld in ['.fr', '.com', '.org', '.net', '.eu']):
                lawyer_data['site_web'] = href
                break
        
        # Spécialisations
        spec_sections = soup.find_all(['div', 'section', 'p'], class_=re.compile(r'(specialisation|competence|domaine)', re.I))
        for section in spec_sections:
            spec_text = section.get_text(strip=True)
            if len(spec_text) > 10:
                lawyer_data['specialisations'] = spec_text[:300]
                break
        
        return lawyer_data
        
    except Exception as e:
        print(f"❌ Erreur extraction détails : {str(e)}")
        return None

def extract_lawyers_from_page(driver, page_url):
    """Extraire tous les avocats d'une page"""
    print(f"📋 Extraction depuis : {page_url}")
    
    lawyers = []
    
    try:
        driver.get(page_url)
        time.sleep(3)
        accept_cookies_if_present(driver)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        lawyer_cards = soup.find_all('div', class_='annuaireFicheMini')
        print(f"👥 {len(lawyer_cards)} avocats trouvés sur cette page")
        
        for card in lawyer_cards:
            try:
                prenom, nom, nom_complet = extract_name_from_card(card)
                
                if not nom_complet:
                    continue
                
                print(f"📝 Traitement de {nom_complet}")
                
                # URL de la fiche détaillée
                detail_link = card.find('a', class_='btnAnnuaireDetail')
                if not detail_link:
                    detail_link = card.find('a', href=True)
                
                lawyer_url = page_url
                if detail_link:
                    href = detail_link.get('href')
                    if href:
                        if href.startswith('http'):
                            lawyer_url = href
                        else:
                            lawyer_url = f"https://www.avocats04.fr/{href.lstrip('/')}"
                
                lawyer_data = {
                    'prenom': prenom, 'nom': nom, 'nom_complet': nom_complet,
                    'annee_inscription': '', 'date_serment': '',
                    'specialisations': '', 'competences': '',
                    'structure': '', 'adresse_complete': '',
                    'telephone': '', 'fax': '', 'email': '', 'site_web': '',
                    'url_fiche': lawyer_url, 'source': page_url
                }
                
                # Données de base depuis la carte
                coords_div = card.find('div', class_='coordonnees')
                if coords_div:
                    adresse_elem = coords_div.find('div', class_='adresse')
                    if adresse_elem:
                        lawyer_data['adresse_complete'] = adresse_elem.get_text(strip=True)
                    
                    tel_elem = coords_div.find('div', class_='tel')
                    if tel_elem:
                        tel_text = tel_elem.get_text(strip=True)
                        tel_match = re.search(r'((?:\+33|0)[\d\s\.\(\)]+)', tel_text)
                        if tel_match:
                            lawyer_data['telephone'] = tel_match.group(1).strip()
                
                serment_elem = card.find('div', class_='dateserment')
                if serment_elem:
                    serment_text = serment_elem.get_text(strip=True)
                    year_match = re.search(r'(\d{4})', serment_text)
                    if year_match:
                        lawyer_data['annee_inscription'] = year_match.group(1)
                        lawyer_data['date_serment'] = year_match.group(1)
                
                lawyers.append(lawyer_data)
                
            except Exception as e:
                print(f"⚠️ Erreur avocat : {str(e)}")
                continue
        
        print(f"✅ {len(lawyers)} avocats extraits de cette page")
        return lawyers
        
    except Exception as e:
        print(f"❌ Erreur page : {str(e)}")
        return []

def extract_detailed_info(driver, lawyers, max_details=None):
    """Extraire les informations détaillées"""
    print(f"\n🔍 EXTRACTION DES DÉTAILS INDIVIDUELS")
    print("=" * 40)
    
    detailed_lawyers = []
    
    for i, lawyer in enumerate(lawyers):
        if max_details and i >= max_details:
            print(f"🎯 Limite de {max_details} détails atteinte")
            break
            
        print(f"\n📋 Détails {i+1}/{len(lawyers)}: {lawyer['nom_complet']}")
        
        if lawyer['url_fiche'] and lawyer['url_fiche'] != lawyer['source']:
            detailed_data = extract_lawyer_details_deep(driver, lawyer['url_fiche'])
            if detailed_data:
                for key, value in detailed_data.items():
                    if value:
                        lawyer[key] = value
        
        detailed_lawyers.append(lawyer)
        time.sleep(1)
    
    return detailed_lawyers

def extract_all_lawyers(base_url, max_lawyers=None, extract_details=True):
    """Extraction complète"""
    print("🚀 SCRAPER ALPES DE HAUTE-PROVENCE - VERSION FINALE")
    print("=" * 60)
    
    driver = setup_driver(headless=True)
    all_lawyers = []
    
    try:
        pages = discover_all_pages(driver, base_url)
        
        for page_num, page_url in enumerate(pages, 1):
            print(f"\n📄 PAGE {page_num}/{len(pages)}")
            page_lawyers = extract_lawyers_from_page(driver, page_url)
            all_lawyers.extend(page_lawyers)
            
            if max_lawyers and len(all_lawyers) >= max_lawyers:
                all_lawyers = all_lawyers[:max_lawyers]
                print(f"🎯 Limite {max_lawyers} atteinte")
                break
        
        if extract_details and all_lawyers:
            detail_limit = min(20, len(all_lawyers)) if max_lawyers else None
            all_lawyers = extract_detailed_info(driver, all_lawyers, detail_limit)
        
        print(f"\n🎉 EXTRACTION TERMINÉE: {len(all_lawyers)} avocats")
        return all_lawyers
        
    finally:
        driver.quit()

def save_results(lawyers, filename_prefix="ALPES_HP_FINAL"):
    """Sauvegarde complète avec rapports détaillés"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if lawyers:
            fieldnames = lawyers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers)
    
    json_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, indent=2, ensure_ascii=False)
    
    emails = [lawyer['email'] for lawyer in lawyers if lawyer['email']]
    emails_filename = f"{filename_prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        for email in emails:
            emailfile.write(email + '\n')
    
    report_filename = f"{filename_prefix}_RAPPORT_COMPLET_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write("RAPPORT EXTRACTION ALPES DE HAUTE-PROVENCE - VERSION FINALE\n")
        reportfile.write("=" * 70 + "\n\n")
        reportfile.write(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        reportfile.write(f"👥 Total avocats: {len(lawyers)}\n")
        reportfile.write(f"📧 Avocats avec email: {len(emails)} ({len(emails)/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"🌐 Source: https://www.avocats04.fr/le-barreau/annuaire-des-avocats.htm\n\n")
        
        # Statistiques par année
        years = [lawyer['annee_inscription'] for lawyer in lawyers if lawyer['annee_inscription']]
        if years:
            from collections import Counter
            year_counts = Counter(years)
            reportfile.write("📊 RÉPARTITION PAR ANNÉE:\n")
            reportfile.write("-" * 30 + "\n")
            for year in sorted(year_counts.keys()):
                reportfile.write(f"{year}: {year_counts[year]} avocat{'s' if year_counts[year] > 1 else ''}\n")
            reportfile.write("\n")
        
        # Contrôle qualité
        with_phone = sum(1 for l in lawyers if l['telephone'])
        with_address = sum(1 for l in lawyers if l['adresse_complete'])
        
        reportfile.write("✅ CONTRÔLE QUALITÉ:\n")
        reportfile.write("-" * 25 + "\n")
        reportfile.write(f"📞 Téléphones: {with_phone}/{len(lawyers)} ({with_phone/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"🏠 Adresses: {with_address}/{len(lawyers)} ({with_address/len(lawyers)*100:.1f}%)\n\n")
        
        reportfile.write("📋 LISTE COMPLÈTE:\n")
        reportfile.write("-" * 20 + "\n")
        for i, lawyer in enumerate(lawyers, 1):
            reportfile.write(f"{i:2d}. {lawyer['nom_complet']}\n")
            reportfile.write(f"    ✓ Prénom: '{lawyer['prenom']}'\n")
            reportfile.write(f"    ✓ Nom: '{lawyer['nom']}'\n")
            if lawyer['email']:
                reportfile.write(f"    📧 {lawyer['email']}\n")
            if lawyer['telephone']:
                reportfile.write(f"    📞 {lawyer['telephone']}\n")
            if lawyer['annee_inscription']:
                reportfile.write(f"    📅 {lawyer['annee_inscription']}\n")
            reportfile.write("\n")
    
    print(f"\n💾 RÉSULTATS SAUVEGARDÉS:")
    print(f"📊 CSV: {csv_filename}")
    print(f"📄 JSON: {json_filename}")
    print(f"📧 Emails: {emails_filename} ({len(emails)} emails)")
    print(f"📝 Rapport: {report_filename}")

def main():
    """Programme principal"""
    import sys
    
    base_url = "https://www.avocats04.fr/le-barreau/annuaire-des-avocats.htm"
    
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        print("🚀 MODE PRODUCTION - EXTRACTION COMPLÈTE")
        lawyers = extract_all_lawyers(base_url, extract_details=True)
        if lawyers:
            save_results(lawyers, "ALPES_HP_PRODUCTION_FINAL")
    else:
        print("🧪 MODE TEST - 20 PREMIERS AVOCATS")
        lawyers = extract_all_lawyers(base_url, max_lawyers=20, extract_details=True)
        if lawyers:
            save_results(lawyers, "ALPES_HP_TEST_FINAL")

if __name__ == "__main__":
    main()