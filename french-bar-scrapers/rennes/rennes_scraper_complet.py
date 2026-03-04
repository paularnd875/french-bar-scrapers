#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER COMPLET - BARREAU DE RENNES
===================================

Script pour extraire tous les avocats du barreau de Rennes avec leurs détails complets.
URL: https://www.ordre-avocats-rennes.fr/annuaire

ÉTAPES D'UTILISATION:
1. Lancer d'abord: python3 rennes_liste_complete.py (récupère la liste de tous les avocats)
2. Puis lancer: python3 rennes_extraction_details.py (extrait les détails de chaque avocat)

RÉSULTAT ATTENDU: ~1107 avocats avec emails, téléphones, adresses, spécialisations
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

def accept_cookies(driver):
    """Gère l'acceptation des cookies"""
    try:
        print("🍪 Tentative d'acceptation des cookies...")
        time.sleep(3)
        
        cookie_selectors = [
            "#axeptio_btn_acceptAll",
            "button[data-axeptio-cookie='all']",
            "button.axeptio-button--accept-all"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                cookie_btn.click()
                print("✅ Cookies acceptés")
                time.sleep(2)
                return True
            except TimeoutException:
                continue
        
        print("⚠️ Pas de cookies à accepter")
        return True
        
    except Exception as e:
        print(f"❌ Erreur cookies: {e}")
        return False

def get_total_pages(driver):
    """Détermine le nombre total de pages (0-36 = 37 pages)"""
    try:
        driver.get("https://www.ordre-avocats-rennes.fr/annuaire")
        time.sleep(3)
        
        # Chercher le lien "Dernière page"
        last_page_links = driver.find_elements(By.CSS_SELECTOR, "a[title*='aller à la dernière page'], a[href*='page=36'], .pager-last a")
        
        for link in last_page_links:
            href = link.get_attribute('href')
            if 'page=' in href:
                page_num = href.split('page=')[-1]
                try:
                    max_page = int(page_num)
                    total_pages = max_page + 1  # page 0-36 = 37 pages
                    print(f"📄 {total_pages} pages détectées (pages 0-{max_page})")
                    return total_pages
                except ValueError:
                    continue
        
        print("📄 37 pages par défaut (1107 avocats)")
        return 37
        
    except Exception as e:
        print(f"❌ Erreur calcul pages: {e}")
        return 37

def navigate_to_page(driver, page_num):
    """Navigue vers une page spécifique"""
    try:
        url_page = page_num - 1  # page 1 = page=0
        
        if page_num == 1:
            url = "https://www.ordre-avocats-rennes.fr/annuaire"
        else:
            url = f"https://www.ordre-avocats-rennes.fr/annuaire?page={url_page}"
        
        print(f"🌐 Page {page_num}: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        lawyer_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/avocat-']")
        
        if lawyer_links:
            print(f"  ✅ Page {page_num} chargée avec {len(lawyer_links)} liens")
            return True
        else:
            print(f"  ⚠️ Page {page_num} sans liens d'avocats")
            return False
        
    except Exception as e:
        print(f"❌ Erreur navigation page {page_num}: {e}")
        return False

def extract_lawyers_from_page(driver, page_num):
    """Extrait SEULEMENT les noms et liens des avocats (pas les détails)"""
    lawyers = []
    
    try:
        lawyer_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/avocat-']")
        
        # Déduplication par URL
        unique_links = {}
        for link in lawyer_links:
            href = link.get_attribute('href')
            if href and href not in unique_links:
                unique_links[href] = link
        
        print(f"  📋 {len(unique_links)} avocats uniques trouvés")
        
        for i, (href, link) in enumerate(unique_links.items()):
            try:
                raw_name = link.text.strip()
                
                if not raw_name or len(raw_name) < 3:
                    if '/avocat-' in href:
                        name_from_url = href.split('/avocat-')[-1]
                        name_parts = name_from_url.replace('-', ' ').title().split()
                        if len(name_parts) >= 2:
                            raw_name = f"Me {' '.join(name_parts)}"
                
                if not raw_name:
                    print(f"    ⚠️ Nom vide pour {href}")
                    continue
                
                lawyer_info = {
                    'page': page_num,
                    'nom_brut': raw_name,
                    'lien_detail': href if href.startswith('http') else f"https://www.ordre-avocats-rennes.fr{href}",
                    'index_page': i + 1
                }
                
                lawyers.append(lawyer_info)
                
            except Exception as e:
                print(f"    ❌ Erreur avocat {i+1} sur page {page_num}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Erreur extraction page {page_num}: {e}")
    
    return lawyers

def save_complete_list(all_lawyers):
    """Sauvegarde la liste complète"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_filename = f"RENNES_LISTE_COMPLETE_{len(all_lawyers)}_avocats_{timestamp}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(all_lawyers, f, ensure_ascii=False, indent=2)
    
    csv_filename = f"RENNES_LISTE_COMPLETE_{len(all_lawyers)}_avocats_{timestamp}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        if all_lawyers:
            fieldnames = ['page', 'nom_brut', 'lien_detail', 'index_page']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_lawyers)
    
    return json_filename, csv_filename

def main():
    print("🚀 EXTRACTION LISTE COMPLÈTE - BARREAU DE RENNES")
    print("=" * 70)
    print("Récupération de tous les 1107 avocats (étape 1/2)")
    print("=" * 70)
    
    driver = None
    all_lawyers = []
    
    try:
        driver = setup_driver()
        
        driver.get("https://www.ordre-avocats-rennes.fr/annuaire")
        accept_cookies(driver)
        
        total_pages = get_total_pages(driver)
        print(f"📄 {total_pages} pages à traiter")
        
        # Parcourir TOUTES les pages
        for page_num in range(1, total_pages + 1):
            print(f"\n📄 PAGE {page_num}/{total_pages}")
            
            if not navigate_to_page(driver, page_num):
                continue
            
            page_lawyers = extract_lawyers_from_page(driver, page_num)
            if not page_lawyers:
                continue
            
            all_lawyers.extend(page_lawyers)
            print(f"  📊 Total actuel: {len(all_lawyers)} avocats")
            
            time.sleep(random.uniform(1, 3))
        
        # Sauvegarde finale
        if all_lawyers:
            json_file, csv_file = save_complete_list(all_lawyers)
            
            print(f"\n🎉 LISTE COMPLÈTE RÉCUPÉRÉE!")
            print(f"  ✅ Total: {len(all_lawyers)} avocats")
            print(f"  📁 JSON: {json_file}")
            print(f"  📁 CSV: {csv_file}")
            print(f"\n➡️  ÉTAPE SUIVANTE: Lancez rennes_extraction_details.py")
        else:
            print("❌ Aucun avocat trouvé!")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()