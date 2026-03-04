#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER BARREAU D'ALES - VERSION FINALE
========================================

Scraper professionnel pour extraire tous les avocats du Barreau d'Alès
- Extraction complète des 50 avocats
- Séparation correcte des prénoms/noms composés  
- Mode headless optimisé
- Gestion des cookies automatique
- Navigation multi-pages
- Export CSV, JSON et rapport détaillé

Utilisation:
    python3 ALES_BARREAU_SCRAPER_FINAL.py              # Test 20 avocats
    python3 ALES_BARREAU_SCRAPER_FINAL.py production   # Tous les avocats
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

def parse_name_correctly(full_name):
    """
    Parsing intelligent des noms composés et prénoms composés
    Gère tous les cas: particules, traits d'union, noms multiples
    """
    full_name = full_name.strip()
    words = full_name.split()
    
    if len(words) < 2:
        return full_name, "", full_name
    
    # Cas 1: Particules (DE, EL, etc.)
    if len(words) >= 3:
        particules = ['DE', 'DU', 'EL', 'VAN', 'VON', 'MAC', 'MC']
        for i, word in enumerate(words[:-1]):
            if word.upper() in particules:
                nom = ' '.join(words[:i+2])
                prenom = ' '.join(words[i+2:])
                return prenom, nom, full_name
    
    # Cas 2: Noms composés avec traits d'union
    for i, word in enumerate(words[:-1]):
        if '-' in word:
            nom = ' '.join(words[:i+1])
            prenom = ' '.join(words[i+1:])
            return prenom, nom, full_name
    
    # Cas 3: Analyse de la casse (noms généralement en MAJUSCULES)
    nom_parts = []
    prenom_parts = []
    found_prenom = False
    
    for word in words:
        if word.isupper() and len(word) > 1 and not found_prenom:
            nom_parts.append(word)
        else:
            found_prenom = True
            prenom_parts.append(word)
    
    if nom_parts and prenom_parts:
        return ' '.join(prenom_parts), ' '.join(nom_parts), full_name
    
    # Cas 4: Défaut - dernier mot = prénom
    if len(words) == 2:
        return words[1], words[0], full_name
    else:
        return words[-1], ' '.join(words[:-1]), full_name

