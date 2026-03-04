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

def extract_lawyer_data_enhanced(html_content, url):
    """Version améliorée de l'extraction des données"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        
        lawyer_data = {
            'url': url,
            'extraction_date': datetime.now().isoformat()
        }
        
        # Nom complet - extraction améliorée
        title_selectors = ['h1.entry-title', 'h1', '.entry-title', '.lawyer-name', '.avocat-name']
        full_name = None
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                full_name = element.get_text().strip()
                break
        
        if full_name:
            # Nettoyer le nom
            clean_name = re.sub(r'Me\.?\s+|Maître\s+', '', full_name).strip()
            lawyer_data['nom_complet'] = clean_name
            
            # Séparer prénom/nom
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
        
        # Email - extraction améliorée
        email = None
        
        # 1. Chercher les liens mailto
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if mailto_links:
            email = mailto_links[0]['href'].replace('mailto:', '').strip()
        
        # 2. Chercher dans les attributs
        if not email:
            email_elements = soup.find_all(attrs={'href': re.compile(r'mailto:')})
            if email_elements:
                href = email_elements[0].get('href', '')
                email = href.replace('mailto:', '').strip()
        
        # 3. Chercher dans le texte avec regex améliorée
        if not email:
            email_pattern = r'\b[A-Za-z0-9][\w\.-]*[A-Za-z0-9]@[A-Za-z0-9][\w\.-]*[A-Za-z0-9]\.[A-Za-z]{2,4}\b'
            email_matches = re.findall(email_pattern, text_content)
            if email_matches:
                # Prendre le premier email qui semble valide
                for match in email_matches:
                    if '.' in match and len(match) > 5:
                        email = match
                        break
        
        lawyer_data['email'] = email if email else "Non trouvé"
        
        # Adresse - extraction améliorée avec nettoyage
        address = None
        
        # Chercher les codes postaux 49xxx spécifiquement
        address_patterns = [
            r'[^\n\r]*49\d{3}[^\n\r]*',  # Ligne contenant code postal
            r'\d+[^,\n]*,\s*[^,\n]*49\d{3}[^,\n]*',  # Adresse avec CP
            r'[^\n\r]*rue[^\n\r]*49\d{3}[^\n\r]*',  # Rue avec CP
            r'[^\n\r]*avenue[^\n\r]*49\d{3}[^\n\r]*'  # Avenue avec CP
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                address = matches[0].strip()
                # Nettoyer l'adresse
                address = re.sub(r'\s+', ' ', address)
                address = re.sub(r'^[\\n\\r\\t\\s]+|[\\n\\r\\t\\s]+$', '', address)
                break
        
        lawyer_data['adresse'] = address if address else "Non trouvé"
        
        # Année d'inscription - patterns améliorés
        year = None
        text_lower = text_content.lower()
        
        inscription_patterns = [
            r'inscrit(?:e?)?\s+(?:au\s+barreau\s+)?(?:d[\'e]\s+\w+\s+)?(?:depuis\s+|en\s+)?(\d{4})',
            r'inscription\s+(?:au\s+barreau\s+)?(?:en\s+)?(\d{4})',
            r'asserment(?:ation|é)?\s+(?:en\s+)?(\d{4})',
            r'barreau\s+(?:depuis\s+|en\s+)?(\d{4})',
            r'avocat\s+depuis\s+(\d{4})'
        ]
        
        for pattern in inscription_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                potential_year = int(match)
                if 1970 <= potential_year <= 2024:
                    year = str(potential_year)
                    break
            if year:
                break
        
        lawyer_data['annee_inscription'] = year if year else "Non trouvé"
        
        # Spécialisations - extraction très améliorée
        specializations = []
        
        # 1. Domaines juridiques standards
        law_domains = [
            'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
            'droit de la famille', 'droit immobilier', 'droit des affaires',
            'droit public', 'droit administratif', 'droit fiscal', 'droit social',
            'droit bancaire', 'droit des sociétés', 'droit international',
            'droit de la construction', 'droit de l\'environnement', 'droit maritime',
            'droit de la santé', 'droit des assurances', 'droit des nouvelles technologies',
            'droit de la propriété intellectuelle', 'droit de l\'urbanisme'
        ]
        
        for domain in law_domains:
            if domain in text_lower:
                specializations.append(domain.title())
        
        # 2. Chercher les éléments avec des classes spécifiques
        spec_selectors = [
            '.domaine', '.specialite', '.competence', '.practice-area',
            '.domain', '.specialty', '[class*="domain"]', '[class*="special"]'
        ]
        
        for selector in spec_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) < 100 and 'droit' in text.lower():
                    specializations.append(text.title())
        
        # 3. Chercher dans les listes
        list_items = soup.find_all(['li', 'p'])
        for item in list_items:
            text = item.get_text().strip()
            if (text and len(text) < 80 and 
                ('droit' in text.lower() or 'contentieux' in text.lower()) and
                text not in specializations):
                specializations.append(text.title())
        
        # 4. Patterns de spécialisation dans le texte
        spec_patterns = [
            r'spécialisé(?:e)?\s+en\s+([^.\n]{5,50})',
            r'domaines?\s+de\s+compétences?\s*:\s*([^.\n]{10,100})',
            r'domaines?\s+d\'intervention\s*:\s*([^.\n]{10,100})',
            r'pratique\s+du\s+([^.\n]{5,50})'
        ]
        
        for pattern in spec_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if 'droit' in match:
                    specializations.append(match.strip().title())
        
        # Nettoyer et dédupliquer
        clean_specializations = []
        for spec in specializations:
            spec_clean = re.sub(r'\s+', ' ', spec.strip())
            if (spec_clean not in clean_specializations and 
                len(spec_clean) > 3 and 
                len(spec_clean) < 100):
                clean_specializations.append(spec_clean)
        
        lawyer_data['specialisations'] = clean_specializations if clean_specializations else ["Non trouvé"]
        
        # Structure/Cabinet - détection améliorée
        structure = "Exercice individuel"
        
        structure_patterns = [
            (r'cabinet\s+([^.\n]{5,50})', 'Cabinet'),
            (r'société\s+d\'avocats\s+([^.\n]{5,50})', 'Société d\'avocats'),
            (r'scpa\s+([^.\n]{5,50})', 'SCPA'),
            (r'scp\s+([^.\n]{5,50})', 'SCP'),
            (r'selarl\s+([^.\n]{5,50})', 'SELARL')
        ]
        
        for pattern, prefix in structure_patterns:
            match = re.search(pattern, text_lower)
            if match:
                structure_name = match.group(1).strip().title()
                structure = f"{prefix} {structure_name}"
                break
        
        # Vérifications simples
        if 'cabinet' in text_lower and structure == "Exercice individuel":
            structure = "Cabinet"
        elif any(word in text_lower for word in ['société', 'scpa', 'scp', 'selarl']):
            structure = "Société d'avocats"
        
        lawyer_data['structure'] = structure
        
        return lawyer_data
        
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
        return None

def scrape_all_angers_lawyers():
    """Script principal pour scraper tous les avocats"""
    
    try:
        print("🚀 Scraping complet du barreau d'Angers...")
        print("⏰ Estimation: environ 8-10 minutes pour 456 avocats")
        
        session = get_session()
        
        # Récupérer les liens d'avocats
        print("📋 Récupération de la liste des avocats...")
        base_url = "https://barreau-angers.org/annuaire-des-avocats/?recherche=&lieu=&domaine="
        
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire tous les liens
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/avocat/' in href:
                if href.startswith('/'):
                    href = f"https://barreau-angers.org{href}"
                elif not href.startswith('http'):
                    href = f"https://barreau-angers.org/{href}"
                links.add(href)
        
        all_links = list(links)
        print(f"✅ {len(all_links)} avocats à traiter")
        
        # Traitement de tous les avocats
        lawyers_data = []
        errors = []
        start_time = time.time()
        
        for i, lawyer_url in enumerate(all_links):
            if i % 50 == 0:
                elapsed = time.time() - start_time
                estimated_total = (elapsed / (i + 1)) * len(all_links) if i > 0 else 0
                print(f"\\n⏳ Progression: {i}/{len(all_links)} - Temps estimé restant: {(estimated_total - elapsed)/60:.1f}min")
            
            print(f"\\r📄 {i+1}/{len(all_links)}: {lawyer_url.split('/')[-2] if lawyer_url.split('/')[-2] else 'processing'}...", end='')
            
            try:
                response = session.get(lawyer_url, timeout=30)
                response.raise_for_status()
                
                lawyer_data = extract_lawyer_data_enhanced(response.content, lawyer_url)
                
                if lawyer_data:
                    lawyers_data.append(lawyer_data)
                else:
                    errors.append(lawyer_url)
            
            except Exception as e:
                print(f"\\n❌ Erreur {lawyer_url}: {e}")
                errors.append(lawyer_url)
            
            # Pause respectueuse
            time.sleep(1)
            
            # Sauvegarde intermédiaire tous les 100 avocats
            if (i + 1) % 100 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"angers_backup_{i+1}_{timestamp}.json"
                with open(backup_filename, 'w', encoding='utf-8') as f:
                    json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
                print(f"\\n💾 Sauvegarde: {backup_filename}")
        
        print("\\n\\n🎯 Traitement terminé!")
        
        # Sauvegarde finale
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_filename = f"angers_avocats_complet_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = f"angers_avocats_complet_{timestamp}.csv"
        if lawyers_data:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'adresse', 
                         'annee_inscription', 'specialisations', 'structure', 'url', 'extraction_date']
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in lawyers_data:
                    row = lawyer.copy()
                    if isinstance(row.get('specialisations'), list):
                        row['specialisations'] = '; '.join(row['specialisations'])
                    writer.writerow(row)
        
        # Rapport final
        total_time = time.time() - start_time
        print(f"📊 RÉSULTATS FINAUX:")
        print(f"   ✅ {len(lawyers_data)} avocats traités avec succès")
        print(f"   ❌ {len(errors)} erreurs")
        print(f"   ⏰ Temps total: {total_time/60:.1f} minutes")
        print(f"   📄 Fichier JSON: {json_filename}")
        print(f"   📊 Fichier CSV: {csv_filename}")
        
        # Statistiques
        emails_found = sum(1 for lawyer in lawyers_data if lawyer.get('email') != "Non trouvé")
        years_found = sum(1 for lawyer in lawyers_data if lawyer.get('annee_inscription') != "Non trouvé")
        specs_found = sum(1 for lawyer in lawyers_data if lawyer.get('specialisations') != ["Non trouvé"])
        
        print(f"\\n📈 STATISTIQUES:")
        print(f"   📧 Emails trouvés: {emails_found}/{len(lawyers_data)} ({emails_found/len(lawyers_data)*100:.1f}%)")
        print(f"   📅 Années d'inscription: {years_found}/{len(lawyers_data)} ({years_found/len(lawyers_data)*100:.1f}%)")
        print(f"   ⚖️ Spécialisations trouvées: {specs_found}/{len(lawyers_data)} ({specs_found/len(lawyers_data)*100:.1f}%)")
        
        return lawyers_data
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return []

if __name__ == "__main__":
    # Vérifier BeautifulSoup
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installation de BeautifulSoup4...")
        import subprocess
        subprocess.check_call(["pip3", "install", "beautifulsoup4"])
    
    # Démarrer le scraping
    scrape_all_angers_lawyers()