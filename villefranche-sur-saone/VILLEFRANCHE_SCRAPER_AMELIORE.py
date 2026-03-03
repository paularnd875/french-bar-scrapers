#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER AMÉLIORÉ - BARREAU VILLEFRANCHE-SUR-SAÔNE
Version corrigée sans doublons
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

def setup_driver(headless=True):
    """Configuration du driver Chrome"""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def parse_lawyer_name(full_name):
    """Sépare prénom et nom en gérant les noms composés"""
    if not full_name:
        return "", ""
    
    # Nettoie le nom
    name = re.sub(r'\s+', ' ', full_name.strip())
    
    # Patterns pour les titres
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
        # Pour les noms composés, prend le premier mot comme prénom
        # et le reste comme nom de famille
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
    
    # Trouver le nom (première ligne avec prénom + nom)
    for line in lines:
        line_clean = line.strip()
        if (line_clean and 
            not any(skip in line_clean.lower() for skip in ['date', 'tel', 'email', '@', 'activité', 'domaine', 'rue', 'avenue', 'boulevard']) and
            len(line_clean.split()) >= 2 and
            any(c.isalpha() for c in line_clean) and
            not line_clean.isdigit()):
            
            # Vérifier que ce n'est pas juste une adresse
            if not re.match(r'^\d+\s+[A-Z]', line_clean):
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
    
    # Téléphone
    phone_pattern = r'0[1-9](?:[0-9]{8})'
    phone_matches = re.findall(phone_pattern, full_text)
    if phone_matches:
        lawyer_data['telephone'] = phone_matches[0]
    
    # Traitement ligne par ligne pour les autres infos
    for line in lines:
        line_lower = line.lower()
        
        # Spécialisations/Activités dominantes
        if 'activités dominantes' in line_lower or 'spécialit' in line_lower:
            lawyer_data['specialisations'] = line.replace('Activités dominantes :', '').strip()
        
        # Adresse
        elif any(keyword in line_lower for keyword in ['rue', 'avenue', 'boulevard', 'place', 'chemin', 'allée']) and not '@' in line:
            # Prendre la ligne la plus complète pour l'adresse
            if len(line) > len(lawyer_data['adresse']):
                lawyer_data['adresse'] = line
        
        # Année d'inscription
        elif 'inscription' in line_lower or 'serment' in line_lower:
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match:
                lawyer_data['annee_inscription'] = year_match.group()
    
    return lawyer_data

