#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER DE PRODUCTION - BARREAU DE BOULOGNE-SUR-MER
==================================================

Extrait tous les avocats du barreau de Boulogne-sur-Mer en mode headless
Site: https://avocats-boulogne.fr/annuaire-des-avocats-barreau-de-boulogne-sur-mer/

Informations extraites:
- Prénom, Nom, Email (principal)
- Téléphone, Adresse complète
- Année d'inscription, Spécialisations, Structure

Usage:
python3 boulogne_scraper_production.py
"""

import time
import json
import csv
import re
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def setup_driver_production():
    """Configure le driver Chrome pour la production (mode headless)"""
    options = Options()
    
    # Configuration headless pour éviter l'ouverture de fenêtres
    options.add_argument('--headless=new')  # Mode headless moderne
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--window-size=1920,1080')
    
    # User agent réaliste
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Options pour améliorer les performances
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--disable-javascript')  # Pas besoin de JS pour ce site
    
    # Désactiver les logs
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--log-level=3')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du driver: {e}")
        print("💡 Assurez-vous que ChromeDriver est installé et à jour")
        sys.exit(1)

def extract_lawyer_from_textblock_enhanced(textblock_content, block_index=0):
    """Version améliorée de l'extraction d'informations d'avocat"""
    
    info = {
        'id_extraction': block_index,
        'nom': '',
        'prenom': '',
        'nom_complet': '',
        'email': '',
        'telephone': '',
        'adresse': '',
        'ville': '',
        'code_postal': '',
        'annee_inscription': '',
        'specialisations': '',
        'structure': '',
        'contenu_brut': textblock_content[:200] + '...' if len(textblock_content) > 200 else textblock_content
    }
    
    try:
        # Nettoyer le contenu
        lines = [line.strip() for line in textblock_content.split('\n') if line.strip()]
        
        if not lines:
            return info
        
        # Première ligne = nom complet (généralement)
        name_line = lines[0] if lines else ""
        
        if (name_line and 
            not any(char.isdigit() for char in name_line) and 
            '@' not in name_line and
            len(name_line.split()) >= 1):
            
            info['nom_complet'] = name_line
            
            # Séparer prénom et nom
            name_parts = name_line.split()
            if len(name_parts) >= 2:
                info['prenom'] = name_parts[0]
                info['nom'] = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                info['nom'] = name_parts[0]
        
        # Recherche dans tout le contenu
        full_content = ' '.join(lines)
        
        # Email (priorité haute)
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', full_content)
        if email_match:
            info['email'] = email_match.group(1)
        
        # Téléphone (formats français multiples)
        phone_patterns = [
            r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2})',  # 03 21 80 83 06
            r'(\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2})',       # 03.21.80.83.06
            r'(\d{2}-\d{2}-\d{2}-\d{2}-\d{2})',           # 03-21-80-83-06
            r'(\d{10})',                                    # 0321808306
            r'(\+33\s*\d\s*\d{8})'                        # +33 3 21808306
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, full_content.replace(' ', ' '))
            if phone_match:
                phone = phone_match.group(1).strip()
                # Nettoyer et formater
                phone_clean = re.sub(r'[^\d]', '', phone)
                if len(phone_clean) == 10 and phone_clean.startswith('0'):
                    info['telephone'] = phone
                    break
        
        # Adresse (logique améliorée)
        address_parts = []
        found_contact = False
        
        for line in lines[1:]:  # Ignorer la première ligne (nom)
            # Marquer qu'on a trouvé les infos de contact
            if (re.search(r'\d{2}[.\s-]\d{2}[.\s-]\d{2}[.\s-]\d{2}[.\s-]\d{2}', line) or 
                '@' in line):
                found_contact = True
                continue
            
            # Après les contacts, chercher l'adresse
            if (found_contact and 
                '@' not in line and
                not re.search(r'\d{2}[.\s-]\d{2}[.\s-]\d{2}[.\s-]\d{2}[.\s-]\d{2}', line) and
                not re.match(r'^\s*(19|20)\d{2}\s*$', line) and
                len(line.strip()) > 3):
                
                # Éviter les lignes de spécialisation évidents
                if not re.search(r'(spécialisé|spécialité|cabinet|scp|selarl)', line, re.IGNORECASE):
                    address_parts.append(line.strip())
        
        if address_parts:
            full_address = ', '.join(address_parts)
            info['adresse'] = full_address
            
            # Extraire ville et code postal de l'adresse
            # Format typique: "... 62200 BOULOGNE SUR MER" ou "... 62930 WIMEREUX"
            city_match = re.search(r'(\d{5})\s+([A-Z\s]+)$', full_address)
            if city_match:
                info['code_postal'] = city_match.group(1)
                info['ville'] = city_match.group(2).strip()
        
        # Année d'inscription (patterns étendus)
        year_patterns = [
            r'\b(19[8-9][0-9])\b',  # 1980-1999
            r'\b(20[0-2][0-9])\b',  # 2000-2029
            r'inscrit[e]?\s+en\s+(\d{4})',  # "inscrit en 1995"
            r'barreau\s+(\d{4})'     # "barreau 1995"
        ]
        
        for pattern in year_patterns:
            year_match = re.search(pattern, full_content, re.IGNORECASE)
            if year_match:
                year = year_match.group(1)
                # Vérifier que l'année est plausible (entre 1970 et 2025)
                if 1970 <= int(year) <= 2025:
                    info['annee_inscription'] = year
                    break
        
        # Spécialisations (patterns étendus)
        specialization_patterns = [
            r'spécialisé[e]?\s+en\s+([^,\n.;]+)',
            r'spécialité[s]?\s*:\s*([^,\n.;]+)',
            r'domaine[s]?\s*:\s*([^,\n.;]+)',
            r'compétence[s]?\s*:\s*([^,\n.;]+)',
            r'(droit\s+[a-zA-Z\s]+)',
        ]
        
        for pattern in specialization_patterns:
            spec_match = re.search(pattern, full_content, re.IGNORECASE)
            if spec_match:
                spec = spec_match.group(1).strip()
                if len(spec) > 3 and len(spec) < 100:  # Filtre de longueur raisonnable
                    info['specialisations'] = spec
                    break
        
        # Structure (patterns étendus)
        structure_patterns = [
            r'(Cabinet\s+[A-Z][^,\n]+)',
            r'(SCP\s+[A-Z][^,\n]+)',
            r'(SELARL\s+[A-Z][^,\n]+)',
            r'(SELASU\s+[A-Z][^,\n]+)',
            r'(Société\s+[^,\n]+)',
            r'(Association\s+[^,\n]+)'
        ]
        
        for pattern in structure_patterns:
            struct_match = re.search(pattern, full_content, re.IGNORECASE)
            if struct_match:
                structure = struct_match.group(1).strip()
                if len(structure) > 5 and len(structure) < 80:
                    info['structure'] = structure
                    break
                
    except Exception as e:
        print(f"⚠️ Erreur lors de l'extraction du bloc #{block_index}: {e}")
    
    return info

