#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper FINAL OPTIMISÉ pour l'annuaire des avocats du barreau de Valenciennes
Site: https://www.avocats-valenciennes.fr/annuaire-avocats-du-barreau.htm

Version optimisée qui extrait correctement les noms et prénoms depuis les URLs
"""

import time
import json
import csv
import re
import html
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, unquote
import requests
from bs4 import BeautifulSoup
import sys

def setup_driver(headless=True):
    """Configure le driver Chrome avec les bonnes options."""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(30)
    
    return driver

def decode_email(encoded_email):
    """Décode les emails encodés en HTML entities."""
    if not encoded_email:
        return None
    
    # Décoder les entités HTML numériques (%xx)
    decoded = unquote(encoded_email)
    
    # Décoder les entités HTML standard
    decoded = html.unescape(decoded)
    
    # Nettoyer les espaces
    decoded = decoded.strip()
    
    # Valider le format email
    if '@' in decoded and '.' in decoded:
        return decoded
    
    return encoded_email  # Retourner l'original si le décodage échoue

def extract_lawyer_links(base_url):
    """Extrait tous les liens uniques vers les fiches d'avocats."""
    print("\n=== EXTRACTION DES LIENS VERS LES FICHES ===\n")
    
    try:
        response = requests.get(base_url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trouver tous les liens vers les fiches
        links = []
        seen_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'page/annuaire' in href and '#' not in href:
                # Construire l'URL complète
                full_url = urljoin(base_url, href)
                
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    
                    # Extraire le nom depuis l'URL - VERSION OPTIMISÉE
                    name_match = re.search(r'/([^/]+)\.htm$', href)
                    if name_match:
                        name_slug = name_match.group(1)
                        
                        # Extraction optimisée du nom depuis l'URL
                        # Format attendu: "monsieur-prenom-nom-numero" ou "madame-prenom-nom-numero"
                        name_clean = re.sub(r'^(maitre|madame|monsieur|mme|me|m)-', '', name_slug, flags=re.IGNORECASE)
                        
                        # Supprimer le numéro à la fin
                        name_clean = re.sub(r'-\d+$', '', name_clean)
                        
                        # Convertir les tirets en espaces et mettre en forme
                        name_parts = [part.title() for part in name_clean.split('-') if part]
                        
                        # Reconstituer prénom et nom
                        if len(name_parts) >= 2:
                            prenom = name_parts[0]
                            nom = ' '.join(name_parts[1:])
                            nom_complet = f"{prenom} {nom}"
                        elif len(name_parts) == 1:
                            prenom = name_parts[0]
                            nom = ""
                            nom_complet = prenom
                        else:
                            prenom = ""
                            nom = ""
                            nom_complet = name_slug.replace('-', ' ').title()
                        
                        links.append({
                            'url': full_url,
                            'slug': name_slug,
                            'prenom': prenom,
                            'nom': nom.upper() if nom else "",
                            'nom_complet': nom_complet
                        })
        
        # Éliminer les doublons par URL
        unique_links = []
        seen_urls = set()
        for link in links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        print(f"✓ {len(unique_links)} fiches d'avocats trouvées")
        if unique_links:
            print(f"\nPremier avocat: {unique_links[0]['nom_complet']}")
            print(f"Dernier avocat: {unique_links[-1]['nom_complet']}")
        
        return unique_links
        
    except Exception as e:
        print(f"Erreur lors de l'extraction des liens: {e}")
        return []

def extract_lawyer_details(driver, lawyer_info, retry_count=3):
    """Extrait les détails d'un avocat depuis sa fiche individuelle avec retry."""
    details = {
        'url_fiche': lawyer_info['url'],
        'slug': lawyer_info['slug'],
        'prenom': lawyer_info['prenom'],
        'nom': lawyer_info['nom'],
        'nom_complet': lawyer_info['nom_complet']
    }
    
    for attempt in range(retry_count):
        try:
            driver.get(lawyer_info['url'])
            
            # Attendre que la page soit chargée
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(1)  # Petite pause pour s'assurer que tout est chargé
            
            # Extraire le contenu principal
            page_html = driver.page_source
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # 1. Email (avec décodage)
            try:
                # Méthode 1: liens mailto
                mailto = soup.find('a', href=re.compile(r'^mailto:'))
                if mailto:
                    email = mailto['href'].replace('mailto:', '').strip()
                    email = decode_email(email)
                    details['email'] = email
                else:
                    # Méthode 2: chercher dans le texte
                    text_content = soup.get_text()
                    # Pattern pour email encodé ou normal
                    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
                    emails = re.findall(email_pattern, text_content)
                    if emails:
                        details['email'] = decode_email(emails[0])
            except:
                pass
            
            # 2. Téléphone
            try:
                # Méthode 1: liens tel
                tel_link = soup.find('a', href=re.compile(r'^tel:'))
                if tel_link:
                    tel = tel_link['href'].replace('tel:', '').strip()
                    # Normaliser le format
                    tel = re.sub(r'[\s.-]', '', tel)
                    tel = re.sub(r'^(\+33|0033)', '0', tel)
                    if len(tel) == 10:
                        tel = ' '.join([tel[i:i+2] for i in range(0, 10, 2)])
                    details['telephone'] = tel
                else:
                    # Méthode 2: chercher dans le texte
                    text_content = soup.get_text()
                    tel_pattern = r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}'
                    tels = re.findall(tel_pattern, text_content)
                    if tels:
                        tel = re.sub(r'[\s.-]', '', tels[0])
                        tel = re.sub(r'^(\+33|0033)', '0', tel)
                        if len(tel) == 10:
                            tel = ' '.join([tel[i:i+2] for i in range(0, 10, 2)])
                        details['telephone'] = tel
            except:
                pass
            
            # 3. Fax
            try:
                text_content = soup.get_text()
                fax_patterns = [
                    r'(?:Fax|Télécopie|Télécopieur)\s*:?\s*((?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4})',
                    r'Fax\s*:\s*([0-9\s.-]{10,})'
                ]
                
                for pattern in fax_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    if matches:
                        fax = re.sub(r'[\s.-]', '', matches[0])
                        fax = re.sub(r'^(\+33|0033)', '0', fax)
                        if len(fax) == 10:
                            fax = ' '.join([fax[i:i+2] for i in range(0, 10, 2)])
                            details['fax'] = fax
                        break
            except:
                pass
                
            # 4. Adresse
            try:
                text_content = soup.get_text()
                # Pattern pour adresse avec code postal
                adresse_pattern = r'([0-9].*?(?:[0-9]{5})\s+[A-Z\s]+)'
                addresses = re.findall(adresse_pattern, text_content)
                if addresses:
                    adresse = addresses[0].strip()
                    details['adresse'] = adresse
                    
                    # Extraire code postal et ville
                    cp_ville = re.search(r'([0-9]{5})\s+([A-Z\s]+)', adresse)
                    if cp_ville:
                        details['code_postal'] = cp_ville.group(1)
                        ville = cp_ville.group(2).strip()
                        # Nettoyer la ville (supprimer les "Tél", etc.)
                        ville = re.sub(r'\s+(Tél|Tel|Fax).*$', '', ville).strip()
                        details['ville'] = ville
            except:
                pass
            
            # 5. Année de serment
            try:
                text_content = soup.get_text()
                serment_patterns = [
                    r'(?:serment|prestation)\s*:?\s*([0-9]{4})',
                    r'([0-9]{4})\s*(?:serment|prestation)',
                    r'inscrit[e]?\s+(?:au\s+barreau\s+)?(?:en\s+)?([0-9]{4})',
                    r'([0-9]{4})\s*inscription'
                ]
                
                for pattern in serment_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    if matches:
                        year = int(matches[0])
                        if 1950 <= year <= 2030:  # Validation
                            details['annee_serment'] = year
                            break
            except:
                pass
            
            # 6. Spécialités/Domaines d'activité
            try:
                text_content = soup.get_text()
                
                # Chercher les sections spécialisations
                specialites_keywords = [
                    'Spécialité', 'Spécialités', 'Domaines', 'Compétences', 
                    'Activités', 'Matières', 'Équipe'
                ]
                
                specialites = []
                for keyword in specialites_keywords:
                    pattern = f'{keyword}[^\\n]*:?\\s*([^\\n]+)'
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    specialites.extend(matches)
                
                if specialites:
                    # Nettoyer et limiter
                    clean_specialites = []
                    for spec in specialites[:3]:  # Limiter à 3
                        spec_clean = re.sub(r'^(Maître|Me\.?|Monsieur|Madame)\s+', '', spec.strip())
                        if spec_clean and len(spec_clean) > 3:
                            clean_specialites.append(spec_clean)
                    
                    if clean_specialites:
                        details['specialites'] = ' | '.join(clean_specialites)
            except:
                pass
            
            # 7. Cabinet/Structure
            try:
                text_content = soup.get_text()
                cabinet_keywords = ['Cabinet', 'Société', 'SCP', 'SELARL', 'Équipe']
                
                for keyword in cabinet_keywords:
                    pattern = f'{keyword}[^\\n]*([^\\n]+)'
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    if matches and matches[0].strip():
                        details['cabinet'] = matches[0].strip()[:100]  # Limiter la longueur
                        break
            except:
                pass
            
            # 8. Site web
            try:
                site_links = soup.find_all('a', href=re.compile(r'https?://'))
                for link in site_links:
                    href = link['href']
                    # Ignorer les liens vers le site du barreau et les mails
                    if ('avocats-valenciennes.fr' not in href and 
                        'mailto:' not in href and 
                        'catalogue-avocats.azko.fr' not in href):
                        details['site_web'] = href
                        break
            except:
                pass
            
            return details
            
        except Exception as e:
            print(f"Erreur tentative {attempt + 1}: {e}")
            if attempt < retry_count - 1:
                time.sleep(2)  # Attendre avant retry
                continue
            else:
                print(f" ❌ ÉCHEC")
                return details

