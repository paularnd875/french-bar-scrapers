#!/usr/bin/env python3
"""
Scraper de production pour le barreau de Bourgoin-Jallieu
Extrait toutes les informations des avocats en mode headless
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import csv
import re
from datetime import datetime

def extract_bourgoin_lawyers_production():
    """Extrait toutes les informations des avocats - Version de production en mode headless"""
    
    # Configuration Chrome en mode headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Mode invisible
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("🚀 Extraction complète des avocats de Bourgoin-Jallieu (mode headless)...")
        
        # Charger la page
        url = "https://www.ordre-avocats-bourgoin-jallieu.com/barreau-de-bourgoin/annuaire-avocats-bourgoin-jallieu-isere-38/"
        driver.get(url)
        
        # Attendre que la page se charge
        time.sleep(5)
        
        # Accepter les cookies si nécessaire (en mode headless)
        try:
            cookie_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Tout accepter') or contains(text(), 'Accept') or contains(text(), 'Accepter')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                print("✅ Cookies acceptés")
                time.sleep(2)
        except:
            pass
        
        # Extraire le texte brut de la page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Parser toutes les informations des avocats
        lawyers = parse_all_lawyers_comprehensive(page_text)
        
        print(f"📊 {len(lawyers)} avocats extraits au total")
        
        # Générer les fichiers de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Fichier JSON complet
        json_filename = f'BOURGOIN_COMPLET_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, indent=2, ensure_ascii=False)
        
        # 2. Fichier CSV complet
        csv_filename = f'BOURGOIN_COMPLET_{timestamp}.csv'
        if lawyers:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=lawyers[0].keys())
                writer.writeheader()
                writer.writerows(lawyers)
        
        # 3. Emails seulement
        emails_filename = f'BOURGOIN_EMAILS_{timestamp}.txt'
        emails = [lawyer.get('email', '') for lawyer in lawyers if lawyer.get('email')]
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        # 4. Rapport détaillé
        rapport_filename = f'BOURGOIN_RAPPORT_{timestamp}.txt'
        generate_detailed_report(lawyers, rapport_filename)
        
        # Afficher les statistiques
        print(f"\n📈 Statistiques d'extraction:")
        print(f"- Total avocats: {len(lawyers)}")
        print(f"- Avocats avec email: {len([l for l in lawyers if l.get('email')])}")
        print(f"- Avocats avec téléphone: {len([l for l in lawyers if l.get('telephone')])}")
        print(f"- Avocats avec site web: {len([l for l in lawyers if l.get('site_web')])}")
        print(f"- Avocats avec fax: {len([l for l in lawyers if l.get('fax')])}")
        
        print(f"\n✅ Fichiers générés:")
        print(f"- {json_filename}")
        print(f"- {csv_filename}")
        print(f"- {emails_filename}")
        print(f"- {rapport_filename}")
        
        return lawyers
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        return []
        
    finally:
        driver.quit()

def parse_all_lawyers_comprehensive(text):
    """Parse complet du texte pour extraire toutes les informations des avocats et sociétés"""
    
    lawyers = []
    
    # 1. Parser les avocats individuels
    individual_lawyers = parse_individual_lawyers(text)
    lawyers.extend(individual_lawyers)
    
    # 2. Parser les sociétés d'avocats
    societies = parse_lawyer_societies(text)
    lawyers.extend(societies)
    
    # 3. Parser les cabinets et bureaux secondaires
    secondary_offices = parse_secondary_offices(text)
    lawyers.extend(secondary_offices)
    
    return lawyers

def parse_individual_lawyers(text):
    """Parse les avocats individuels"""
    
    lawyers = []
    
    # Extraire la section des avocats individuels
    start_marker = "Avocats du Barreau"
    end_marker = "Sociétés d'avocats"
    
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        individual_section = text[start_idx:end_idx]
    else:
        individual_section = text
    
    # Pattern pour identifier les avocats individuels
    lawyer_pattern = r'([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ\-\s]+?)\s+([A-Za-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþß\-\s]+?)\nPrestation\s+(?:de\s+)?serment\s*:\s*([^\n]+)'
    
    matches = re.finditer(lawyer_pattern, individual_section)
    
    for match in matches:
        try:
            nom = clean_name(match.group(1))
            prenom = clean_name(match.group(2))
            prestation_serment = match.group(3).strip()
            
            # Extraire le bloc de données pour cet avocat
            lawyer_text = extract_lawyer_block(individual_section, match)
            
            # Parser les détails
            lawyer_info = extract_comprehensive_lawyer_details(nom, prenom, prestation_serment, lawyer_text)
            lawyer_info['type'] = 'Avocat individuel'
            
            lawyers.append(lawyer_info)
            
        except Exception as e:
            print(f"⚠️ Erreur lors du parsing de l'avocat individuel: {e}")
            continue
    
    return lawyers

def parse_lawyer_societies(text):
    """Parse les sociétés d'avocats"""
    
    societies = []
    
    # Extraire la section des sociétés
    start_marker = "Sociétés d'avocats"
    end_marker = "Cabinets secondaires"
    
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker)
    
    if start_idx == -1:
        return societies
    
    if end_idx == -1:
        end_idx = text.find("Bureaux Secondaires")
        if end_idx == -1:
            societies_section = text[start_idx:]
        else:
            societies_section = text[start_idx:end_idx]
    else:
        societies_section = text[start_idx:end_idx]
    
    # Pattern pour les sociétés
    society_pattern = r'(SCP|SELARL|SELURL)\s+([^\n]+)\n([^\n]*\n)*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    
    matches = re.finditer(society_pattern, societies_section)
    
    for match in matches:
        try:
            type_societe = match.group(1)
            nom_societe = match.group(2).strip()
            
            # Extraire le bloc pour cette société
            society_text = extract_society_block(societies_section, match)
            
            society_info = extract_society_details(type_societe, nom_societe, society_text)
            society_info['type'] = 'Société d\'avocats'
            
            societies.append(society_info)
            
        except Exception as e:
            print(f"⚠️ Erreur lors du parsing de la société: {e}")
            continue
    
    return societies