def scrape_boulogne_production():
    """Production: Extraction complète de tous les avocats en mode headless"""
    
    print("🚀 SCRAPING PRODUCTION - BARREAU DE BOULOGNE-SUR-MER")
    print("=" * 60)
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Mode: Headless (sans interface)")
    print("🎯 Objectif: Extraction complète de tous les avocats")
    print()
    
    # Configuration driver
    print("⚙️ Initialisation du driver Chrome...")
    driver = setup_driver_production()
    
    start_time = time.time()
    
    try:
        # Accès à la page
        url = "https://avocats-boulogne.fr/annuaire-des-avocats-barreau-de-boulogne-sur-mer/"
        print(f"🌐 Connexion à: {url}")
        driver.get(url)
        
        # Attendre le chargement
        print("⏳ Attente du chargement de la page...")
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)
        
        print("✅ Page chargée avec succès")
        
        # Récupérer le source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Analyse des blocs
        print("🔍 Analyse des blocs d'informations...")
        textblocks = soup.find_all('div', class_='avia_textblock')
        print(f"📋 {len(textblocks)} blocs trouvés")
        
        # Extraction
        print("🏃‍♂️ Début de l'extraction...")
        lawyers_data = []
        processed_emails = set()
        errors_count = 0
        
        for i, textblock in enumerate(textblocks, 1):
            try:
                content = textblock.get_text().strip()
                
                # Vérifier la présence d'un email
                if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content):
                    lawyer_info = extract_lawyer_from_textblock_enhanced(content, i)
                    
                    # Éviter les doublons d'email
                    if lawyer_info['email'] and lawyer_info['email'] not in processed_emails:
                        processed_emails.add(lawyer_info['email'])
                        lawyers_data.append(lawyer_info)
                        
                        # Affichage du progrès
                        if len(lawyers_data) % 10 == 0:
                            print(f"📊 Extraction en cours... {len(lawyers_data)} avocats traités")
                
            except Exception as e:
                errors_count += 1
                print(f"⚠️ Erreur bloc #{i}: {e}")
        
        extraction_time = time.time() - start_time
        
        # Résultats
        print("\n" + "=" * 60)
        print("📈 RÉSULTATS DE L'EXTRACTION")
        print("=" * 60)
        print(f"⏱️ Temps d'extraction: {extraction_time:.1f} secondes")
        print(f"👥 Avocats extraits: {len(lawyers_data)}")
        print(f"📧 Emails uniques: {len(processed_emails)}")
        print(f"⚠️ Erreurs: {errors_count}")
        
        if lawyers_data:
            # Statistiques détaillées
            stats = {
                'avec_email': sum(1 for l in lawyers_data if l['email']),
                'avec_telephone': sum(1 for l in lawyers_data if l['telephone']),
                'avec_adresse': sum(1 for l in lawyers_data if l['adresse']),
                'avec_ville': sum(1 for l in lawyers_data if l['ville']),
                'avec_code_postal': sum(1 for l in lawyers_data if l['code_postal']),
                'avec_annee': sum(1 for l in lawyers_data if l['annee_inscription']),
                'avec_specialisations': sum(1 for l in lawyers_data if l['specialisations']),
                'avec_structure': sum(1 for l in lawyers_data if l['structure'])
            }
            
            print(f"\n📊 STATISTIQUES DÉTAILLÉES:")
            for key, value in stats.items():
                percentage = (value / len(lawyers_data)) * 100
                print(f"   {key.replace('_', ' ').title()}: {value} ({percentage:.1f}%)")
            
            # Sauvegarde des fichiers
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            print(f"\n💾 GÉNÉRATION DES FICHIERS...")
            
            # 1. JSON complet
            json_file = f"/Users/paularnould/boulogne_COMPLET_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(lawyers_data, f, indent=2, ensure_ascii=False)
            
            # 2. CSV complet
            csv_file = f"/Users/paularnould/boulogne_COMPLET_{timestamp}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if lawyers_data:
                    fieldnames = lawyers_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(lawyers_data)
            
            # 3. Emails uniquement
            emails_file = f"/Users/paularnould/boulogne_EMAILS_COMPLET_{timestamp}.txt"
            with open(emails_file, 'w', encoding='utf-8') as f:
                for lawyer in lawyers_data:
                    if lawyer['email']:
                        f.write(f"{lawyer['email']}\n")
            
            # 4. Rapport complet
            report_file = f"/Users/paularnould/boulogne_RAPPORT_COMPLET_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("RAPPORT COMPLET - SCRAPING BARREAU DE BOULOGNE-SUR-MER\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"🕒 Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"🌐 URL source: {url}\n")
                f.write(f"⏱️ Temps d'extraction: {extraction_time:.1f} secondes\n")
                f.write(f"🔧 Mode: Production (headless)\n\n")
                
                f.write("📈 RÉSULTATS GLOBAUX:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Total avocats extraits: {len(lawyers_data)}\n")
                f.write(f"Emails uniques collectés: {len(processed_emails)}\n")
                f.write(f"Erreurs rencontrées: {errors_count}\n")
                f.write(f"Taux de réussite: {((len(lawyers_data) / len(textblocks)) * 100):.1f}%\n\n")
                
                f.write("📊 STATISTIQUES PAR CHAMP:\n")
                f.write("-" * 30 + "\n")
                for key, value in stats.items():
                    percentage = (value / len(lawyers_data)) * 100
                    f.write(f"{key.replace('_', ' ').title():<20}: {value:>3} ({percentage:>5.1f}%)\n")
                
                f.write(f"\n💾 FICHIERS GÉNÉRÉS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"📄 Données JSON complètes: {json_file}\n")
                f.write(f"📊 Données CSV complètes: {csv_file}\n")
                f.write(f"📧 Liste emails: {emails_file}\n")
                f.write(f"📋 Ce rapport: {report_file}\n")
                
                f.write(f"\n🎯 UTILISATION:\n")
                f.write("-" * 30 + "\n")
                f.write("- Le fichier JSON contient toutes les données structurées\n")
                f.write("- Le fichier CSV peut être ouvert dans Excel/Sheets\n")
                f.write("- Le fichier TXT contient uniquement les emails (1 par ligne)\n")
                f.write("- Ce rapport contient les statistiques complètes\n")
            
            print(f"✅ Fichiers générés avec succès:")
            print(f"   📄 JSON: {json_file}")
            print(f"   📊 CSV: {csv_file}")
            print(f"   📧 Emails: {emails_file}")
            print(f"   📋 Rapport: {report_file}")
            
            print(f"\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print(f"💡 Vous disposez maintenant de {len(lawyers_data)} fiches d'avocats complètes")
            
        else:
            print("❌ Aucune donnée extraite")
            
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        
    finally:
        driver.quit()
        total_time = time.time() - start_time
        print(f"\n🏁 Fin du processus ({total_time:.1f}s total)")

if __name__ == "__main__":
    scrape_boulogne_production()