#!/usr/bin/env python3
"""
SCRAPER LIMOGES COMPLET - VERSION OPTIMISÉE
Traite toutes les pages automatiquement avec consolidation finale
"""

import sys
import time
import csv
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_single_page(page_number):
    """Scrape UNE SEULE page"""
    
    # URLs des pages
    pages_config = {
        1: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html", 30),
        2: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=30", 30),
        3: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=60", 30),
        4: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=90", 30),
        5: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=120", 30),
        6: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=150", 30),
        7: ("https://www.avocats-limoges.org/annuaire-des-avocats/searching.html?limitstart=180", 14)
    }
    
    if page_number not in pages_config:
        return False, []
    
    page_url, expected_count = pages_config[page_number]
    
    driver = setup_driver()
    page_lawyers = []
    
    try:
        # 1. Charge la page
        driver.get(page_url)
        time.sleep(1.5)
        
        # 2. Récupère tous les liens cb-profile
        elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='cb-profile']")
        profile_links = []
        
        for element in elements:
            href = element.get_attribute('href')
            if href and 'cb-profile' in href:
                profile_links.append(href)
        
        # Supprime les doublons
        unique_links = list(set(profile_links))
        
        if len(unique_links) == 0:
            return False, []
        
        # 3. Traite chaque profil
        for i, profile_url in enumerate(unique_links, 1):            
            try:
                driver.get(profile_url)
                time.sleep(0.3)
                
                # Structure complète des données
                lawyer = {
                    'prenom': '',
                    'nom': '',
                    'email': '',
                    'annee_inscription': '',
                    'specialisations': '',
                    'structure': '',
                    'telephone': '',
                    'adresse': '',
                    'source_url': profile_url
                }
                
                # Récupère tout le texte de la page
                try:
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                except:
                    page_text = ""
                
                # 1. Nom et prénom depuis h3
                try:
                    h3 = driver.find_element(By.CSS_SELECTOR, "h3")
                    full_name = h3.text.strip().replace("Maître", "").strip()
                    parts = full_name.split()
                    if len(parts) >= 2:
                        lawyer['prenom'] = parts[0]
                        lawyer['nom'] = ' '.join(parts[1:])
                    elif len(parts) == 1:
                        lawyer['nom'] = parts[0]
                except:
                    pass
                
                # 2. Email
                try:
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text)
                    if emails:
                        lawyer['email'] = emails[0]
                except:
                    pass
                
                # 3. Année d'inscription au barreau
                try:
                    # Cherche "Prestation de serment: DD/MM/YYYY"
                    serment_match = re.search(r'Prestation de serment[:\s]*(\d{1,2}[/\-]\d{1,2}[/\-](\d{4}))', page_text)
                    if serment_match:
                        lawyer['annee_inscription'] = serment_match.group(2)
                except:
                    pass
                
                # 4. Spécialisations
                try:
                    # Cherche après "Spécialisation(s) :"
                    spec_match = re.search(r'Spécialisation\(s\)\s*:([^\n]+)', page_text)
                    if spec_match:
                        specialisations = spec_match.group(1).strip()
                        # Nettoie les spécialisations
                        if specialisations and not any(word in specialisations.lower() for word in ['espace', 'maison', 'avocat', 'téléphone', 'fax']):
                            lawyer['specialisations'] = specialisations
                except:
                    pass
                
                # 5. Téléphone
                try:
                    tel_matches = re.findall(r'Téléphone[:\s]*([0-9\s\.\-]+)', page_text)
                    if tel_matches:
                        # Prend le premier téléphone (celui de l'avocat, pas du barreau)
                        telephone = tel_matches[0].strip()
                        if not telephone.startswith('05.55.34.40.63'):  # Évite le téléphone du barreau
                            lawyer['telephone'] = telephone
                except:
                    pass
                
                # 6. Adresse (première ligne d'adresse trouvée)
                try:
                    # Cherche une adresse avec numéro et nom de rue/avenue/place
                    addr_match = re.search(r'(\d+[^\n]*(?:rue|avenue|place|boulevard|impasse|Emile)[^\n]*\d{5}[^\n]*)', page_text, re.IGNORECASE)
                    if addr_match:
                        adresse = addr_match.group(1).strip()
                        # Évite l'adresse du barreau
                        if 'Winston Churchill' not in adresse:
                            lawyer['adresse'] = adresse
                except:
                    pass
                
                # 7. Structure/Cabinet (extraction basique)
                try:
                    # Si il y a plusieurs lignes avant l'adresse, c'est peut-être le nom du cabinet
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if 'Maître' in line and lawyer['nom'] in line:
                            # Regarde les lignes suivantes pour trouver un nom de cabinet
                            for j in range(i+1, min(i+4, len(lines))):
                                next_line = lines[j].strip()
                                if next_line and not any(word in next_line.lower() for word in ['prestation', 'téléphone', 'email', 'serment', 'spécialisation']):
                                    if re.match(r'^[A-Z]', next_line) and len(next_line) > 3:
                                        lawyer['structure'] = next_line
                                        break
                            break
                except:
                    pass
                
                if lawyer['nom'] or lawyer['email']:
                    page_lawyers.append(lawyer)
                
            except Exception:
                pass
        
        return True, page_lawyers
            
    except Exception:
        return False, []
        
    finally:
        driver.quit()

def consolidate_and_save(all_lawyers_data):
    """Consolide tous les avocats et sauvegarde"""
    
    all_lawyers = []
    for page_data in all_lawyers_data:
        all_lawyers.extend(page_data)
    
    # Supprime les doublons par URL
    seen_urls = set()
    unique_lawyers = []
    
    for lawyer in all_lawyers:
        url = lawyer.get('source_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_lawyers.append(lawyer)
    
    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"LIMOGES_COMPLET_{len(unique_lawyers)}_avocats_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['prenom', 'nom', 'email', 'annee_inscription', 'specialisations', 'structure', 'telephone', 'adresse', 'source_url']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_lawyers)
    
    return filename, len(unique_lawyers)

def main():
    """Scraper complet automatique"""
    print("🎯 SCRAPER LIMOGES COMPLET - VERSION OPTIMISÉE")
    print("=" * 50)
    
    all_lawyers_data = []
    successful_pages = []
    failed_pages = []
    
    for page_num in range(1, 8):
        print(f"\n📄 PAGE {page_num}/7", end=" ", flush=True)
        
        success, lawyers = scrape_single_page(page_num)
        if success and lawyers:
            successful_pages.append(page_num)
            all_lawyers_data.append(lawyers)
            print(f"✅ ({len(lawyers)} avocats)")
        else:
            failed_pages.append(page_num)
            print("❌")
        
        # Petite pause
        if page_num < 7:
            time.sleep(0.5)
    
    # Bilan
    print(f"\n📊 BILAN:")
    print(f"✅ Pages réussies: {len(successful_pages)}/7")
    if failed_pages:
        print(f"❌ Pages échouées: {failed_pages}")
    
    # Consolidation
    if successful_pages:
        print(f"\n🔗 Consolidation...")
        filename, total = consolidate_and_save(all_lawyers_data)
        print(f"💾 Fichier final: {filename}")
        print(f"📊 Total: {total} avocats")
        print(f"\n🎉 MISSION ACCOMPLIE!")
    else:
        print(f"\n❌ AUCUNE PAGE EXTRAITE")

if __name__ == "__main__":
    main()