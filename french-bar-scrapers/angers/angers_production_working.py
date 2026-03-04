#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import csv
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

def get_session():
    """Crée une session requests optimisée"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    return session

def extract_lawyer_data_from_html(html_content, url):
    """Extrait les données d'un avocat depuis le HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        
        lawyer_data = {
            'url': url,
            'extraction_date': datetime.now().isoformat()
        }
        
        # Nom complet
        title_selectors = ['h1', '.entry-title', '.lawyer-name', '.avocat-name']
        full_name = None
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                full_name = element.get_text().strip()
                break
        
        if full_name:
            lawyer_data['nom_complet'] = full_name
            # Nettoyer et séparer
            clean_name = full_name.replace("Me ", "").replace("Maître ", "").strip()
            name_parts = clean_name.split()
            if len(name_parts) >= 2:
                lawyer_data['prenom'] = name_parts[0]
                lawyer_data['nom'] = ' '.join(name_parts[1:])
            else:
                lawyer_data['prenom'] = ""
                lawyer_data['nom'] = clean_name
        else:
            lawyer_data['nom_complet'] = "Non trouvé"
            lawyer_data['prenom'] = ""
            lawyer_data['nom'] = ""
        
        # Email
        email = None
        # Chercher les liens mailto
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').strip()
        
        # Si pas trouvé, chercher dans le texte
        if not email:
            email_matches = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content)
            if email_matches:
                email = email_matches[0]
        
        lawyer_data['email'] = email if email else "Non trouvé"
        
        # Adresse (codes postaux 49xxx pour Maine-et-Loire)
        address_matches = re.findall(r'[^\n\r]*49\d{3}[^\n\r]*', text_content)
        if address_matches:
            address = address_matches[0].strip()
            # Nettoyer l'adresse
            address = re.sub(r'\s+', ' ', address).strip()
            lawyer_data['adresse'] = address
        else:
            lawyer_data['adresse'] = "Non trouvé"
        
        # Année d'inscription
        inscription_patterns = [
            r'inscrit.*?(\d{4})',
            r'inscription.*?(\d{4})',
            r'barreau.*?(\d{4})',
            r'asserment.*?(\d{4})'
        ]
        
        year = None
        text_lower = text_content.lower()
        for pattern in inscription_patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_year = int(match.group(1))
                if 1970 <= potential_year <= 2024:
                    year = str(potential_year)
                    break
        
        lawyer_data['annee_inscription'] = year if year else "Non trouvé"
        
        # Spécialisations
        specializations = []
        law_domains = [
            'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
            'droit de la famille', 'droit immobilier', 'droit des affaires',
            'droit public', 'droit administratif', 'droit fiscal', 'droit social',
            'droit bancaire', 'droit des sociétés', 'droit international',
            'droit de la construction', 'droit de l\'environnement'
        ]
        
        for domain in law_domains:
            if domain in text_lower:
                specializations.append(domain.title())
        
        # Chercher d'autres mentions de spécialisations
        if not specializations:
            spec_elements = soup.find_all(text=re.compile(r'spécialis|domaine|compétence'))
            for element in spec_elements:
                parent_text = element.parent.get_text() if element.parent else ""
                if 'droit' in parent_text.lower():
                    specializations.append(parent_text.strip()[:50])  # Limiter la longueur
        
        lawyer_data['specialisations'] = specializations if specializations else ["Non trouvé"]
        
        # Structure/Cabinet
        structure = "Exercice individuel"
        if 'cabinet' in text_lower:
            cabinet_matches = re.findall(r'cabinet[^.\n\r]{0,50}', text_lower)
            if cabinet_matches:
                structure = cabinet_matches[0].strip().title()
        elif 'société' in text_lower and 'avocats' in text_lower:
            structure = "Société d'avocats"
        elif 'scpa' in text_lower or 'scp' in text_lower:
            structure = "Société civile professionnelle"
        
        lawyer_data['structure'] = structure
        
        return lawyer_data
        
    except Exception as e:
        print(f"❌ Erreur extraction HTML: {e}")
        return None

def get_lawyer_links_requests(session, base_url):
    """Récupère les liens d'avocats avec requests"""
    try:
        print(f"🔍 Récupération des liens: {base_url}")
        
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tous les liens vers les pages d'avocats
        links = set()
        
        # Différents sélecteurs possibles
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/avocat/' in href:
                if href.startswith('/'):
                    href = f"https://barreau-angers.org{href}"
                elif not href.startswith('http'):
                    href = f"https://barreau-angers.org/{href}"
                links.add(href)
        
        lawyer_links = list(links)
        print(f"✅ {len(lawyer_links)} liens d'avocats trouvés")
        
        return lawyer_links
        
    except Exception as e:
        print(f"❌ Erreur récupération liens: {e}")
        return []

