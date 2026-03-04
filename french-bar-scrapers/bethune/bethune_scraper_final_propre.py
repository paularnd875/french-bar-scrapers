#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import json
import csv
from datetime import datetime
import re

# Liste complète des URLs (les 108 avocats)
LAWYER_URLS = [
    "https://www.barreaudebethune.com/page/annuaire/maitre-fanny-amourette-1.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-anne-charlotte-angoulvent-2.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-carine-bavencoffe-3.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-eloise-behra-4.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-rani-belmokhtar-5.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-francoise-bertrand-6.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-marianne-bleitrach-7.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-aurelie-boens-13.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sandra-bonnet-8.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-leila-boukrif-9.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-marine-boulanger-martin-10.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-christine-bouquet-wattez-11.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-virginie-bourgois-12.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-alexandre-braud-14.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-simon-breuvart-15.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-francois-xavier-brunet-16.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-regine-calzia-17.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-stephane-campagne-18.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-jean-louis-capelle-19.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sarah-castelain-20.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-jeremie-chabe-21.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-pierre-cianci-22.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-brigitte-coquempot-darras-23.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-blandine-crunelle-24.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-didier-darras-25.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-valerie-dautricourt-sorez-26.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-stephanie-debert-27.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-gaelle-delalieux-28.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-pauline-delattre-123.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-estelle-delattre-arena-29.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-jerome-delbreil-30.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-cindy-denisselle-gnilka-31.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-gael-dennetiere-32.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-maxime-deseure-33.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lorene-desmis-34.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-eric-devaux-35.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-elise-devriendt-36.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-david-dherbecourt-37.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-laurie-dubois-38.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-edouard-dubout-39.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sylvie-dumoulin-40.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-chloe-dupont-124.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-bastien-duriez-41.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-nathalie-erouart-42.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-cathy-faliva-43.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-arnaud-fasquelle-44.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-manon-favier-45.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-charlotte-feutrie-46.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-marine-flajolet-47.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-violaine-flamme-48.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-thomas-florczak-49.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-hortense-fontaine-50.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sylvie-fontaine-51.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-alicia-galet-52.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-garance-geoffroy-53.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-jean-bernard-geoffroy-54.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-elisabeth-gobbers-veniel-55.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sabrina-guedouar-56.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-bruno-guilbert-57.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-valentin-guislain-58.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sebastien-habourdin-59.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-elodie-hannoir-60.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-christophe-hareng-61.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-virginie-hecquet-62.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-ludovic-hemmerling-63.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-bertrand-henne-64.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-adeline-hermary-65.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-maxime-hermary-66.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-philippe-hure-67.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-gautier-lacherie-69.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-anastasia-langlois-blanquart-70.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-diane-laur-71.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-kathy-lavogez-72.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-ophelie-lecolier-78.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-florentin-leleu-73.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-melinda-leleu-74.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-anne-celine-lemonnier-75.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-pascal-leroy-126.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-christophe-loonis-76.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lea-lorthios-77.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-marie-machicoane-francois-79.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lisa-madeleine-80.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-fanny-malbrancq-81.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-anne-beatrice-malet-82.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-emmanuelle-mauro-83.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-alexis-merlin-84.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-nafa-mezine-85.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-louise-milhomme-86.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-david-mink-87.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-melodie-morel-125.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-mildrey-nguema-88.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-charlotte-nourry-89.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-celine-omer-90.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-camille-pahaut-91.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-jean-francois-pambo-92.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-tarecq-parmentier-chebaro-93.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lynda-peirenboom-94.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-camille-penez-95.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sophie-philippe-96.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-charlotte-pidoux-97.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-aurelia-planque-98.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-philippe-preudhomme-99.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-elise-queinnec-100.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-aurelie-richard-101.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-antoine-robert-102.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-emmanuel-rousseaux-103.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-clemence-saunier-104.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-stephane-schoner-105.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-edwige-senaya-106.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-camille-senechal-109.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-maud-siedlecki-107.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-delphine-sroka-108.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-alexandra-tancre-110.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lucie-tellier-111.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-gerald-vairon-112.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-lysiane-vairon-113.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-brigitte-van-rompu-114.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-tiffany-vandrepotte-115.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sophie-vanhamme-116.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-sylvie-vantroyen-117.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-pauline-verfaillie-lecomte-118.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-johann-verhaest-119.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-eric-waterlot-120.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-philippine-wattez-bouquet-121.htm",
    "https://www.barreaudebethune.com/page/annuaire/maitre-alexandre-zehnder-122.htm"
]

