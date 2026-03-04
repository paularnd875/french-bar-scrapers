#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER BARREAU D'AVEYRON - VERSION FINALE
========================================
Scraper pour l'extraction complète des avocats du Barreau d'Aveyron
URL: https://www.avocats12.com/liste-des-avocats

Auteur: Claude Code
Date: Février 2026
Repository: https://github.com/paularnd875/french-bar-scrapers
"""

import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import urllib.parse
import re
import sys
import os

def mapping_noms_corriges_complet():
    """Mapping complet des noms avec problèmes d'accents dans les URLs"""
    return {
        'archimbaud-th%': 'Archimbaud Théophile',
        'berger-fran%': 'Berger François-Xavier',
        'bessi%': 'Bessière Maxime',
        'bourinet-danneville-b%': 'Bourinet-Danneville Béatrice',
        'boutaric-st%': 'Boutaric Stéphane',
    }

def corriger_nom_depuis_url(url):
    """Corrige le nom à partir de l'URL avec le mapping complet"""
    mapping = mapping_noms_corriges_complet()
    nom_url = url.split('/')[-1] if url else ""
    
    if nom_url in mapping:
        nom_corrige = mapping[nom_url]
        parties = nom_corrige.split(' ', 1)
        return {
            'nom_famille': parties[0],
            'prenom': parties[1] if len(parties) > 1 else '',
            'nom_complet_corrige': nom_corrige,
            'correction_appliquee': True
        }
    
    try:
        nom_decode = urllib.parse.unquote(nom_url)
        nom_decode = nom_decode.replace('-', ' ')
        nom_decode = ' '.join(word.capitalize() for word in nom_decode.split())
        parties = nom_decode.split(' ', 1)
        return {
            'nom_famille': parties[0],
            'prenom': parties[1] if len(parties) > 1 else '',
            'nom_complet_corrige': nom_decode,
            'correction_appliquee': False
        }
    except:
        return {
            'nom_famille': nom_url,
            'prenom': '',
            'nom_complet_corrige': nom_url,
            'correction_appliquee': False
        }

def extraire_par_selecteur(driver, selecteur, description=""):
    """Extraction par sélecteur CSS avec gestion d'erreurs"""
    try:
        element = driver.find_element(By.CSS_SELECTOR, selecteur)
        text = element.text.strip()
        if text and description and not os.environ.get('SILENT_MODE'):
            print(f"       {description}: {text}")
        return text
    except:
        return ""

def extraire_info_avocat(driver, url_avocat):
    """Extraction complète des informations d'un avocat avec sélecteurs Wix précis"""
    
    correction_noms = corriger_nom_depuis_url(url_avocat)
    
    avocat_info = {
        'nom_famille': correction_noms['nom_famille'],
        'prenom': correction_noms['prenom'],
        'nom_complet': correction_noms['nom_complet_corrige'],
        'telephone': '',
        'fax': '',
        'adresse': '',
        'ville': '',
        'annee_inscription': '',
        'statut': '',
        'url_source': url_avocat
    }
    
    try:
        if not os.environ.get('SILENT_MODE'):
            print(f"   📝 Extraction: {correction_noms['nom_complet_corrige']}")
        
        driver.get(url_avocat)
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#comp-kezosnjb, body")))
        time.sleep(3)
        
        # Sélecteurs Wix précis
        avocat_info['statut'] = extraire_par_selecteur(driver, "#comp-kezp4zjj", "👔 Statut")
        avocat_info['annee_inscription'] = extraire_par_selecteur(driver, "#comp-kezp5i4q", "📅 Année")
        avocat_info['telephone'] = extraire_par_selecteur(driver, "#comp-kezpcw70", "📞 Téléphone")
        avocat_info['fax'] = extraire_par_selecteur(driver, "#comp-kezph14q", "📠 Fax")
        avocat_info['adresse'] = extraire_par_selecteur(driver, "#comp-kezq0cbl", "🏠 Adresse")
        
        # Extraction ville de l'adresse
        if avocat_info['adresse']:
            ville_match = re.search(r'(\d{5})\s+([A-Za-zÀ-ÿ\s-]+)', avocat_info['adresse'])
            if ville_match:
                avocat_info['ville'] = ville_match.group(2).strip()
        
    except Exception as e:
        if not os.environ.get('SILENT_MODE'):
            print(f"       ❌ Erreur: {str(e)[:50]}")
    
    return avocat_info

def scraper_aveyron_complet(mode="production"):
    """Scraper principal pour l'extraction complète du Barreau d'Aveyron"""
    
    if not os.environ.get('SILENT_MODE'):
        print("🏛️  SCRAPER BARREAU D'AVEYRON")
        print("🔗 https://www.avocats12.com/liste-des-avocats")
        print("=" * 50)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get("https://www.avocats12.com/liste-des-avocats")
        time.sleep(3)
        
        # Récupération des liens
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/liste-des-avocats/']")
        urls_avocats = []
        for link in links:
            href = link.get_attribute('href')
            if href and '/liste-des-avocats/' in href and href != "https://www.avocats12.com/liste-des-avocats":
                if href not in urls_avocats:
                    urls_avocats.append(href)
        
        if not os.environ.get('SILENT_MODE'):
            print(f"📋 {len(urls_avocats)} avocats détectés")
        
        # Test limité pour validation
        if mode == "test":
            urls_avocats = urls_avocats[:5]
        
        # Extraction
        avocats_data = []
        for i, url in enumerate(urls_avocats, 1):
            if not os.environ.get('SILENT_MODE'):
                print(f"\n📝 Avocat {i}/{len(urls_avocats)}")
            
            avocat_info = extraire_info_avocat(driver, url)
            avocats_data.append(avocat_info)
            time.sleep(1.5)
        
        # Sauvegarde
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = f"AVEYRON_{mode.upper()}_{len(avocats_data)}avocats_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if avocats_data:
                writer = csv.DictWriter(f, fieldnames=avocats_data[0].keys())
                writer.writeheader()
                writer.writerows(avocats_data)
        
        json_file = f"AVEYRON_{mode.upper()}_{len(avocats_data)}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(avocats_data, f, indent=2, ensure_ascii=False)
        
        if not os.environ.get('SILENT_MODE'):
            print(f"\n✅ Extraction terminée: {len(avocats_data)} avocats")
            print(f"📄 Fichiers: {csv_file}, {json_file}")
        
        return {'success': True, 'total_avocats': len(avocats_data)}
        
    except Exception as e:
        if not os.environ.get('SILENT_MODE'):
            print(f"❌ Erreur: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        driver.quit()

if __name__ == "__main__":
    mode = "production" if len(sys.argv) < 2 else sys.argv[1]
    
    if mode == "production" and not os.environ.get('SILENT_MODE'):
        response = input("Confirmer extraction complète ? (oui/non): ")
        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Extraction annulée")
            sys.exit(1)
    
    resultats = scraper_aveyron_complet(mode)
    sys.exit(0 if resultats['success'] else 1)