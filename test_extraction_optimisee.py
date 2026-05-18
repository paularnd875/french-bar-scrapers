#!/usr/bin/env python3
"""
TEST RAPIDE DE L'EXTRACTION OPTIMISÉE
Teste les techniques avancées sur quelques profils sans date
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def test_extraction_avancee():
    print("🧪 TEST EXTRACTION OPTIMISÉE - 5 PROFILS SANS DATE")
    print("=" * 60)
    
    # Charger le fichier pour obtenir des profils sans date
    df = pd.read_csv('BARREAU_LYON_COMPLET_4141avocats_2593emails_20260505_165132.csv')
    sans_dates = df[df['date_serment'].isna() | (df['date_serment'] == '')].copy()
    
    # Prendre les 5 premiers
    test_sample = sans_dates.head(5)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    for i, (_, row) in enumerate(test_sample.iterrows(), 1):
        url = row.get('url', '')
        nom = row.get('nom', '')
        prenom = row.get('prenom', '')
        
        print(f"\n[{i}/5] {prenom} {nom}")
        print(f"URL: {url}")
        
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()
                
                # Test techniques avancées
                dates_trouvees = []
                
                # Technique 1: Pattern Prestation de serment
                serment_match = re.search(r'Prestation de serment[^\d]*(\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})', text_content, re.IGNORECASE)
                if serment_match:
                    dates_trouvees.append(f"Technique 1: {serment_match.group(1)}")
                
                # Technique 2: Toutes dates françaises
                dates_fr = re.findall(r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b', text_content, re.IGNORECASE)
                if dates_fr:
                    for date_str in dates_fr[:2]:  # Max 2
                        dates_trouvees.append(f"Technique 2: {date_str}")
                
                # Technique 3: Recherche contexte "serment"
                serment_positions = [match.start() for match in re.finditer(r'serment', text_content, re.IGNORECASE)]
                for pos in serment_positions[:2]:  # Max 2
                    start = max(0, pos - 200)
                    end = min(len(text_content), pos + 200)
                    contexte = text_content[start:end]
                    date_match = re.search(r'(\d{4})', contexte)
                    if date_match:
                        annee = int(date_match.group())
                        if 1970 <= annee <= 2030:
                            dates_trouvees.append(f"Technique 3: {annee}")
                            break
                
                if dates_trouvees:
                    print("✅ DATES TROUVÉES:")
                    for date in dates_trouvees[:3]:  # Max 3 affichées
                        print(f"   • {date}")
                else:
                    print("❌ Aucune date trouvée avec techniques avancées")
                    # Regarder si "serment" est présent
                    if 'serment' in text_content.lower():
                        print("⚠️  'serment' détecté mais pas de date extraite")
                    else:
                        print("ℹ️  Pas de mention 'serment' trouvée")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur: {str(e)[:50]}")
        
        import time
        time.sleep(1.5)  # Pause respectueuse
    
    print("\n📊 TEST TERMINÉ")

if __name__ == "__main__":
    test_extraction_avancee()