def test_requests_scraper():
    """Test du scraper avec requests/BeautifulSoup"""
    
    try:
        print("🚀 Test du scraper Angers avec requests...")
        
        session = get_session()
        
        # URL de base
        base_url = "https://barreau-angers.org/annuaire-des-avocats/?recherche=&lieu=&domaine="
        
        # Récupérer les liens d'avocats
        all_links = get_lawyer_links_requests(session, base_url)
        
        if not all_links:
            print("❌ Aucun lien d'avocat trouvé")
            return
        
        # Traitement de TOUS les avocats
        test_links = all_links
        print(f"🚀 Production: {len(test_links)} avocats à traiter")
        
        lawyers_data = []
        
        for i, lawyer_url in enumerate(test_links):
            # Progress chaque 25 avocats
            if i % 25 == 0:
                print(f"\n--- {i+1}/{len(test_links)} ({(i+1)/len(test_links)*100:.1f}%) ---")
            
            try:
                response = session.get(lawyer_url, timeout=30)
                response.raise_for_status()
                
                lawyer_data = extract_lawyer_data_from_html(response.content, lawyer_url)
                
                if lawyer_data:
                    lawyers_data.append(lawyer_data)
                    
                    print(f"✅ {lawyer_data.get('nom_complet', 'Nom inconnu')}")
                    print(f"   👤 Prénom: {lawyer_data.get('prenom', 'N/A')}")
                    print(f"   👤 Nom: {lawyer_data.get('nom', 'N/A')}")
                    print(f"   📧 Email: {lawyer_data.get('email', 'N/A')}")
                    print(f"   🏠 Adresse: {lawyer_data.get('adresse', 'N/A')}")
                    print(f"   📅 Inscription: {lawyer_data.get('annee_inscription', 'N/A')}")
                    print(f"   🏢 Structure: {lawyer_data.get('structure', 'N/A')}")
                    print(f"   ⚖️ Spécialisations: {', '.join(lawyer_data.get('specialisations', []))}")
                else:
                    print(f"❌ Échec d'extraction pour: {lawyer_url}")
            
            except Exception as e:
                print(f"❌ Erreur pour {lawyer_url}: {e}")
            
            # Pause respectueuse (plus courte pour production)
            time.sleep(0.5)
            
            # Sauvegarde tous les 100 avocats
            if (i + 1) % 100 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"angers_production_backup_{i+1}_{timestamp}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
                print(f"💾 Sauvegarde: {backup_file}")
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_filename = f"angers_production_COMPLET_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = f"angers_production_COMPLET_{timestamp}.csv"
        if lawyers_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=lawyers_data[0].keys())
                writer.writeheader()
                for lawyer in lawyers_data:
                    row = lawyer.copy()
                    if isinstance(row.get('specialisations'), list):
                        row['specialisations'] = '; '.join(row['specialisations'])
                    writer.writerow(row)
        
        print(f"\n🎯 Test terminé avec succès!")
        print(f"📊 {len(lawyers_data)} avocats traités sur {len(test_links)}")
        print(f"💾 Résultats sauvegardés:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📊 CSV: {csv_filename}")
        print(f"🔗 Total d'avocats disponibles: {len(all_links)}")
        
        return lawyers_data, all_links
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return [], []

def create_production_scraper(all_links):
    """Crée le script de production pour tous les avocats"""
    
    production_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import csv
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Insérer ici toutes les fonctions du script de test...

def scrape_all_lawyers():
    \"\"\"Script de production pour scraper tous les avocats\"\"\"
    
    try:
        print("🚀 Démarrage du scraping complet du barreau d'Angers...")
        
        session = get_session()
        
        # Liens récupérés lors du test
        all_links = """ + json.dumps(all_links, indent=8) + """
        
        print(f"📋 {len(all_links)} avocats à traiter")
        
        lawyers_data = []
        errors = []
        
        for i, lawyer_url in enumerate(all_links):
            print(f"\\n--- {i+1}/{len(all_links)} ---")
            
            try:
                response = session.get(lawyer_url, timeout=30)
                response.raise_for_status()
                
                lawyer_data = extract_lawyer_data_from_html(response.content, lawyer_url)
                
                if lawyer_data:
                    lawyers_data.append(lawyer_data)
                    print(f"✅ {lawyer_data.get('nom_complet', 'Nom inconnu')}")
                else:
                    print(f"❌ Échec d'extraction pour: {lawyer_url}")
                    errors.append(lawyer_url)
            
            except Exception as e:
                print(f"❌ Erreur pour {lawyer_url}: {e}")
                errors.append(lawyer_url)
            
            # Pause respectueuse
            time.sleep(1)
            
            # Sauvegarde intermédiaire tous les 50 avocats
            if (i + 1) % 50 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"angers_backup_{i+1}_{timestamp}.json"
                with open(backup_filename, 'w', encoding='utf-8') as f:
                    json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
                print(f"💾 Sauvegarde intermédiaire: {backup_filename}")
        
        # Sauvegarde finale
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_filename = f"angers_avocats_complet_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = f"angers_avocats_complet_{timestamp}.csv"
        if lawyers_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=lawyers_data[0].keys())
                writer.writeheader()
                for lawyer in lawyers_data:
                    row = lawyer.copy()
                    if isinstance(row.get('specialisations'), list):
                        row['specialisations'] = '; '.join(row['specialisations'])
                    writer.writerow(row)
        
        print(f"\\n🎯 Scraping terminé!")
        print(f"📊 {len(lawyers_data)} avocats traités avec succès")
        print(f"❌ {len(errors)} erreurs")
        print(f"💾 Fichiers créés:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📊 CSV: {csv_filename}")
        
        return lawyers_data
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return []

if __name__ == "__main__":
    scrape_all_lawyers()
"""
    
    with open("angers_production_scraper.py", 'w', encoding='utf-8') as f:
        f.write(production_script)
    
    print(f"📝 Script de production créé: angers_production_scraper.py")

if __name__ == "__main__":
    # Vérifier que BeautifulSoup est installé
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ BeautifulSoup4 non installé. Installation...")
        import subprocess
        subprocess.check_call(["pip3", "install", "beautifulsoup4"])
        from bs4 import BeautifulSoup
    
    # Exécuter le test
    lawyers_data, all_links = test_requests_scraper()
    
    if lawyers_data and all_links:
        create_production_scraper(all_links)