def main():
    """Fonction principale."""
    base_url = "https://www.avocats-valenciennes.fr/annuaire-avocats-du-barreau.htm"
    
    print("=" * 80)
    print("SCRAPER FINAL OPTIMISÉ - BARREAU DE VALENCIENNES")
    print("=" * 80)
    
    # Mode test si argument fourni
    test_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'test'
    
    # 1. Extraire les liens
    lawyer_links = extract_lawyer_links(base_url)
    if not lawyer_links:
        print("❌ Aucun lien trouvé")
        return
    
    # Limitation pour le test
    if test_mode:
        lawyer_links = lawyer_links[:20]
        print(f"\n⚠ MODE TEST : Limitation à {len(lawyer_links)} avocats")
    
    # 2. Configurer le driver
    driver = setup_driver(headless=True)
    
    try:
        print(f"\n=== EXTRACTION DES DÉTAILS DES AVOCATS ===")
        print(f"Nombre d'avocats à traiter: {len(lawyer_links)}")
        
        lawyers_data = []
        errors = []
        
        for idx, lawyer_info in enumerate(lawyer_links, 1):
            print(f"{idx}/{len(lawyer_links)} - {lawyer_info['nom_complet']}...", end='')
            
            details = extract_lawyer_details(driver, lawyer_info)
            
            # Vérifier qu'on a les infos essentielles
            if details.get('email') or details.get('telephone'):
                status_items = []
                if details.get('email'):
                    status_items.append('Email')
                if details.get('telephone'):
                    status_items.append('Tél')
                if details.get('adresse'):
                    status_items.append('Adresse')
                
                print(f" ✓ ({', '.join(status_items)})")
                lawyers_data.append(details)
            else:
                print(f" ⚠ Informations limitées")
                lawyers_data.append(details)
            
            # Pause entre requêtes
            time.sleep(0.5)
        
        # 3. Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_suffix = "_TEST" if test_mode else "_COMPLET"
        
        print(f"\n=== SAUVEGARDE DES RÉSULTATS FINAUX ===\n")
        
        # JSON
        json_filename = f"VALENCIENNES{mode_suffix}_{len(lawyers_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Données JSON sauvegardées: {json_filename}")
        
        # CSV
        csv_filename = f"VALENCIENNES{mode_suffix}_{len(lawyers_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
            if lawyers_data:
                fieldnames = [
                    'nom', 'prenom', 'nom_complet', 'email', 'telephone', 'fax',
                    'adresse', 'code_postal', 'ville', 'annee_serment', 'specialites',
                    'cabinet', 'site_web', 'langues', 'url_fiche', 'slug'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                writer.writerows(lawyers_data)
        print(f"✓ Données CSV sauvegardées: {csv_filename}")
        
        # Liste des emails
        emails = []
        for lawyer in lawyers_data:
            if lawyer.get('email'):
                # Gérer les emails multiples
                email_str = lawyer['email']
                if ';' in email_str:
                    emails.extend([e.strip() for e in email_str.split(';')])
                else:
                    emails.append(email_str)
        
        unique_emails = list(set(emails))
        email_filename = f"VALENCIENNES_EMAILS_UNIQUES_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as f:
            for email in sorted(unique_emails):
                f.write(f"{email}\n")
        print(f"✓ {len(unique_emails)} emails uniques sauvegardés: {email_filename}")
        
        # Rapport
        rapport_filename = f"VALENCIENNES_RAPPORT_COMPLET_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as f:
            f.write("RAPPORT D'EXTRACTION - BARREAU DE VALENCIENNES\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Site source: {base_url}\n\n")
            
            f.write("STATISTIQUES DÉTAILLÉES:\n")
            f.write("=" * 80 + "\n")
            f.write(f"Nombre total d'avocats: {len(lawyers_data)}\n")
            f.write(f"Avocats avec email: {len([l for l in lawyers_data if l.get('email')])} ({len([l for l in lawyers_data if l.get('email')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec téléphone: {len([l for l in lawyers_data if l.get('telephone')])} ({len([l for l in lawyers_data if l.get('telephone')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec fax: {len([l for l in lawyers_data if l.get('fax')])} ({len([l for l in lawyers_data if l.get('fax')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec adresse: {len([l for l in lawyers_data if l.get('adresse')])} ({len([l for l in lawyers_data if l.get('adresse')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec code postal: {len([l for l in lawyers_data if l.get('code_postal')])} ({len([l for l in lawyers_data if l.get('code_postal')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec ville: {len([l for l in lawyers_data if l.get('ville')])} ({len([l for l in lawyers_data if l.get('ville')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec année de serment: {len([l for l in lawyers_data if l.get('annee_serment')])} ({len([l for l in lawyers_data if l.get('annee_serment')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec spécialités: {len([l for l in lawyers_data if l.get('specialites')])} ({len([l for l in lawyers_data if l.get('specialites')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec cabinet: {len([l for l in lawyers_data if l.get('cabinet')])} ({len([l for l in lawyers_data if l.get('cabinet')])/len(lawyers_data)*100:.0f}%)\n")
            f.write(f"Avocats avec site web: {len([l for l in lawyers_data if l.get('site_web')])} ({len([l for l in lawyers_data if l.get('site_web')])/len(lawyers_data)*100:.0f}%)\n")
            
            if [l for l in lawyers_data if l.get('annee_serment')]:
                years = [l['annee_serment'] for l in lawyers_data if l.get('annee_serment')]
                f.write(f"\nDistribution des années de serment:\n")
                f.write(f"  Plus ancien: {min(years)}\n")
                f.write(f"  Plus récent: {max(years)}\n")
                f.write(f"  Médiane: {sorted(years)[len(years)//2]}\n")
            
            f.write(f"\n" + "=" * 80 + "\n")
            f.write(f"LISTE DÉTAILLÉE DES AVOCATS:\n\n")
            
            for i, lawyer in enumerate(lawyers_data, 1):
                nom = lawyer.get('nom', '').upper()
                prenom = lawyer.get('prenom', '')
                nom_complet = lawyer.get('nom_complet', 'N/A')
                
                f.write(f"{i}. {nom} {prenom} - {nom_complet}\n")
                f.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                f.write(f"   Tél: {lawyer.get('telephone', 'N/A')}\n")
                if lawyer.get('fax'):
                    f.write(f"   Fax: {lawyer.get('fax')}\n")
                f.write(f"   Adresse: {lawyer.get('adresse', 'N/A')}\n")
                if lawyer.get('annee_serment'):
                    f.write(f"   Serment: {lawyer.get('annee_serment')}\n")
                if lawyer.get('specialites'):
                    f.write(f"   Spécialités: {lawyer.get('specialites')}\n")
                if lawyer.get('cabinet'):
                    f.write(f"   Cabinet: {lawyer.get('cabinet')}\n")
                if lawyer.get('site_web'):
                    f.write(f"   Site: {lawyer.get('site_web')}\n")
                f.write(f"\n")
        
        print(f"✓ Rapport détaillé sauvegardé: {rapport_filename}")
        
        # Statistiques finales
        print(f"\n=== STATISTIQUES FINALES ===")
        print(f"Total avocats traités: {len(lawyers_data)}")
        print(f"Avec email: {len([l for l in lawyers_data if l.get('email')])} ({len([l for l in lawyers_data if l.get('email')])/len(lawyers_data)*100:.0f}%)")
        print(f"Avec téléphone: {len([l for l in lawyers_data if l.get('telephone')])} ({len([l for l in lawyers_data if l.get('telephone')])/len(lawyers_data)*100:.0f}%)")
        print(f"Avec adresse: {len([l for l in lawyers_data if l.get('adresse')])} ({len([l for l in lawyers_data if l.get('adresse')])/len(lawyers_data)*100:.0f}%)")
        print(f"Avec année de serment: {len([l for l in lawyers_data if l.get('annee_serment')])} ({len([l for l in lawyers_data if l.get('annee_serment')])/len(lawyers_data)*100:.0f}%)")
        
        print(f"\n✓ Scraper terminé avec succès.")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()