def extract_lawyers_data_improved(driver):
    """Version améliorée de l'extraction sans doublons"""
    lawyers = []
    
    try:
        # Attendre que les résultats se chargent
        wait = WebDriverWait(driver, 15)
        time.sleep(3)
        
        # Sauvegarder la page pour debug
        page_source = driver.page_source
        with open(f'villefranche_debug_{datetime.now().strftime("%H%M%S")}.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        
        print("🔍 Recherche des blocs d'avocats...")
        
        # Méthode 1: Chercher les divs avec class="avocat-*"
        lawyer_divs = driver.find_elements(By.CSS_SELECTOR, 'div[class*="avocat"]')
        print(f"📋 Trouvé {len(lawyer_divs)} éléments 'avocat'")
        
        # Filtrer et traiter uniquement les vrais blocs d'avocats
        processed_names = set()
        
        for div in lawyer_divs:
            try:
                text_content = div.text.strip()
                
                # Ignorer les blocs vides ou trop courts
                if len(text_content) < 20:
                    continue
                
                # Ignorer les blocs qui ne contiennent que des infos partielles
                if (text_content.startswith('Date de prestation') or 
                    '@' not in text_content or
                    not any(c.isalpha() for c in text_content)):
                    continue
                
                # Extraire les infos
                lawyer_info = extract_lawyer_info(text_content)
                
                # Vérifier qu'on a au moins un nom et un email
                if (lawyer_info['nom_complet'] and 
                    lawyer_info['email'] and 
                    lawyer_info['nom_complet'] not in processed_names):
                    
                    lawyer_info['source'] = driver.current_url
                    lawyers.append(lawyer_info)
                    processed_names.add(lawyer_info['nom_complet'])
                    
                    print(f"✅ Avocat {len(lawyers)}: {lawyer_info['nom_complet']} ({lawyer_info['email']})")
                    
                    # Limite pour le test
                    if len(lawyers) >= 20:
                        print(f"🛑 Limite de test atteinte ({len(lawyers)} avocats)")
                        break
                        
            except Exception as e:
                continue
        
        print(f"📊 Total extrait: {len(lawyers)} avocats uniques")
        
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
    
    return lawyers

def scrape_villefranche_ameliore(mode="test", headless=True):
    """Fonction principale améliorée"""
    print("🚀 DÉMARRAGE DU SCRAPER AMÉLIORÉ - VILLEFRANCHE-SUR-SAÔNE")
    print("=" * 60)
    
    driver = setup_driver(headless=headless)
    lawyers_data = []
    
    try:
        # Accès à la page
        print("📍 Accès à la page d'annuaire...")
        driver.get("https://www.avocatsvillefranche.fr/annuaire/")
        time.sleep(3)
        
        print(f"📄 Page chargée: {driver.title}")
        
        # Recherche et soumission du formulaire
        try:
            # Attendre que le formulaire soit chargé
            wait = WebDriverWait(driver, 10)
            form = wait.until(EC.presence_of_element_located((By.ID, "form--avocat")))
            print("✅ Formulaire trouvé")
            
            # Scroll vers le formulaire
            driver.execute_script("arguments[0].scrollIntoView(true);", form)
            time.sleep(2)
            
            # Chercher le bouton submit
            submit_button = wait.until(EC.element_to_be_clickable((By.NAME, "zabe_barotech_submit")))
            
            # Essayer plusieurs méthodes de clic
            try:
                print("🔍 Soumission du formulaire (méthode 1)...")
                submit_button.click()
            except:
                try:
                    print("🔍 Soumission du formulaire (méthode 2 - JS)...")
                    driver.execute_script("arguments[0].click();", submit_button)
                except:
                    print("🔍 Soumission du formulaire (méthode 3 - submit)...")
                    form.submit()
            
            time.sleep(5)
            print("⏳ Chargement des résultats terminé")
            
        except Exception as e:
            print(f"⚠️ Problème avec le formulaire: {e}")
            print("🔍 Tentative d'extraction directe...")
        
        # Extraction améliorée
        print("📊 Extraction des données...")
        lawyers_data = extract_lawyers_data_improved(driver)
        
        print(f"✅ Extraction terminée: {len(lawyers_data)} avocats")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        driver.quit()
    
    # Sauvegarde
    if lawyers_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"VILLEFRANCHE_AMELIORE_{len(lawyers_data)}_avocats_{timestamp}"
        
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
        
        # Emails
        email_file = f"VILLEFRANCHE_AMELIORE_EMAILS_{timestamp}.txt"
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write(f"EMAILS EXTRAITS - VILLEFRANCHE AMÉLIORÉ\n")
            f.write("=" * 50 + "\n\n")
            for lawyer in lawyers_data:
                if lawyer['email']:
                    f.write(f"{lawyer['email']}\n")
        
        # Rapport
        report_file = f"VILLEFRANCHE_AMELIORE_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT AMÉLIORÉ - BARREAU VILLEFRANCHE-SUR-SAÔNE\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"🌐 URL: https://www.avocatsvillefranche.fr/annuaire/\n")
            f.write(f"📊 Mode: {mode} (headless: {headless})\n")
            f.write(f"👥 Avocats extraits: {len(lawyers_data)}\n\n")
            
            emails_count = len([l for l in lawyers_data if l['email']])
            phones_count = len([l for l in lawyers_data if l['telephone']])
            specializations_count = len([l for l in lawyers_data if l['specialisations']])
            
            f.write("📊 STATISTIQUES:\n")
            f.write(f"  📧 Avec email: {emails_count}/{len(lawyers_data)}\n")
            f.write(f"  📞 Avec téléphone: {phones_count}/{len(lawyers_data)}\n") 
            f.write(f"  🎯 Avec spécialisations: {specializations_count}/{len(lawyers_data)}\n\n")
            
            f.write("📋 LISTE DES AVOCATS:\n")
            f.write("-" * 40 + "\n")
            for i, lawyer in enumerate(lawyers_data, 1):
                f.write(f"\n{i}. {lawyer['nom_complet']}\n")
                f.write(f"   📧 {lawyer['email']}\n")
                f.write(f"   📞 {lawyer['telephone']}\n")
                if lawyer['specialisations']:
                    f.write(f"   🎯 {lawyer['specialisations']}\n")
                if lawyer['annee_inscription']:
                    f.write(f"   📅 Inscription: {lawyer['annee_inscription']}\n")
        
        print(f"\n📁 FICHIERS GÉNÉRÉS:")
        print(f"  📊 CSV: {csv_file}")
        print(f"  🔧 JSON: {json_file}")
        print(f"  📧 Emails: {email_file}")
        print(f"  📋 Rapport: {report_file}")
        
        print(f"\n📊 RÉSULTATS:")
        print(f"  👥 Total: {len(lawyers_data)} avocats")
        print(f"  📧 Emails: {emails_count}")
        print(f"  📞 Téléphones: {phones_count}")
        print(f"  🎯 Spécialisations: {specializations_count}")
        
    return lawyers_data

if __name__ == "__main__":
    # Test en mode headless
    scrape_villefranche_ameliore(mode="test", headless=True)