def setup_driver():
    """Configuration du driver Chrome optimisé"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ Erreur driver: {e}")
        return None

def separate_name(full_name):
    """Séparer prénom et nom en gérant les noms composés"""
    if not full_name:
        return "", ""
    
    full_name = full_name.strip()
    
    # Nettoyer les titres
    titles = ['Me', 'Maître', 'M.', 'Mme', 'Mr', 'Mrs', 'Dr', 'Docteur']
    for title in titles:
        if full_name.startswith(title):
            full_name = full_name[len(title):].strip()
    
    parts = full_name.split()
    
    if len(parts) == 1:
        return parts[0], ""
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        prenom = " ".join(parts[:-1])
        nom = parts[-1]
        
        # Gestion des particules
        particles = ['de', 'du', 'des', 'van', 'von', 'da', 'del', 'della', 'le', 'la', 'les']
        if len(parts) > 2 and parts[-2].lower() in particles:
            prenom = " ".join(parts[:-2])
            nom = " ".join(parts[-2:])
            
        return prenom, nom

def clean_city_name(city):
    """Nettoyer le nom de ville"""
    if not city:
        return ""
    
    prefixes_to_remove = ['e ', 'de ', 'du ', 'des ', 'le ', 'la ', 'les ']
    city_cleaned = city.strip()
    
    for prefix in prefixes_to_remove:
        if city_cleaned.lower().startswith(prefix):
            city_cleaned = city_cleaned[len(prefix):].strip()
            break
    
    return city_cleaned

def extract_from_meta_tags(driver):
    """Extraire les informations fiables des méta-tags"""
    meta_info = {}
    
    try:
        # Titre principal
        title = driver.title
        if title and '|' in title:
            parts = title.split('|')
            if len(parts) == 2:
                name_part = parts[0].strip()
                location_part = parts[1].strip()
                
                if 'Maître' in name_part:
                    name = name_part.replace('Maître', '').strip()
                    meta_info['name_from_title'] = name
                
                if 'Avocat' in location_part:
                    city = location_part.replace('Avocat', '').strip()
                    city = clean_city_name(city)
                    meta_info['city'] = city
        
        # Description
        try:
            description_meta = driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
            description = description_meta.get_attribute('content')
            if description:
                meta_info['description'] = description
        except NoSuchElementException:
            pass
    
    except Exception as e:
        print(f"    ⚠️ Erreur méta-tags: {e}")
    
    return meta_info

def extract_lawyer_data_clean(driver, lawyer_url):
    """Extraction propre et fiable des données d'avocat"""
    lawyer_info = {
        'nom_complet': '',
        'prenom': '',
        'nom': '',
        'annee_inscription': '',
        'specialisations': '',  # Sera laissé vide car données non fiables
        'structure': '',
        'adresse': '',
        'telephone': '',
        'email': '',
        'ville': '',
        'source': lawyer_url
    }
    
    try:
        driver.get(lawyer_url)
        time.sleep(random.uniform(1.5, 2.5))
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 1. Extraction depuis méta-tags (le plus fiable)
        meta_info = extract_from_meta_tags(driver)
        
        # 2. Nom depuis URL (fallback)
        url_name_match = re.search(r'/maitre-([^-]+(?:-[^-]+)*)-\d+\.htm', lawyer_url)
        if url_name_match:
            url_name = url_name_match.group(1)
            formatted_name = ' '.join(word.capitalize() for word in url_name.split('-'))
            lawyer_info['nom_complet'] = formatted_name
        
        # 3. Priorité au nom depuis méta-tags
        if meta_info.get('name_from_title'):
            lawyer_info['nom_complet'] = meta_info['name_from_title']
        
        # Séparer prénom/nom
        if lawyer_info['nom_complet']:
            prenom, nom = separate_name(lawyer_info['nom_complet'])
            lawyer_info['prenom'] = prenom
            lawyer_info['nom'] = nom
        
        # 4. Ville depuis méta-tags
        if meta_info.get('city'):
            clean_city = clean_city_name(meta_info['city'])
            lawyer_info['ville'] = clean_city
            lawyer_info['adresse'] = clean_city
        
        # 5. SPÉCIALISATIONS: Laissées volontairement VIDES
        # Car les données détectées sont génériques et trompeuses
        lawyer_info['specialisations'] = ""
        
        # 6. Extraction basique email/téléphone (optionnel)
        page_source = driver.page_source
        
        # Email (si disponible)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_source)
        for email in emails:
            if not any(generic in email.lower() for generic in ['azko.fr', 'analytics', 'tracking']):
                lawyer_info['email'] = email
                break
        
        # Téléphone (plus permissif)
        phone_patterns = [r'(?:\+33|0)[1-9](?:[.\-\s]?\d{2}){4}']
        for pattern in phone_patterns:
            phones = re.findall(pattern, page_source)
            for phone in phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                # Accepter plus de numéros, juste exclure le principal du barreau
                if clean_phone != '0321562557' and len(clean_phone) == 10:
                    lawyer_info['telephone'] = phone
                    break
            if lawyer_info['telephone']:
                break
        
        # 7. Année d'inscription
        page_text = driver.find_element(By.TAG_NAME, "body").text
        year_patterns = [
            r'inscrit[e]?\s+(?:depuis\s+|en\s+)?(19\d{2}|20\d{2})',
            r'serment\s*:?\s*(19\d{2}|20\d{2})',
            r'barreau.*?(19\d{2}|20\d{2})',
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, page_text + ' ' + page_source, re.IGNORECASE)
            for year in matches:
                year_int = int(year)
                if 1950 <= year_int <= datetime.now().year:
                    lawyer_info['annee_inscription'] = year
                    break
            if lawyer_info['annee_inscription']:
                break
        
        return lawyer_info
        
    except Exception as e:
        print(f"    ❌ Erreur: {e}")
        return lawyer_info

