#!/usr/bin/env python3
"""
TEST RAPIDE - TAUX DE COUVERTURE DATES DE SERMENT
Teste 20 profils d'avocats du Barreau de Lyon pour estimer le taux de couverture des dates de serment
"""

import requests
from bs4 import BeautifulSoup
import re
import time

def extraire_date_serment(url):
    """Extraction de la date de serment depuis une page d'avocat"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        response = session.get(url, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            # Méthode 1: Rechercher "Prestation de serment" + date française
            serment_pattern = r'Prestation de serment[^\d]*(\d{1,2}\s+\w+\s+\d{4})'
            match = re.search(serment_pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            # Méthode 2: Rechercher toutes les dates françaises
            all_dates_fr = re.findall(r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b', 
                                     text_content, re.IGNORECASE)
            if all_dates_fr:
                return all_dates_fr[0]
            
            # Méthode 3: Rechercher dans les éléments contenant "serment"
            elements = soup.find_all(string=re.compile(r'serment', re.IGNORECASE))
            for element in elements:
                parent = element.parent if hasattr(element, 'parent') else None
                if parent:
                    parent_text = parent.get_text(strip=True)
                    date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', parent_text)
                    if date_match:
                        return date_match.group(1).strip()
            
        return None
    except Exception:
        return None

def tester_echantillon_dates():
    """Teste un échantillon de profils pour estimer le taux de couverture"""
    print("🧪 TEST TAUX DE COUVERTURE DATES DE SERMENT")
    print("Échantillon : 20 profils d'avocats du Barreau de Lyon")
    print("=" * 60)
    
    # Générer URLs réelles en utilisant l'API
    urls_test = []
    try:
        api_response = requests.get("https://www.barreaulyon.com/wp-json/wp/v2/annuaire?per_page=20")
        if api_response.status_code == 200:
            avocats_api = api_response.json()
            for avocat in avocats_api[:20]:
                url = avocat.get('link', '')
                if url:
                    urls_test.append(url)
            print(f"✅ {len(urls_test)} URLs réelles récupérées via API")
        else:
            print("❌ API non accessible, test impossible")
            return 0, 0, 0
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return 0, 0, 0
    
    dates_trouvees = 0
    urls_testees = 0
    
    print(f"\n🔄 TEST DE {len(urls_test)} PROFILS")
    
    for i, url in enumerate(urls_test):
        print(f"\n[{i+1}/{len(urls_test)}] Test de {url}")
        
        date_serment = extraire_date_serment(url)
        urls_testees += 1
        
        if date_serment:
            dates_trouvees += 1
            print(f"   ✅ DATE TROUVÉE: {date_serment}")
        else:
            print(f"   ❌ Pas de date trouvée")
        
        # Pause respectueuse
        time.sleep(1.5)
    
    # Calcul des statistiques
    taux_couverture = (dates_trouvees / urls_testees) * 100 if urls_testees > 0 else 0
    
    print(f"\n📊 RÉSULTATS DU TEST ÉCHANTILLON:")
    print("=" * 50)
    print(f"✅ Dates trouvées: {dates_trouvees}/{urls_testees}")
    print(f"📈 Taux de couverture: {taux_couverture:.1f}%")
    
    # Estimation pour 4141 avocats
    if taux_couverture > 0:
        estimation_total = int((taux_couverture / 100) * 4141)
        print(f"\n🎯 ESTIMATION POUR 4141 AVOCATS:")
        print(f"📈 Dates potentielles récupérables: ~{estimation_total}")
        print(f"📈 Taux potentiel: {taux_couverture:.1f}%")
        
        if taux_couverture >= 80:
            print("🏆 EXCELLENT taux de couverture potentiel !")
        elif taux_couverture >= 60:
            print("🎯 BON taux de couverture potentiel")
        elif taux_couverture >= 40:
            print("⚠️ Taux de couverture MOYEN")
        else:
            print("❌ Taux de couverture FAIBLE")
    else:
        print("❌ Aucune date trouvée dans l'échantillon")
    
    return taux_couverture, dates_trouvees, urls_testees

if __name__ == "__main__":
    tester_echantillon_dates()