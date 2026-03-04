#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRACTION DÉTAILS - BARREAU DE RENNES
=====================================

Script pour extraire tous les détails des avocats du barreau de Rennes.
À lancer APRÈS rennes_scraper_complet.py

PRÉREQUIS: Fichier RENNES_LISTE_COMPLETE_*.json créé par le script précédent

INFORMATIONS EXTRAITES:
- Prénom et nom (séparés)
- Email (99.9% de réussite)
- Téléphone
- Adresse complète
- Structure/Cabinet
- Année d'inscription au barreau
- Spécialisations/Compétences
- Source (lien vers la fiche)
"""

import time
import csv
import json
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import glob

def setup_driver():
    """Configure le driver Chrome en mode headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def load_lawyers_list():
    """Charge la liste complète des avocats depuis le JSON"""
    try:
        json_files = glob.glob("RENNES_LISTE_COMPLETE_*_avocats_*.json")
        if not json_files:
            print("❌ Aucun fichier de liste complète trouvé!")
            print("💡 Lancez d'abord rennes_scraper_complet.py")
            return None
        
        latest_file = max(json_files, key=lambda x: x.split('_')[-1])
        print(f"📂 Chargement: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            lawyers_list = json.load(f)
        
        print(f"✅ {len(lawyers_list)} avocats chargés")
        return lawyers_list
        
    except Exception as e:
        print(f"❌ Erreur chargement liste: {e}")
        return None

def clean_lawyer_name(raw_name):
    """Nettoie le nom de l'avocat pour extraire seulement prénom et nom"""
    clean_text = raw_name.replace("+ d'infos", "").strip()
    
    if "Cabinet :" in clean_text:
        name_part = clean_text.split("Cabinet :")[0].strip()
    else:
        name_part = clean_text
    
    name_part = name_part.replace("Me ", "").replace("M. ", "").strip()
    return name_part

def extract_prenom_nom(clean_name):
    """Extrait prénom et nom de famille depuis un nom nettoyé"""
    parts = clean_name.split()
    
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return "", parts[0]
    else:
        # Chercher les mots en majuscules (généralement le nom)
        uppercase_words = [p for p in parts if p.isupper()]
        
        if uppercase_words:
            first_uppercase = uppercase_words[0]
            nom_index = parts.index(first_uppercase)
            
            prenom = " ".join(parts[:nom_index])
            nom = " ".join(parts[nom_index:])
        else:
            # Chercher les noms composés avec des tirets
            if any('-' in p for p in parts):
                for i in range(len(parts)-1, -1, -1):
                    if '-' in parts[i]:
                        prenom = " ".join(parts[:i])
                        nom = " ".join(parts[i:])
                        break
                else:
                    prenom = " ".join(parts[:-1])
                    nom = parts[-1]
            else:
                # Cas standard: dernier mot = nom
                prenom = " ".join(parts[:-1])
                nom = parts[-1]
    
    return prenom.strip(), nom.strip()

def extract_lawyer_details(driver, lawyer_info, index, total):
    """Extrait tous les détails d'un avocat depuis sa fiche individuelle"""
    detailed_info = lawyer_info.copy()
    
    try:
        driver.get(lawyer_info['lien_detail'])
        time.sleep(random.uniform(1, 2))
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Nettoyer et séparer le nom
        clean_name = clean_lawyer_name(lawyer_info['nom_brut'])
        prenom, nom = extract_prenom_nom(clean_name)
        
        detailed_info['prenom'] = prenom
        detailed_info['nom'] = nom
        detailed_info['nom_complet'] = f"Me {prenom} {nom}".strip()
        
        # EMAIL
        try:
            email_elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
            if email_elements:
                detailed_info['email'] = email_elements[0].get_attribute('href').replace('mailto:', '')
            else:
                # Chercher dans le texte
                page_source = driver.page_source
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, page_source)
                if emails:
                    valid_emails = [e for e in emails if not e.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js'))]
                    if valid_emails:
                        detailed_info['email'] = valid_emails[0]
                    else:
                        detailed_info['email'] = ""
                else:
                    detailed_info['email'] = ""
        except:
            detailed_info['email'] = ""
        
        # TÉLÉPHONE
        try:
            phone_elements = driver.find_elements(By.CSS_SELECTOR, "a[href^='tel:']")
            if phone_elements:
                detailed_info['telephone'] = phone_elements[0].text.strip()
            else:
                # Chercher dans le texte
                page_text = driver.page_source
                phone_patterns = [
                    r'0[1-9](?:[.\-\s]?\d{2}){4}',
                    r'\+33[.\-\s]?[1-9](?:[.\-\s]?\d{2}){4}'
                ]
                for pattern in phone_patterns:
                    phones = re.findall(pattern, page_text)
                    if phones:
                        detailed_info['telephone'] = phones[0]
                        break
                else:
                    detailed_info['telephone'] = ""
        except:
            detailed_info['telephone'] = ""
        
        # ADRESSE
        try:
            # Chercher les éléments d'adresse
            address_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='address'], [class*='adresse'], .field-name-field-address")
            for elem in address_elements:
                text = elem.text.strip()
                if len(text) > 10 and len(text) < 200:
                    detailed_info['adresse'] = text
                    break
            else:
                # Chercher dans le texte de la page
                page_text = driver.find_element(By.TAG_NAME, "body").text
                lines = page_text.split('\n')
                for line in lines:
                    # Chercher les lignes avec des codes postaux français
                    if re.search(r'\d{5}\s+[A-Z\s]+', line):
                        if len(line.strip()) > 5 and len(line.strip()) < 150:
                            detailed_info['adresse'] = line.strip()
                            break
                else:
                    detailed_info['adresse'] = ""
        except:
            detailed_info['adresse'] = ""
        
        # STRUCTURE/CABINET
        try:
            # Extraire depuis le nom brut d'abord
            if "Cabinet :" in lawyer_info['nom_brut']:
                cabinet_info = lawyer_info['nom_brut'].split("Cabinet :")[1].replace("+ d'infos", "")
                cabinet_parts = cabinet_info.strip().split()
                structure_parts = []
                for part in cabinet_parts:
                    if part.isupper() and len(part) > 2:  # Probable ville
                        break
                    structure_parts.append(part)
                if structure_parts:
                    detailed_info['structure'] = " ".join(structure_parts).strip()
                else:
                    detailed_info['structure'] = ""
            else:
                detailed_info['structure'] = ""
        except:
            detailed_info['structure'] = ""
        
        # ANNÉE D'INSCRIPTION AU BARREAU
        try:
            page_text = driver.page_source.lower()
            year_patterns = [
                r'inscrit.*?(\d{4})',
                r'inscription.*?(\d{4})',
                r'barreau.*?(\d{4})',
                r'depuis.*?(\d{4})'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_text)
                for year in matches:
                    if 1950 <= int(year) <= 2025:
                        detailed_info['annee_inscription'] = year
                        break
                if detailed_info.get('annee_inscription'):
                    break
            else:
                detailed_info['annee_inscription'] = ""
        except:
            detailed_info['annee_inscription'] = ""
        
        # SPÉCIALISATIONS ET COMPÉTENCES - VERSION CORRIGÉE
        try:
            # Chercher la div spécifique avec les spécialisations
            specialites_divs = driver.find_elements(By.CSS_SELECTOR, ".avocatDetails_infoCompl_col")
            specialisations_list = []
            
            for div in specialites_divs:
                div_text = div.text.strip()
                if "Spécialités :" in div_text:
                    # Récupérer tous les sous-éléments div contenant les spécialisations
                    spec_elements = div.find_elements(By.TAG_NAME, "div")
                    for spec_elem in spec_elements:
                        spec_text = spec_elem.text.strip()
                        # Filtrer les textes vides et les titres
                        if spec_text and spec_text != "Spécialités :" and len(spec_text) > 3:
                            specialisations_list.append(spec_text)
                    break
            
            # Si pas trouvé avec la méthode précise, essayer les sélecteurs field
            if not specialisations_list:
                field_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='field--field-mentionsspecialisations'] div div")
                for elem in field_elements:
                    spec_text = elem.text.strip()
                    if spec_text and len(spec_text) > 3:
                        specialisations_list.append(spec_text)
            
            # Nettoyer et formater les spécialisations
            if specialisations_list:
                # Supprimer les doublons et nettoyer
                clean_specialisations = []
                for spec in specialisations_list:
                    spec_clean = spec.strip()
                    if spec_clean and spec_clean not in clean_specialisations:
                        clean_specialisations.append(spec_clean)
                
                detailed_info['specialisations'] = " | ".join(clean_specialisations)
                detailed_info['competences'] = detailed_info['specialisations']  # Alias
            else:
                detailed_info['specialisations'] = ""
                detailed_info['competences'] = ""
                
        except Exception as e:
            detailed_info['specialisations'] = ""
            detailed_info['competences'] = ""
        
        # Ajouter la source
        detailed_info['source'] = lawyer_info['lien_detail']
        
        # Affichage du progrès
        if index % 50 == 0 or index <= 10:
            print(f"  [{index}/{total}] {prenom} {nom} - Email: {'✅' if detailed_info['email'] else '❌'}")
        
    except Exception as e:
        print(f"  ❌ Erreur avocat {index}: {e}")
        # Initialiser les champs manquants
        for field in ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 'adresse', 'structure', 'annee_inscription', 'specialisations', 'competences', 'source']:
            if field not in detailed_info:
                detailed_info[field] = ""
    
    return detailed_info