def save_backup(lawyers_data, count):
    """Sauvegarder backup périodique"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"BETHUNE_BACKUP_{count}avocats_{timestamp}.json"
    
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Backup: {backup_filename}")

def run_final_clean_scraper():
    """Scraper final propre pour tous les avocats"""
    print("🚀 SCRAPER FINAL PROPRE - BARREAU DE BÉTHUNE")
    print("=" * 55)
    print(f"🎯 {len(LAWYER_URLS)} avocats à traiter")
    print("📋 Spécialisations: VOLONTAIREMENT VIDES (données non fiables)")
    print("✅ Focus: Noms, Villes, Années, Contacts")
    
    driver = setup_driver()
    if not driver:
        return []
    
    lawyers_data = []
    
    try:
        for i, url in enumerate(LAWYER_URLS, 1):
            print(f"\n📋 {i}/{len(LAWYER_URLS)}: {url.split('/')[-1]}")
            
            lawyer_info = extract_lawyer_data_clean(driver, url)
            
            if lawyer_info.get('nom_complet'):
                lawyers_data.append(lawyer_info)
                print(f"✅ {lawyer_info['nom_complet']}")
                
                # Détails trouvés
                details = []
                if lawyer_info.get('ville'):
                    details.append(f"🏙️ {lawyer_info['ville']}")
                if lawyer_info.get('telephone'):
                    details.append(f"📱 {lawyer_info['telephone']}")
                if lawyer_info.get('email'):
                    details.append(f"📧 {lawyer_info['email']}")
                if lawyer_info.get('annee_inscription'):
                    details.append(f"📅 {lawyer_info['annee_inscription']}")
                
                if details:
                    print(f"   {' | '.join(details)}")
            else:
                print("❌ Échec")
            
            # Backup tous les 25
            if i > 0 and i % 25 == 0:
                save_backup(lawyers_data, len(lawyers_data))
            
            time.sleep(random.uniform(0.8, 1.5))
    
    finally:
        driver.quit()
    
    return lawyers_data

def save_final_clean_results(lawyers_data):
    """Sauvegarder les résultats finaux propres"""
    if not lawyers_data:
        print("❌ Aucune donnée à sauvegarder")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"BETHUNE_FINAL_PROPRE_{len(lawyers_data)}_avocats_{timestamp}"
    
    # CSV
    csv_filename = f"{base_filename}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if lawyers_data:
            fieldnames = lawyers_data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers_data)
    
    # JSON
    json_filename = f"{base_filename}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers_data, jsonfile, ensure_ascii=False, indent=2)
    
    # Emails uniques
    emails_filename = f"{base_filename}_EMAILS.txt"
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        unique_emails = set()
        for lawyer in lawyers_data:
            if lawyer.get('email'):
                unique_emails.add(lawyer['email'])
        for email in sorted(unique_emails):
            emailfile.write(f"{email}\n")
    
    # Rapport final
    rapport_filename = f"{base_filename}_RAPPORT.txt"
    with open(rapport_filename, 'w', encoding='utf-8') as rapportfile:
        rapportfile.write(f"RAPPORT FINAL PROPRE - BARREAU DE BÉTHUNE\n")
        rapportfile.write(f"=" * 60 + "\n\n")
        rapportfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        rapportfile.write(f"Avocats extraits: {len(lawyers_data)}\n\n")
        
        # Statistiques
        with_email = sum(1 for l in lawyers_data if l.get('email'))
        with_phone = sum(1 for l in lawyers_data if l.get('telephone'))
        with_year = sum(1 for l in lawyers_data if l.get('annee_inscription'))
        with_city = sum(1 for l in lawyers_data if l.get('ville'))
        
        rapportfile.write(f"STATISTIQUES:\n")
        rapportfile.write(f"- Villes: {with_city}/{len(lawyers_data)} ({with_city/len(lawyers_data)*100:.1f}%)\n")
        rapportfile.write(f"- Emails: {with_email}/{len(lawyers_data)} ({with_email/len(lawyers_data)*100:.1f}%)\n")
        rapportfile.write(f"- Téléphones: {with_phone}/{len(lawyers_data)} ({with_phone/len(lawyers_data)*100:.1f}%)\n")
        rapportfile.write(f"- Années: {with_year}/{len(lawyers_data)} ({with_year/len(lawyers_data)*100:.1f}%)\n")
        rapportfile.write(f"- Spécialisations: 0/{len(lawyers_data)} (0% - volontairement vides)\n\n")
        
        # Analyse des villes
        cities = [l.get('ville', '') for l in lawyers_data if l.get('ville')]
        if cities:
            unique_cities = list(set(cities))
            rapportfile.write(f"RÉPARTITION GÉOGRAPHIQUE ({len(unique_cities)} villes):\n")
            for city in sorted(unique_cities):
                count = cities.count(city)
                rapportfile.write(f"- {city}: {count} avocat(s)\n")
        
        rapportfile.write(f"\nNOTE: Les spécialisations ont été volontairement laissées vides\n")
        rapportfile.write(f"car les données détectées étaient génériques et non spécifiques\n")
        rapportfile.write(f"à chaque avocat (répétition de contenu commun du site).\n")
    
    print(f"\n📁 RÉSULTATS FINAUX PROPRES:")
    print(f"   📊 CSV: {csv_filename}")
    print(f"   📋 JSON: {json_filename}")
    print(f"   📧 Emails: {emails_filename}")
    print(f"   📄 Rapport: {rapport_filename}")
    
    # Stats finales
    with_city = sum(1 for l in lawyers_data if l.get('ville'))
    with_phone = sum(1 for l in lawyers_data if l.get('telephone'))
    with_email = sum(1 for l in lawyers_data if l.get('email'))
    
    print(f"\n🎯 STATISTIQUES FINALES:")
    print(f"   🏙️ Villes: {with_city}/{len(lawyers_data)} ({with_city/len(lawyers_data)*100:.0f}%)")
    print(f"   📱 Téléphones: {with_phone}/{len(lawyers_data)} ({with_phone/len(lawyers_data)*100:.0f}%)")
    print(f"   📧 Emails: {with_email}/{len(lawyers_data)} ({with_email/len(lawyers_data)*100:.0f}%)")

if __name__ == "__main__":
    print("🎬 DÉMARRAGE DU SCRAPER FINAL PROPRE")
    
    lawyers_data = run_final_clean_scraper()
    
    if lawyers_data:
        print(f"\n🏁 EXTRACTION TERMINÉE - {len(lawyers_data)} avocats")
        save_final_clean_results(lawyers_data)
        print(f"\n🎉 SCRAPER TERMINÉ AVEC SUCCÈS !")
        print(f"    Données propres et fiables extraites")
        print(f"    Spécialisations volontairement omises pour éviter les erreurs")
    else:
        print("❌ Aucune donnée extraite")