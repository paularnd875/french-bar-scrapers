#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DE PRODUCTION - BARREAU VILLEFRANCHE-SUR-SAÔNE
Extraction complète de tous les avocats
"""

import time
import json
import csv
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

def setup_driver(headless=True):
    """Configuration du driver Chrome optimisée"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    
    # Options d'optimisation
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-images')
    options.add_argument('--disable-javascript-harmony-shipping')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    # Options anti-détection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def parse_lawyer_name(full_name):
    """Sépare prénom et nom en gérant les noms composés"""
    if not full_name:
        return "", ""
    
    name = re.sub(r'\s+', ' ', full_name.strip())
    titles = r'^(M\.|Mme|Maître|Me\.?\s+|Avocat\s+)'
    name = re.sub(titles, '', name, flags=re.IGNORECASE).strip()
    
    parts = name.split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return "", parts[0]
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        return parts[0], ' '.join(parts[1:])

def extract_lawyer_info(text_block):
    """Extrait les informations d'un bloc de texte d'avocat"""
    lines = [line.strip() for line in text_block.split('\n') if line.strip()]
    
    lawyer_data = {
        'prenom': '',
        'nom': '',
        'nom_complet': '',
        'structure': '',
        'specialisations': '',
        'telephone': '',
        'email': '',
        'adresse': '',
        'annee_inscription': ''
    }
    
    # Trouver le nom (première ligne valide)
    for line in lines:
        line_clean = line.strip()
        if (line_clean and 
            not any(skip in line_clean.lower() for skip in ['date', 'tel', 'email', '@', 'activité', 'domaine', 'rue', 'avenue', 'boulevard']) and
            len(line_clean.split()) >= 2 and
            any(c.isalpha() for c in line_clean) and
            not line_clean.isdigit() and
            not re.match(r'^\d+\s+[A-Z]', line_clean)):
            
            lawyer_data['nom_complet'] = line_clean
            prenom, nom = parse_lawyer_name(line_clean)
            lawyer_data['prenom'] = prenom
            lawyer_data['nom'] = nom
            break
    
    # Extraction des autres informations
    full_text = text_block
    
    # Email
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_matches = re.findall(email_pattern, full_text)
    if email_matches:
        lawyer_data['email'] = email_matches[0]
    
    # Téléphone (format français)
    phone_pattern = r'0[1-9](?:[0-9]{8})'
    phone_matches = re.findall(phone_pattern, full_text)
    if phone_matches:
        lawyer_data['telephone'] = phone_matches[0]
    
    # Traitement ligne par ligne
    for line in lines:
        line_lower = line.lower()
        
        # Spécialisations
        if 'activités dominantes' in line_lower or 'spécialit' in line_lower:
            lawyer_data['specialisations'] = line.replace('Activités dominantes :', '').strip()
        
        # Adresse - prendre la plus complète
        elif any(keyword in line_lower for keyword in ['rue', 'avenue', 'boulevard', 'place', 'chemin', 'allée']) and not '@' in line:
            if len(line) > len(lawyer_data['adresse']):
                lawyer_data['adresse'] = line
        
        # Structure/Cabinet
        elif any(keyword in line_lower for keyword in ['cabinet', 'scp', 'selarl', 'société']) and '@' not in line:
            lawyer_data['structure'] = line
        
        # Année d'inscription
        elif 'inscription' in line_lower or 'serment' in line_lower:
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match:
                lawyer_data['annee_inscription'] = year_match.group()
    
    return lawyer_data

