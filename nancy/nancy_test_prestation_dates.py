#!/usr/bin/env python3
"""
Test rapide pour valider l'extraction des dates de prestation de serment
"""

import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_prestation_extraction():
    print("🔍 TEST D'EXTRACTION DES DATES DE PRESTATION DE SERMENT")
    print("=" * 60)
    
    # URLs de test (quelques avocats)
    test_urls = [
        "https://avocats-nancy.com/portfolio/adam-samuel/",
        "https://avocats-nancy.com/portfolio/adriant-guylene/", 
        "https://avocats-nancy.com/portfolio/alexandre-laurene/",
        "https://avocats-nancy.com/portfolio/altmeyer-cedric/",
        "https://avocats-nancy.com/portfolio/amm-sahra/"
    ]
    
    # Setup driver headless
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        for i, url in enumerate(test_urls, 1):
            print(f"\n{i}. Test sur: {url}")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Tester la fonction d'extraction
                year, date = extract_prestation_date(driver)
                
                if year and date:
                    print(f"   ✅ TROUVÉ: {date} (année {year})")
                else:
                    print(f"   ❌ Non trouvé - cherchons manuellement...")
                    
                    # Debug: chercher dans le texte complet
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    if "prestation" in page_text.lower():
                        lines = page_text.split('\n')
                        for line in lines:
                            if "prestation" in line.lower():
                                print(f"      DEBUG: {line.strip()}")
                    else:
                        print(f"      DEBUG: Aucune mention de 'prestation' trouvée")
                        
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
    finally:
        driver.quit()

def extract_prestation_date(driver):
    """Fonction d'extraction des dates de prestation"""
    try:
        # Méthode 1: Paragraphe spécifique
        prestation_elements = driver.find_elements(By.CSS_SELECTOR, 
            "p.has-text-align-right.wp-block-paragraph")
        
        for elem in prestation_elements:
            text = elem.text.strip()
            if "prestation de serment" in text.lower():
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        year = int(date_str.split('/')[-1])
                        return year, date_str
                    except:
                        pass
        
        # Méthode 2: Tous les paragraphes
        all_paragraphs = driver.find_elements(By.TAG_NAME, "p")
        for p in all_paragraphs:
            text = p.text.strip()
            if "prestation de serment" in text.lower():
                date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        year = int(date_str.split('/')[-1])
                        return year, date_str
                    except:
                        pass
        
        # Méthode 3: Texte complet
        page_text = driver.find_element(By.TAG_NAME, "body").text
        prestation_match = re.search(r'prestation\s+de\s+serment\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})', 
                                    page_text, re.IGNORECASE)
        if prestation_match:
            date_str = prestation_match.group(1)
            try:
                year = int(date_str.split('/')[-1])
                return year, date_str
            except:
                pass
                
    except Exception as e:
        print(f"Erreur extraction: {e}")
    
    return None, None

if __name__ == "__main__":
    test_prestation_extraction()