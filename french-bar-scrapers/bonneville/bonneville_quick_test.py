#!/usr/bin/env python3
"""
Test rapide pour analyser le site Bonneville
"""

import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_with_requests():
    """Test avec requests pour voir la structure de base"""
    print("=== TEST AVEC REQUESTS ===")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(
            "https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/",
            headers=headers,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher des liens contenant "avocat" ou des noms
        links = soup.find_all('a', href=True)
        
        lawyer_links = []
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if (('avocat' in href.lower() or 'lawyer' in href.lower() or 
                 'member' in href.lower()) and len(text) > 3):
                lawyer_links.append({
                    'text': text,
                    'href': href
                })
                
        print(f"Liens d'avocats potentiels trouvés : {len(lawyer_links)}")
        for link in lawyer_links[:5]:
            print(f"  - {link['text']} -> {link['href']}")
            
        # Chercher du texte qui pourrait être des noms
        text_content = soup.get_text()
        
        # Patterns pour trouver des noms d'avocats
        import re
        patterns = [
            r'Me\.?\s+([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)',
            r'Maître\s+([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)',
            r'\b([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)\b.*?avocat',
            r'avocat[^.]*?([A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+)'
        ]
        
        names_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            names_found.extend(matches)
            
        if names_found:
            print(f"Noms potentiels trouvés via regex : {len(set(names_found))}")
            for name in set(names_found)[:5]:
                print(f"  - {name}")
        else:
            print("Aucun nom trouvé via regex")
            
        return lawyer_links, list(set(names_found))
        
    except Exception as e:
        print(f"Erreur requests : {e}")
        return [], []

def test_with_selenium_quick():
    """Test rapide avec Selenium"""
    print("\n=== TEST AVEC SELENIUM ===")
    
    options = Options()
    # Mode visuel pour voir ce qui se passe
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("Chargement de la page...")
        driver.get("https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/")
        
        # Attendre 5 secondes pour voir ce qui se charge
        time.sleep(5)
        
        # Accepter les cookies si présents
        try:
            cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Tout accepter')]")
            cookie_btn.click()
            print("✅ Cookies acceptés")
            time.sleep(2)
        except:
            print("Pas de cookies à accepter")
            
        # Chercher un bouton pour afficher la liste
        try:
            display_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'CLIQUEZ ICI')]")
            print(f"✅ Trouvé bouton : {display_btn.text}")
            driver.execute_script("arguments[0].click();", display_btn)
            time.sleep(3)
        except:
            print("Pas de bouton d'affichage trouvé")
            
        # Analyser ce qui est maintenant visible
        page_text = driver.page_source
        
        # Chercher des éléments qui pourraient contenir des avocats
        potential_elements = driver.find_elements(By.CSS_SELECTOR, ".et_pb_text, .et_pb_module, p, div")
        
        lawyer_elements = []
        for elem in potential_elements:
            text = elem.text.strip()
            if (text and 
                len(text) > 5 and len(text) < 200 and
                ' ' in text and
                not any(word in text.lower() for word in ['copyright', 'mentions', 'contact@', 'accueil'])):
                
                # Vérifier si ça ressemble à un nom
                if (text.count(' ') <= 3 and 
                    any(c.isupper() for c in text) and
                    not text.lower().startswith(('tél', 'tel', 'mail', 'adresse', 'le ', 'la ', 'du ', 'de '))):
                    lawyer_elements.append(text)
                    
        print(f"Éléments de texte potentiels : {len(lawyer_elements)}")
        for elem in lawyer_elements[:10]:
            print(f"  - {elem}")
            
        # Sauvegarder la page pour inspection
        with open("bonneville_selenium_debug.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✅ Page sauvegardée : bonneville_selenium_debug.html")
        
        return lawyer_elements
        
    except Exception as e:
        print(f"Erreur Selenium : {e}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🔍 ANALYSE RAPIDE BONNEVILLE")
    
    # Test avec requests
    req_links, req_names = test_with_requests()
    
    # Test avec Selenium  
    selenium_elements = test_with_selenium_quick()
    
    print(f"\n📊 RÉSUMÉ :")
    print(f"Liens trouvés (requests) : {len(req_links)}")
    print(f"Noms trouvés (requests) : {len(req_names)}")
    print(f"Éléments trouvés (selenium) : {len(selenium_elements)}")