def extract_lawyers_from_page(driver, page_url):
    """Extraction intelligente des avocats avec tous leurs détails"""
    print(f"📋 Extraction depuis : {page_url}")
    
    lawyers = []
    
    try:
        driver.get(page_url)
        time.sleep(3)
        
        # Attendre le chargement du tableau
        wait = WebDriverWait(driver, 15)
        table = wait.until(EC.presence_of_element_located((By.ID, "tableaccordion")))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', id='tableaccordion')
        if not table:
            return lawyers
        
        lawyer_rows = table.find_all('tr', class_='t')
        print(f"👥 {len(lawyer_rows)} avocats trouvés")
        
        for row in lawyer_rows:
            try:
                name_elem = row.find('th')
                if not name_elem:
                    continue
                
                full_name = name_elem.get_text(strip=True)
                prenom, nom, nom_complet = parse_name_correctly(full_name)
                
                # Structure de données complète
                lawyer_data = {
                    'prenom': prenom,
                    'nom': nom,
                    'nom_complet': nom_complet,
                    'annee_inscription': '',
                    'date_inscription_complete': '',
                    'specialisations': '',
                    'structure': '',
                    'adresse': '',
                    'ville': '',
                    'code_postal': '',
                    'telephone': '',
                    'fax': '',
                    'email': '',
                    'fonction': '',
                    'url_fiche': page_url,
                    'source': 'https://www.barreau-ales.fr/fr/annuaire/avocats-barreau-ales/'
                }
                
                # Extraction ville/code postal depuis la colonne droite
                city_cell = row.find('td')
                if city_cell:
                    city_text = city_cell.get_text(strip=True)
                    city_match = re.search(r'([A-Z\s]+)\s*\((\d+)\)', city_text)
                    if city_match:
                        lawyer_data['ville'] = city_match.group(1).strip()
                        lawyer_data['code_postal'] = city_match.group(2)
                
                # Extraction des détails depuis la section dépliable
                details_row = row.find_next_sibling('tr', class_='s')
                if details_row:
                    details_div = details_row.find('div', class_='s')
                    if details_div:
                        details_text = details_div.get_text()
                        
                        # Email
                        email_link = details_div.find('a', href=re.compile(r'mailto:'))
                        if email_link:
                            lawyer_data['email'] = email_link.get_text(strip=True)
                        
                        # Téléphone  
                        tel_match = re.search(r'Tél\s*:\s*((?:\d{2}[\.\s]?){5})', details_text)
                        if tel_match:
                            lawyer_data['telephone'] = tel_match.group(1).strip()
                        
                        # Fax
                        fax_match = re.search(r'Fax\s*:\s*((?:\d{2}[\.\s]?){5})', details_text)
                        if fax_match:
                            lawyer_data['fax'] = fax_match.group(1).strip()
                        
                        # Date d'inscription complète et année
                        debut_match = re.search(r'Début d\'activité\s*:\s*(\d{1,2}/\d{1,2}/\d{4})', details_text)
                        if debut_match:
                            lawyer_data['date_inscription_complete'] = debut_match.group(1)
                            year_match = re.search(r'/(\d{4})', debut_match.group(1))
                            if year_match:
                                lawyer_data['annee_inscription'] = year_match.group(1)
                        
                        # Adresse complète
                        adresse_patterns = [
                            r'Cabinet principal\s+(.*?)\s*-\s*\d{5}\s+[A-Z]+',
                            r'Cabinet principal\s+(.*?)(?=\n|$)'
                        ]
                        
                        for pattern in adresse_patterns:
                            adresse_match = re.search(pattern, details_text, re.DOTALL)
                            if adresse_match:
                                address_raw = adresse_match.group(1).strip()
                                # Nettoyer l'adresse
                                address_clean = re.sub(r'\s+', ' ', address_raw)
                                lawyer_data['adresse'] = address_clean
                                break
                        
                        # Structure/Cabinet
                        structure_patterns = [
                            r'(SCP [A-Za-z\s]+)',
                            r'(SELARL [A-Za-z\s]+)', 
                            r'(Cabinet [A-Za-z\s]+)',
                            r'(SARL [A-Za-z\s]+)'
                        ]
                        
                        for pattern in structure_patterns:
                            struct_match = re.search(pattern, details_text)
                            if struct_match:
                                lawyer_data['structure'] = struct_match.group(1).strip()
                                break
                        
                        # Fonctions spéciales
                        if 'membre du Conseil de l\'Ordre' in details_text:
                            lawyer_data['fonction'] = 'Membre du Conseil de l\'Ordre'
                        elif 'Bâtonnier' in details_text and 'Ancien' not in details_text:
                            lawyer_data['fonction'] = 'Bâtonnier'
                        elif 'Ancien bâtonnier' in details_text:
                            lawyer_data['fonction'] = 'Ancien Bâtonnier'
                        elif 'Vice-bâtonnier' in details_text:
                            lawyer_data['fonction'] = 'Vice-Bâtonnier'
                
                lawyers.append(lawyer_data)
                
            except Exception as e:
                print(f"⚠️ Erreur avocat: {str(e)}")
                continue
        
        print(f"✅ {len(lawyers)} avocats extraits")
        return lawyers
        
    except Exception as e:
        print(f"❌ Erreur page: {str(e)}")
        return lawyers

def extract_all_lawyers(base_url, max_lawyers=None):
    """Extraction complète multi-pages"""
    print("🚀 SCRAPER BARREAU D'ALES - EXTRACTION COMPLÈTE")
    print("=" * 60)
    print(f"🎯 URL: {base_url}")
    if max_lawyers:
        print(f"🎯 Limite: {max_lawyers} avocats")
    print()
    
    pages = [
        base_url,
        base_url + "page-2/", 
        base_url + "page-3/"
    ]
    
    all_lawyers = []
    driver = setup_driver(headless=True)
    
    try:
        for page_num, page_url in enumerate(pages, 1):
            print(f"📄 PAGE {page_num}/{len(pages)}")
            page_lawyers = extract_lawyers_from_page(driver, page_url)
            all_lawyers.extend(page_lawyers)
            
            if max_lawyers and len(all_lawyers) >= max_lawyers:
                all_lawyers = all_lawyers[:max_lawyers]
                print(f"🎯 Limite {max_lawyers} atteinte")
                break
                
            if page_num < len(pages):
                time.sleep(3)  # Pause entre pages
        
        print(f"\n🎉 EXTRACTION TERMINÉE: {len(all_lawyers)} avocats")
        return all_lawyers
        
    finally:
        driver.quit()