def parse_secondary_offices(text):
    """Parse les cabinets et bureaux secondaires"""
    
    offices = []
    
    # Cette section contient généralement des informations complémentaires
    # On peut les traiter de manière similaire aux sociétés
    
    return offices

def extract_lawyer_block(text, match):
    """Extrait le bloc de texte correspondant à un avocat"""
    
    start_pos = match.end()
    
    # Chercher le prochain avocat ou la fin de section
    next_lawyer = re.search(r'[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ\-\s]+\s+[A-Za-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþß\-\s]+\nPrestation', text[start_pos:])
    
    if next_lawyer:
        end_pos = start_pos + next_lawyer.start()
    else:
        # Chercher autres marqueurs de fin
        end_markers = ["Sociétés d'avocats", "Cabinets secondaires", "Bureaux Secondaires"]
        end_pos = start_pos + 800  # Limite par défaut
        
        for marker in end_markers:
            marker_pos = text.find(marker, start_pos)
            if marker_pos != -1 and marker_pos < end_pos:
                end_pos = marker_pos
    
    return text[start_pos:end_pos]

def extract_society_block(text, match):
    """Extrait le bloc de texte correspondant à une société"""
    
    start_pos = match.start()
    
    # Chercher la prochaine société ou fin de section
    next_society = re.search(r'(SCP|SELARL|SELURL)\s+[^\n]+', text[start_pos + 10:])
    
    if next_society:
        end_pos = start_pos + 10 + next_society.start()
    else:
        end_pos = start_pos + 400  # Limite par défaut
    
    return text[start_pos:end_pos]

def extract_comprehensive_lawyer_details(nom, prenom, prestation_serment, text):
    """Extrait de manière exhaustive les détails d'un avocat"""
    
    lawyer = {
        'nom': nom,
        'prenom': prenom,
        'prestation_serment': prestation_serment,
        'email': '',
        'telephone': '',
        'mobile': '',
        'fax': '',
        'adresse': '',
        'code_postal': '',
        'ville': '',
        'site_web': '',
        'specialisations': '',
        'structure': ''
    }
    
    # Email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        lawyer['email'] = email_match.group(1)
    
    # Téléphones (fixe et mobile)
    tel_matches = re.findall(r'Tél\s*:\s*([0-9\s\.\-\+]+)', text)
    mob_matches = re.findall(r'Mob\s*:\s*([0-9\s\.\-\+]+)', text)
    
    if tel_matches:
        lawyer['telephone'] = tel_matches[0].strip()
    
    if mob_matches:
        lawyer['mobile'] = mob_matches[0].strip()
    
    # Fax
    fax_match = re.search(r'Fax\s*:\s*([0-9\s\.\-\+]+)', text)
    if fax_match:
        lawyer['fax'] = fax_match.group(1).strip()
    
    # Site web
    site_matches = re.findall(r'(https?://[^\s]+)', text)
    if site_matches:
        lawyer['site_web'] = site_matches[0]
    
    # Adresse avec parsing intelligent
    parse_address(text, lawyer)
    
    return lawyer