def save_progress(lawyers, current_index, total, prefix="RENNES_PROGRESS"):
    """Sauvegarde les progrès toutes les 100 extractions"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    progress_filename = f"{prefix}_{current_index}sur{total}_{timestamp}.json"
    
    try:
        with open(progress_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, ensure_ascii=False, indent=2)
        print(f"    💾 Progression sauvée: {progress_filename}")
    except Exception as e:
        print(f"    ❌ Erreur sauvegarde: {e}")

def save_final_results(lawyers, filename_prefix="RENNES_FINAL_COMPLET"):
    """Sauvegarde finale complète"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV complet
    csv_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if lawyers:
            fieldnames = [
                'page', 'index_page', 'nom_complet', 'prenom', 'nom', 
                'email', 'telephone', 'adresse', 'structure', 
                'annee_inscription', 'specialisations', 'competences', 
                'source', 'lien_detail', 'nom_brut'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers)
    
    # JSON complet
    json_filename = f"{filename_prefix}_{len(lawyers)}_avocats_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Emails seulement
    emails_filename = f"{filename_prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        emails = [lawyer['email'] for lawyer in lawyers if lawyer.get('email')]
        emailfile.write('\n'.join(emails))
    
    # Rapport final
    report_filename = f"{filename_prefix}_RAPPORT_FINAL_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as reportfile:
        reportfile.write(f"=== EXTRACTION FINALE COMPLÈTE - BARREAU DE RENNES ===\n")
        reportfile.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        reportfile.write(f"URL: https://www.ordre-avocats-rennes.fr/annuaire\n\n")
        
        emails_found = len([l for l in lawyers if l.get('email')])
        phones_found = len([l for l in lawyers if l.get('telephone')])
        addresses_found = len([l for l in lawyers if l.get('adresse')])
        structures_found = len([l for l in lawyers if l.get('structure')])
        years_found = len([l for l in lawyers if l.get('annee_inscription')])
        specialisations_found = len([l for l in lawyers if l.get('specialisations')])
        
        reportfile.write(f"NOMBRE TOTAL D'AVOCATS: {len(lawyers)}\n")
        reportfile.write(f"EMAILS RÉCUPÉRÉS: {emails_found} ({emails_found/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"TÉLÉPHONES RÉCUPÉRÉS: {phones_found} ({phones_found/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"ADRESSES RÉCUPÉRÉES: {addresses_found} ({addresses_found/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"STRUCTURES RÉCUPÉRÉES: {structures_found} ({structures_found/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"ANNÉES INSCRIPTION: {years_found} ({years_found/len(lawyers)*100:.1f}%)\n")
        reportfile.write(f"SPÉCIALISATIONS RÉCUPÉRÉES: {specialisations_found} ({specialisations_found/len(lawyers)*100:.1f}%)\n\n")
        
        # Échantillon avec spécialisations
        reportfile.write(f"=== ÉCHANTILLON AVEC SPÉCIALISATIONS ===\n")
        lawyers_with_specs = [l for l in lawyers if l.get('specialisations')][:20]
        for i, lawyer in enumerate(lawyers_with_specs):
            reportfile.write(f"\n{i+1}. {lawyer.get('prenom', '')} {lawyer.get('nom', '')}\n")
            reportfile.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
            reportfile.write(f"   Spécialisations: {lawyer.get('specialisations', 'N/A')}\n")
    
    print(f"\n📁 RÉSULTATS FINAUX SAUVEGARDÉS:")
    print(f"  - CSV: {csv_filename}")
    print(f"  - JSON: {json_filename}")
    print(f"  - Emails: {emails_filename}")
    print(f"  - Rapport: {report_filename}")
    
    return csv_filename, json_filename, emails_filename, report_filename

def main():
    print("🚀 EXTRACTION DÉTAILS COMPLÈTE - BARREAU DE RENNES")
    print("=" * 70)
    print("Extraction des détails de tous les 1107 avocats (étape 2/2)")
    print("=" * 70)
    
    # Charger la liste complète
    lawyers_list = load_lawyers_list()
    if not lawyers_list:
        return
    
    print(f"🎯 Extraction détails pour {len(lawyers_list)} avocats")
    
    driver = None
    detailed_lawyers = []
    
    try:
        driver = setup_driver()
        
        print(f"\n🔍 EXTRACTION EN COURS...")
        print("=" * 70)
        
        # Traiter TOUS les avocats
        for i, lawyer in enumerate(lawyers_list, 1):
            detailed_lawyer = extract_lawyer_details(driver, lawyer, i, len(lawyers_list))
            detailed_lawyers.append(detailed_lawyer)
            
            # Sauvegarde de progression toutes les 100
            if i % 100 == 0:
                save_progress(detailed_lawyers, i, len(lawyers_list))
                print(f"  📊 {i}/{len(lawyers_list)} avocats traités")
            
            # Pause entre chaque avocat
            time.sleep(random.uniform(0.5, 1.5))
        
        # Sauvegarde finale
        print(f"\n{'='*70}")
        print("💾 SAUVEGARDE FINALE")
        print(f"{'='*70}")
        
        csv_file, json_file, emails_file, report_file = save_final_results(detailed_lawyers)
        
        # Statistiques finales
        emails_found = len([l for l in detailed_lawyers if l.get('email')])
        phones_found = len([l for l in detailed_lawyers if l.get('telephone')])
        specialisations_found = len([l for l in detailed_lawyers if l.get('specialisations')])
        
        print(f"\n📊 RÉSULTATS FINAUX:")
        print(f"  ✅ Total avocats traités: {len(detailed_lawyers)}/1107")
        print(f"  📧 Emails récupérés: {emails_found} ({emails_found/len(detailed_lawyers)*100:.1f}%)")
        print(f"  📞 Téléphones: {phones_found} ({phones_found/len(detailed_lawyers)*100:.1f}%)")
        print(f"  📋 Spécialisations: {specialisations_found} ({specialisations_found/len(detailed_lawyers)*100:.1f}%)")
        
        print(f"\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erreur principale: {e}")
        
        if detailed_lawyers:
            save_final_results(detailed_lawyers, "RENNES_PARTIEL")
            print(f"💾 Sauvegarde partielle: {len(detailed_lawyers)} avocats")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()