#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import csv
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

def scrape_angers_complete():
    """Scraper de production optimisé pour le barreau d'Angers"""
    
    print("🚀 SCRAPING COMPLET - Barreau d'Angers")
    print("⏰ Estimation: 5-7 minutes pour 455 avocats")
    
    # Configuration session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    start_time = time.time()
    
    try:
        # Étape 1: Récupération des liens
        print("📋 1/3 - Récupération de la liste des avocats...")
        
        response = session.get("https://barreau-angers.org/annuaire-des-avocats/", timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire tous les liens d'avocats
        lawyer_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/avocat/' in href:
                if href.startswith('/'):
                    href = f"https://barreau-angers.org{href}"
                lawyer_links.append(href)
        
        # Dédupliquer
        lawyer_links = list(set(lawyer_links))
        print(f"✅ {len(lawyer_links)} avocats identifiés")
        
        # Étape 2: Extraction des données
        print("📄 2/3 - Extraction des données...")
        
        lawyers_data = []
        errors = []
        
        for i, url in enumerate(lawyer_links):
            # Progress
            if i % 25 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta_seconds = (len(lawyer_links) - i) / rate if rate > 0 else 0
                print(f"⏳ {i+1}/{len(lawyer_links)} ({(i+1)/len(lawyer_links)*100:.1f}%) - ETA: {eta_seconds/60:.1f}min")
            
            try:
                # Requête page avocat
                resp = session.get(url, timeout=10)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.content, 'html.parser')
                text_content = soup.get_text()
                
                # Extraction des données
                lawyer = {'url': url, 'extraction_date': datetime.now().isoformat()}
                
                # 1. Nom complet
                title_tag = soup.find('h1')
                if title_tag:
                    full_name = title_tag.get_text().strip()
                    full_name = re.sub(r'^(Me\\.?\\s+|Maître\\s+)', '', full_name, flags=re.IGNORECASE).strip()
                    lawyer['nom_complet'] = full_name
                    
                    # Séparer prénom/nom
                    parts = full_name.split()
                    if len(parts) >= 2:
                        lawyer['prenom'] = parts[0]
                        lawyer['nom'] = ' '.join(parts[1:])
                    else:
                        lawyer['prenom'] = ""
                        lawyer['nom'] = full_name
                else:
                    lawyer['nom_complet'] = "Non trouvé"
                    lawyer['prenom'] = ""
                    lawyer['nom'] = ""
                
                # 2. Email
                email = None
                
                # Recherche mailto
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
                if mailto_links:
                    email = mailto_links[0]['href'].replace('mailto:', '').strip()
                
                # Recherche regex dans le texte
                if not email:
                    email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b'
                    matches = re.findall(email_pattern, text_content)
                    if matches:
                        email = matches[0]
                
                lawyer['email'] = email if email else "Non trouvé"
                
                # 3. Adresse
                address_pattern = r'[^\\n]*49\\d{3}[^\\n]*'
                address_matches = re.findall(address_pattern, text_content)
                if address_matches:
                    address = address_matches[0].strip()
                    address = re.sub(r'\\s+', ' ', address)
                    lawyer['adresse'] = address
                else:
                    lawyer['adresse'] = "Non trouvé"
                
                # 4. Année d'inscription
                year_patterns = [
                    r'inscrit.*?(\\d{4})',
                    r'inscription.*?(\\d{4})',
                    r'barreau.*?(\\d{4})',
                    r'asserment.*?(\\d{4})'
                ]
                
                year = None
                for pattern in year_patterns:
                    matches = re.findall(pattern, text_content.lower())
                    for match in matches:
                        y = int(match)
                        if 1970 <= y <= 2024:
                            year = str(y)
                            break
                    if year:
                        break
                
                lawyer['annee_inscription'] = year if year else "Non trouvé"
                
                # 5. Spécialisations
                specializations = []
                domains = [
                    'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
                    'droit de la famille', 'droit immobilier', 'droit des affaires',
                    'droit public', 'droit administratif', 'droit fiscal', 'droit social'
                ]
                
                text_lower = text_content.lower()
                for domain in domains:
                    if domain in text_lower:
                        specializations.append(domain.title())
                
                lawyer['specialisations'] = specializations if specializations else ["Non trouvé"]
                
                # 6. Structure
                if 'cabinet' in text_lower:
                    lawyer['structure'] = "Cabinet"
                elif any(word in text_lower for word in ['société', 'scpa', 'scp']):
                    lawyer['structure'] = "Société d'avocats"
                else:
                    lawyer['structure'] = "Exercice individuel"
                
                lawyers_data.append(lawyer)
                
            except Exception as e:
                print(f"\\n❌ Erreur {url}: {e}")
                errors.append(url)
            
            # Pause respectueuse
            time.sleep(0.3)
            
            # Sauvegarde intermédiaire tous les 100
            if (i + 1) % 100 == 0:
                backup_file = f"angers_backup_auto_{i+1}_{datetime.now().strftime('%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
                print(f"\\n💾 Sauvegarde: {backup_file}")
        
        print(f"\\n🎯 3/3 - Finalisation...")
        
        # Sauvegarde finale
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f"angers_avocats_COMPLET_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_file = f"angers_avocats_COMPLET_{timestamp}.csv"
        fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'adresse', 
                     'annee_inscription', 'specialisations', 'structure', 'url']
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for lawyer in lawyers_data:
                row = {k: v for k, v in lawyer.items() if k in fieldnames}
                if isinstance(row.get('specialisations'), list):
                    row['specialisations'] = '; '.join(row['specialisations'])
                writer.writerow(row)
        
        # Statistiques finales
        total_time = time.time() - start_time
        emails_found = sum(1 for l in lawyers_data if l.get('email') != "Non trouvé")
        addresses_found = sum(1 for l in lawyers_data if l.get('adresse') != "Non trouvé")
        years_found = sum(1 for l in lawyers_data if l.get('annee_inscription') != "Non trouvé")
        specs_found = sum(1 for l in lawyers_data if l.get('specialisations') != ["Non trouvé"])
        
        print(f"\\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS !")
        print(f"="*60)
        print(f"📊 RÉSULTATS :")
        print(f"   ✅ Avocats traités: {len(lawyers_data)}/{len(lawyer_links)}")
        print(f"   ❌ Erreurs: {len(errors)}")
        print(f"   ⏰ Temps total: {total_time/60:.1f} minutes")
        print(f"   🚀 Vitesse: {len(lawyers_data)/(total_time/60):.1f} avocats/minute")
        print(f"")
        print(f"📈 TAUX DE SUCCÈS :")
        print(f"   📧 Emails: {emails_found}/{len(lawyers_data)} ({emails_found/len(lawyers_data)*100:.1f}%)")
        print(f"   🏠 Adresses: {addresses_found}/{len(lawyers_data)} ({addresses_found/len(lawyers_data)*100:.1f}%)")
        print(f"   📅 Années: {years_found}/{len(lawyers_data)} ({years_found/len(lawyers_data)*100:.1f}%)")
        print(f"   ⚖️ Spécialisations: {specs_found}/{len(lawyers_data)} ({specs_found/len(lawyers_data)*100:.1f}%)")
        print(f"")
        print(f"💾 FICHIERS CRÉÉS :")
        print(f"   📄 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")
        print(f"="*60)
        
        return lawyers_data
        
    except Exception as e:
        print(f"❌ ERREUR GÉNÉRALE: {e}")
        return []

if __name__ == "__main__":
    scrape_angers_complete()