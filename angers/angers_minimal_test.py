#!/usr/bin/env python3
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

# Test minimal
print("🔄 Test de base...")

try:
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    url = "https://barreau-angers.org/annuaire-des-avocats/"
    print(f"📞 Connexion à {url}...")
    
    response = session.get(url, timeout=10)
    print(f"✅ Réponse: {response.status_code}")
    print(f"📊 Taille: {len(response.content)} bytes")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Chercher les liens d'avocats
    links = []
    for a in soup.find_all('a', href=True):
        if '/avocat/' in a['href']:
            links.append(a['href'])
    
    print(f"🔗 {len(links)} liens trouvés")
    
    if links:
        # Tester le premier avocat
        first_link = links[0]
        if first_link.startswith('/'):
            first_link = f"https://barreau-angers.org{first_link}"
        
        print(f"🧪 Test du premier: {first_link}")
        
        resp2 = session.get(first_link, timeout=10)
        print(f"✅ Page avocat: {resp2.status_code}")
        
        soup2 = BeautifulSoup(resp2.content, 'html.parser')
        
        # Extraction basique
        title = soup2.find('h1')
        name = title.get_text().strip() if title else "Non trouvé"
        
        email_link = soup2.find('a', href=lambda x: x and 'mailto:' in x)
        email = email_link['href'].replace('mailto:', '') if email_link else "Non trouvé"
        
        print(f"👤 Nom: {name}")
        print(f"📧 Email: {email}")
        
        # Sauvegarder le test
        result = {
            'total_lawyers': len(links),
            'test_lawyer': {
                'name': name,
                'email': email,
                'url': first_link
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open('angers_minimal_test_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("✅ Test réussi ! Prêt pour le scraping complet.")
        
    else:
        print("❌ Aucun lien d'avocat trouvé")

except Exception as e:
    print(f"❌ Erreur: {e}")