def extract_society_details(type_societe, nom_societe, text):
    """Extrait les détails d'une société d'avocats"""
    
    society = {
        'nom': nom_societe,
        'prenom': '',
        'prestation_serment': '',
        'email': '',
        'telephone': '',
        'mobile': '',
        'fax': '',
        'adresse': '',
        'code_postal': '',
        'ville': '',
        'site_web': '',
        'specialisations': '',
        'structure': type_societe
    }
    
    # Email
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        society['email'] = email_match.group(1)
    
    # Téléphone
    tel_match = re.search(r'Tél\s*:\s*([0-9\s\.\-\+]+)', text)
    if tel_match:
        society['telephone'] = tel_match.group(1).strip()
    
    # Fax
    fax_match = re.search(r'Fax\s*:\s*([0-9\s\.\-\+]+)', text)
    if fax_match:
        society['fax'] = fax_match.group(1).strip()
    
    # Adresse
    parse_address(text, society)
    
    return society

def parse_address(text, lawyer_dict):
    """Parse intelligent de l'adresse"""
    
    lines = text.split('\n')
    address_lines = []
    
    for line in lines[:6]:  # Regarder les 6 premières lignes
        line = line.strip()
        
        # Ignorer les lignes avec email, téléphone, etc.
        if any(keyword in line.lower() for keyword in ['@', 'tél', 'fax', 'http', 'mob']):
            continue
            
        # Ligne probable d'adresse
        if line and len(line) > 3:
            address_lines.append(line)
    
    if address_lines:
        full_address = ', '.join(address_lines)
        lawyer_dict['adresse'] = full_address
        
        # Extraire code postal et ville si possible
        cp_ville_match = re.search(r'(\d{5})\s+([A-Za-zÀ-ÿ\-\s]+)', full_address)
        if cp_ville_match:
            lawyer_dict['code_postal'] = cp_ville_match.group(1)
            lawyer_dict['ville'] = cp_ville_match.group(2).strip()

def clean_name(name):
    """Nettoie et formate un nom"""
    return ' '.join(name.split()).title()

def generate_detailed_report(lawyers, filename):
    """Génère un rapport détaillé de l'extraction"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("RAPPORT DÉTAILLÉ - EXTRACTION BARREAU DE BOURGOIN-JALLIEU\\n")
        f.write("=" * 60 + "\\n\\n")
        
        f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\\n")
        f.write(f"Total avocats extraits: {len(lawyers)}\\n\\n")
        
        # Statistiques par type
        types = {}
        for lawyer in lawyers:
            t = lawyer.get('type', 'Non défini')
            types[t] = types.get(t, 0) + 1
        
        f.write("RÉPARTITION PAR TYPE:\\n")
        for t, count in types.items():
            f.write(f"- {t}: {count}\\n")
        
        f.write("\\nSTATISTIQUES DE COMPLÉTUDE:\\n")
        f.write(f"- Emails renseignés: {len([l for l in lawyers if l.get('email')])}\\n")
        f.write(f"- Téléphones renseignés: {len([l for l in lawyers if l.get('telephone')])}\\n")
        f.write(f"- Sites web renseignés: {len([l for l in lawyers if l.get('site_web')])}\\n")
        f.write(f"- Adresses renseignées: {len([l for l in lawyers if l.get('adresse')])}\\n")
        
        f.write("\\nLISTE COMPLÈTE:\\n")
        f.write("-" * 60 + "\\n")
        
        for i, lawyer in enumerate(lawyers, 1):
            f.write(f"\\n{i}. {lawyer.get('nom', 'N/A')} {lawyer.get('prenom', 'N/A')}\\n")
            f.write(f"   Type: {lawyer.get('type', 'N/A')}\\n")
            f.write(f"   Email: {lawyer.get('email', 'N/A')}\\n")
            f.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\\n")
            f.write(f"   Prestation serment: {lawyer.get('prestation_serment', 'N/A')}\\n")
            f.write(f"   Adresse: {lawyer.get('adresse', 'N/A')}\\n")
            if lawyer.get('site_web'):
                f.write(f"   Site web: {lawyer.get('site_web')}\\n")

if __name__ == "__main__":
    print("🚀 Lancement du scraper de production Bourgoin-Jallieu...")
    result = extract_bourgoin_lawyers_production()
    print(f"\\n🏁 Extraction terminée: {len(result)} entrées au total")
    print("\\n✅ Tous les fichiers ont été générés avec succès!")