def extract_all_lawyers_production(driver):
    """Extraction complète de tous les avocats"""
    lawyers = []
    processed_names = set()
    backup_counter = 0
    
    try:
        print("🔍 Recherche des blocs d'avocats...")
        time.sleep(3)
        
        # Trouver tous les éléments avocat
        lawyer_divs = driver.find_elements(By.CSS_SELECTOR, 'div[class*="avocat"]')
        total_elements = len(lawyer_divs)
        print(f"📋 Trouvé {total_elements} éléments potentiels")
        
        if total_elements == 0:
            print("⚠️ Aucun élément trouvé, sauvegarde de la page pour debug")
            with open(f'villefranche_debug_production_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            return lawyers
        
        for i, div in enumerate(lawyer_divs):
            try:
                text_content = div.text.strip()
                
                # Filtrage basique
                if (len(text_content) < 20 or 
                    text_content.startswith('Date de prestation') or 
                    '@' not in text_content):
                    continue
                
                # Extraction des infos
                lawyer_info = extract_lawyer_info(text_content)
                
                # Validation et ajout
                if (lawyer_info['nom_complet'] and 
                    lawyer_info['email'] and 
                    lawyer_info['nom_complet'] not in processed_names):
                    
                    lawyer_info['source'] = driver.current_url
                    lawyers.append(lawyer_info)
                    processed_names.add(lawyer_info['nom_complet'])
                    
                    print(f"✅ Avocat {len(lawyers)}: {lawyer_info['nom_complet']}")
                    
                    # Sauvegarde intermédiaire tous les 25 avocats
                    if len(lawyers) % 25 == 0:
                        backup_counter += 1
                        backup_file = f"VILLEFRANCHE_BACKUP_{len(lawyers)}avocats_{datetime.now().strftime('%H%M%S')}.json"
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            json.dump(lawyers, f, indent=2, ensure_ascii=False)
                        print(f"💾 Sauvegarde intermédiaire: {backup_file}")
                
                # Affichage du progrès
                if (i + 1) % 50 == 0:
                    print(f"🔄 Progression: {i + 1}/{total_elements} éléments traités, {len(lawyers)} avocats extraits")
                    
            except Exception as e:
                continue
        
        print(f"📊 Extraction terminée: {len(lawyers)} avocats uniques sur {total_elements} éléments")
        
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
    
    return lawyers

def save_production_results(lawyers_data, mode="production"):
    """Sauvegarde les résultats avec horodatage"""
    if not lawyers_data:
        print("❌ Aucune donnée à sauvegarder")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"VILLEFRANCHE_{mode.upper()}_{len(lawyers_data)}_avocats_{timestamp}"
    
    # CSV
    csv_file = f"{base_name}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=lawyers_data[0].keys())
        writer.writeheader()
        writer.writerows(lawyers_data)
    
    # JSON
    json_file = f"{base_name}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(lawyers_data, f, indent=2, ensure_ascii=False)
    
    # Emails uniquement
    email_file = f"VILLEFRANCHE_{mode.upper()}_EMAILS_SEULEMENT_{timestamp}.txt"
    emails = [lawyer['email'] for lawyer in lawyers_data if lawyer['email']]
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(f"EMAILS EXTRAITS - VILLEFRANCHE {mode.upper()}\n")
        f.write(f"Total: {len(emails)} emails uniques\n")
        f.write("=" * 50 + "\n\n")
        for email in sorted(set(emails)):
            f.write(f"{email}\n")
    
    # Rapport détaillé
    report_file = f"VILLEFRANCHE_{mode.upper()}_RAPPORT_COMPLET_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"RAPPORT COMPLET - BARREAU VILLEFRANCHE-SUR-SAÔNE\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"📅 Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"🌐 URL source: https://www.avocatsvillefranche.fr/annuaire/\n")
        f.write(f"🔧 Mode: {mode}\n")
        f.write(f"👥 Total avocats: {len(lawyers_data)}\n\n")
        
        # Statistiques détaillées
        emails_count = len([l for l in lawyers_data if l['email']])
        phones_count = len([l for l in lawyers_data if l['telephone']])
        specializations_count = len([l for l in lawyers_data if l['specialisations']])
        years_count = len([l for l in lawyers_data if l['annee_inscription']])
        addresses_count = len([l for l in lawyers_data if l['adresse']])
        
        f.write("📊 STATISTIQUES DÉTAILLÉES:\n")
        f.write("-" * 30 + "\n")
        f.write(f"📧 Avec email: {emails_count}/{len(lawyers_data)} ({emails_count/len(lawyers_data)*100:.1f}%)\n")
        f.write(f"📞 Avec téléphone: {phones_count}/{len(lawyers_data)} ({phones_count/len(lawyers_data)*100:.1f}%)\n")
        f.write(f"🎯 Avec spécialisations: {specializations_count}/{len(lawyers_data)} ({specializations_count/len(lawyers_data)*100:.1f}%)\n")
        f.write(f"📅 Avec année inscription: {years_count}/{len(lawyers_data)} ({years_count/len(lawyers_data)*100:.1f}%)\n")
        f.write(f"📍 Avec adresse: {addresses_count}/{len(lawyers_data)} ({addresses_count/len(lawyers_data)*100:.1f}%)\n\n")
        
        # Analyse des spécialisations
        specializations = [l['specialisations'] for l in lawyers_data if l['specialisations']]
        if specializations:
            f.write("🎯 SPÉCIALISATIONS LES PLUS COURANTES:\n")
            f.write("-" * 40 + "\n")
            from collections import Counter
            spec_counter = Counter()
            for spec in specializations:
                if 'droit' in spec.lower():
                    spec_clean = spec.replace('Activités dominantes :', '').strip()
                    spec_counter[spec_clean] += 1
            
            for spec, count in spec_counter.most_common(10):
                f.write(f"  - {spec}: {count} avocat(s)\n")
            f.write("\n")
        
        # Liste détaillée des avocats
        f.write("📋 LISTE COMPLÈTE DES AVOCATS:\n")
        f.write("-" * 50 + "\n")
        for i, lawyer in enumerate(lawyers_data, 1):
            f.write(f"\n{i:3d}. {lawyer['nom_complet']}\n")
            f.write(f"      📧 {lawyer['email']}\n")
            if lawyer['telephone']:
                f.write(f"      📞 {lawyer['telephone']}\n")
            if lawyer['specialisations']:
                f.write(f"      🎯 {lawyer['specialisations']}\n")
            if lawyer['annee_inscription']:
                f.write(f"      📅 Inscription: {lawyer['annee_inscription']}\n")
            if lawyer['adresse']:
                f.write(f"      📍 {lawyer['adresse']}\n")
    
    print(f"\n📁 FICHIERS DE PRODUCTION GÉNÉRÉS:")
    print(f"  📊 CSV: {csv_file}")
    print(f"  🔧 JSON: {json_file}")
    print(f"  📧 Emails: {email_file}")
    print(f"  📋 Rapport: {report_file}")
    
    return csv_file, json_file, email_file, report_file

def scrape_villefranche_production():
    """Fonction principale de production"""
    print("🚀 DÉMARRAGE DU SCRAPER DE PRODUCTION - VILLEFRANCHE-SUR-SAÔNE")
    print("=" * 70)
    print("⚠️  EXTRACTION COMPLÈTE DE TOUS LES AVOCATS")
    print("=" * 70)
    
    start_time = time.time()
    driver = setup_driver(headless=True)
    lawyers_data = []
    
    try:
        # Accès à la page
        print("📍 Accès à la page d'annuaire...")
        driver.get("https://www.avocatsvillefranche.fr/annuaire/")
        time.sleep(3)
        
        print(f"📄 Page chargée: {driver.title}")
        
        # Soumission du formulaire pour afficher tous les avocats
        try:
            wait = WebDriverWait(driver, 10)
            form = wait.until(EC.presence_of_element_located((By.ID, "form--avocat")))
            print("✅ Formulaire trouvé")
            
            driver.execute_script("arguments[0].scrollIntoView(true);", form)
            time.sleep(2)
            
            submit_button = wait.until(EC.element_to_be_clickable((By.NAME, "zabe_barotech_submit")))
            
            try:
                print("🔍 Soumission du formulaire...")
                submit_button.click()
            except:
                driver.execute_script("arguments[0].click();", submit_button)
            
            time.sleep(5)
            print("⏳ Formulaire soumis, chargement des résultats...")
            
        except Exception as e:
            print(f"⚠️ Problème formulaire: {e}")
        
        # Extraction complète
        print("📊 DÉMARRAGE DE L'EXTRACTION COMPLÈTE...")
        lawyers_data = extract_all_lawyers_production(driver)
        
        execution_time = time.time() - start_time
        print(f"✅ Extraction terminée en {execution_time:.1f}s: {len(lawyers_data)} avocats")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        # Sauvegarde de la page pour debug
        try:
            with open(f'villefranche_error_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
        except:
            pass
    
    finally:
        driver.quit()
    
    # Sauvegarde des résultats
    if lawyers_data:
        save_production_results(lawyers_data, "production")
        
        # Statistiques finales
        print(f"\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 50)
        print(f"👥 Total avocats extraits: {len(lawyers_data)}")
        print(f"📧 Emails collectés: {len([l for l in lawyers_data if l['email']])}")
        print(f"📞 Téléphones: {len([l for l in lawyers_data if l['telephone']])}")
        print(f"🎯 Spécialisations: {len([l for l in lawyers_data if l['specialisations']])}")
        print(f"⏱️  Temps d'exécution: {time.time() - start_time:.1f} secondes")
        print("=" * 50)
        
    else:
        print("❌ ÉCHEC DE L'EXTRACTION - Aucune donnée collectée")
    
    return lawyers_data

if __name__ == "__main__":
    # Vérification des arguments
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 MODE TEST - Limitation à 20 avocats")
        # Modification temporaire pour le test
        original_extract = extract_all_lawyers_production
        def test_extract(driver):
            lawyers = original_extract(driver)
            return lawyers[:20] if len(lawyers) > 20 else lawyers
        extract_all_lawyers_production = test_extract
    
    scrape_villefranche_production()