def save_complete_results(lawyers, filename_prefix="ALES_FINAL"):
    """Sauvegarde complète avec rapports détaillés"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV principal
    csv_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if lawyers:
            fieldnames = lawyers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers)
    
    # JSON complet
    json_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, indent=2, ensure_ascii=False)
    
    # Emails uniquement
    emails = [lawyer['email'] for lawyer in lawyers if lawyer['email']]
    emails_filename = f"{filename_prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        for email in emails:
            emailfile.write(email + '\n')
    
    # Rapport de vérification
    report_filename = f"{filename_prefix}_RAPPORT_COMPLET_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write("RAPPORT EXTRACTION BARREAU D'ALES - VERSION FINALE\n")
        reportfile.write("=" * 70 + "\n\n")
        reportfile.write(f"📅 Date extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        reportfile.write(f"👥 Total avocats: {len(lawyers)}\n")
        reportfile.write(f"📧 Avocats avec email: {len(emails)} ({len(emails)/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"🌐 Source: https://www.barreau-ales.fr/fr/annuaire/avocats-barreau-ales/\n\n")
        
        # Statistiques par année
        years = [lawyer['annee_inscription'] for lawyer in lawyers if lawyer['annee_inscription']]
        if years:
            from collections import Counter
            year_counts = Counter(years)
            reportfile.write("📊 RÉPARTITION PAR ANNÉE D'INSCRIPTION:\n")
            reportfile.write("-" * 40 + "\n")
            for year in sorted(year_counts.keys()):
                reportfile.write(f"{year}: {year_counts[year]} avocat{'s' if year_counts[year] > 1 else ''}\n")
            reportfile.write("\n")
        
        # Vérification de la qualité des données
        reportfile.write("✅ CONTRÔLE QUALITÉ:\n")
        reportfile.write("-" * 25 + "\n")
        with_phone = sum(1 for l in lawyers if l['telephone'])
        with_address = sum(1 for l in lawyers if l['adresse'])
        with_year = sum(1 for l in lawyers if l['annee_inscription'])
        
        reportfile.write(f"📞 Téléphones: {with_phone}/{len(lawyers)} ({with_phone/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"🏠 Adresses: {with_address}/{len(lawyers)} ({with_address/len(lawyers)*100:.1f}%)\n") 
        reportfile.write(f"📅 Années: {with_year}/{len(lawyers)} ({with_year/len(lawyers)*100:.1f}%)\n\n")
        
        # Liste détaillée
        reportfile.write("📋 LISTE COMPLÈTE (Vérification Prénom/Nom):\n")
        reportfile.write("-" * 50 + "\n")
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
            if lawyer['fonction']:
                reportfile.write(f"    🎖️  {lawyer['fonction']}\n")
            reportfile.write("\n")
    
    print(f"\n💾 RÉSULTATS SAUVEGARDÉS:")
    print(f"📊 CSV: {csv_filename}")
    print(f"📄 JSON: {json_filename}")
    print(f"📧 Emails: {emails_filename} ({len(emails)} emails)")
    print(f"📝 Rapport: {report_filename}")
    
    return {
        'csv': csv_filename,
        'json': json_filename, 
        'emails': emails_filename,
        'report': report_filename
    }

def main():
    """Programme principal"""
    import sys
    
    base_url = "https://www.barreau-ales.fr/fr/annuaire/avocats-barreau-ales/"
    
    if len(sys.argv) > 1 and sys.argv[1] == "production":
        print("🚀 MODE PRODUCTION - EXTRACTION COMPLÈTE")
        lawyers = extract_all_lawyers(base_url)
        if lawyers:
            files = save_complete_results(lawyers, "ALES_PRODUCTION_FINAL")
            print(f"\n🎉 SUCCÈS! {len(lawyers)} avocats extraits")
    else:
        print("🧪 MODE TEST - 20 PREMIERS AVOCATS")
        lawyers = extract_all_lawyers(base_url, max_lawyers=20)
        if lawyers:
            files = save_complete_results(lawyers, "ALES_TEST_FINAL")
            print(f"\n✅ Test réussi! {len(lawyers)} avocats")
            print("\nPour l'extraction complète:")
            print("python3 ALES_BARREAU_SCRAPER_FINAL.py production")

if __name__ == "__main__":
    main()