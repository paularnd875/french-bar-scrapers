#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU AIX-EN-PROVENCE - VERSION TEST AMÉLIORÉE
========================================================

Test pour ~5 avocats avec extraction des détails complets.
Extraction précise selon les sélecteurs fournis :
- Email dans : <a class="hoverund lh1" href="mailto:...">
- Date serment dans : <h3 class="mb-5"><strong>...A prêté serment le...</strong>
- Adresse dans : <p class="noir400 f14"><i class="fa-location-dot">...

Auteur: Assistant IA
Date: 2026-02-24
URL: https://barreauaix.com/grand-public/annuaire/
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

def setup_driver(headless=True):
    """Configuration du driver Chrome optimisée"""
    print("🚀 Configuration du driver Chrome...")
    
    options = Options()
    if headless:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Désactiver les images pour plus de rapidité
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def accept_cookies(driver):
    """Gestion des cookies du site"""
    print("🍪 Gestion des cookies...")
    
    try:
        cookie_selectors = [
            ".borlabs-cookie-btn-accept-all",
            "#BorlabsCookieBoxBtnAcceptAll",
            "[data-cookie-accept-all]",
            "button[class*='cookie'][class*='accept']",
            "button[class*='accept'][class*='all']"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                cookie_btn.click()
                print(f"✅ Cookies acceptés via : {selector}")
                time.sleep(2)
                return True
            except:
                continue
                
        print("ℹ️ Aucun bandeau de cookies détecté")
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur cookies : {e}")
        return True

def parse_lawyer_name(full_name):
    """Séparation prénom/nom améliorée"""
    if not full_name:
        return "", ""
    
    name_clean = full_name.strip()
    parts = name_clean.split()
    
    if len(parts) == 1:
        return "", parts[0]
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Logique pour noms composés
        if "-" in name_clean:
            # Si trait d'union, analyser où il se trouve
            for i, part in enumerate(parts):
                if "-" in part and i < len(parts) - 1:
                    # Trait d'union probablement dans le nom
                    prenom = " ".join(parts[:i])
                    nom = " ".join(parts[i:])
                    return prenom, nom
        
        # Par défaut : dernier mot = nom
        prenom = " ".join(parts[:-1])
        nom = parts[-1]
        return prenom, nom

def extract_facet_wp_data(driver):
    """Extraction des données FacetWP"""
    print("📊 Extraction des données FacetWP...")
    
    try:
        script = """
        try {
            if (typeof FWP !== 'undefined' && FWP.settings && FWP.settings.leafletMap && FWP.settings.leafletMap.locations) {
                return FWP.settings.leafletMap.locations;
            }
            return null;
        } catch (e) {
            return null;
        }
        """
        
        data = driver.execute_script(script)
        
        if data and len(data) > 0:
            print(f"✅ Données FacetWP trouvées : {len(data)} avocats")
            return data
        else:
            print("❌ Données FacetWP non trouvées")
            return None
            
    except Exception as e:
        print(f"❌ Erreur extraction FacetWP : {e}")
        return None

def extract_lawyer_from_facet_data(lawyer_data):
    """Extraction des informations d'un avocat depuis les données FacetWP"""
    try:
        content_html = lawyer_data.get('content', '')
        full_name = ""
        url_fiche = ""
        specialisations = []
        
        if content_html:
            soup = BeautifulSoup(content_html, 'html.parser')
            
            # Nom et URL
            link = soup.find('a', href=True)
            if link:
                full_name = link.get('title', '') or link.get_text().strip()
                url_fiche = link['href']
                if url_fiche and not url_fiche.startswith('http'):
                    url_fiche = f"https://barreauaix.com{url_fiche}"
            
            # Spécialisations
            tags = soup.find_all('span', class_='tag')
            for tag in tags:
                spec = tag.get_text().strip()
                if spec and spec not in specialisations:
                    specialisations.append(spec)
        
        # Séparation prénom/nom
        prenom, nom = parse_lawyer_name(full_name)
        
        return {
            'prenom': prenom,
            'nom': nom,
            'nom_complet': full_name,
            'specialisations': '; '.join(specialisations) if specialisations else '',
            'structure': '',
            'annee_inscription': '',
            'date_serment': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'url_fiche': url_fiche,
            'source': 'https://barreauaix.com/grand-public/annuaire/'
        }
        
    except Exception as e:
        print(f"❌ Erreur parsing avocat : {e}")
        return None

def extract_detailed_info(lawyer_url):
    """Extraction des informations détaillées selon les sélecteurs spécifiques"""
    if not lawyer_url:
        return {}
    
    print(f"🔍 Extraction détails: {lawyer_url}")
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        response = session.get(lawyer_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = {
            'structure': '',
            'annee_inscription': '',
            'date_serment': '',
            'email': '',
            'telephone': '',
            'adresse': ''
        }
        
        # 1. EMAIL - Dans <a class="hoverund lh1" href="mailto:...">
        print("  🔍 Recherche email...")
        email_link = soup.find('a', {'class': 'hoverund lh1', 'href': lambda x: x and x.startswith('mailto:')})
        if email_link:
            email = email_link.get('href').replace('mailto:', '').strip()
            details['email'] = email
            print(f"  ✅ Email trouvé: {email}")
        else:
            # Fallback - tous les liens mailto
            email_link = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
            if email_link:
                email = email_link.get('href').replace('mailto:', '').strip()
                details['email'] = email
                print(f"  ✅ Email trouvé (fallback): {email}")
            else:
                print("  ❌ Email non trouvé")
        
        # 2. DATE SERMENT - Dans <h3 class="mb-5"><strong>...A prêté serment le...
        print("  🔍 Recherche date serment...")
        serment_h3 = soup.find('h3', class_='mb-5')
        if serment_h3:
            serment_text = serment_h3.get_text()
            print(f"    📋 Texte H3: {serment_text}")
            
            # Chercher "prêté serment le [date]"
            serment_pattern = r'prêté serment le (.+?)(?:\n|$|\.)'
            serment_match = re.search(serment_pattern, serment_text, re.IGNORECASE)
            if serment_match:
                date_complete = serment_match.group(1).strip()
                details['date_serment'] = date_complete
                print(f"  ✅ Date serment: {date_complete}")
                
                # Extraire l'année
                year_match = re.search(r'(\d{4})', date_complete)
                if year_match:
                    details['annee_inscription'] = year_match.group(1)
                    print(f"  ✅ Année: {details['annee_inscription']}")
            else:
                print("  ❌ Date serment non trouvée")
        else:
            print("  ❌ H3 mb-5 non trouvé")
        
        # 3. ADRESSE - Dans <p class="noir400 f14"><i class="fa-location-dot">...
        print("  🔍 Recherche adresse...")
        
        # Chercher tous les paragraphes avec ces classes
        address_paragraphs = soup.find_all('p', class_=lambda x: x and 'noir400' in str(x) and 'f14' in str(x))
        print(f"    📋 {len(address_paragraphs)} paragraphes noir400 f14 trouvés")
        
        address_found = False
        for i, p in enumerate(address_paragraphs):
            print(f"    🔍 Paragraphe {i+1}: {p}")
            
            # Chercher l'icône fa-location-dot dans ce paragraphe
            location_icon = p.find('i', class_=lambda x: x and 'fa-location-dot' in str(x))
            if location_icon:
                # Récupérer le texte en excluant l'icône
                full_text = p.get_text().strip()
                clean_address = ' '.join(full_text.split())
                details['adresse'] = clean_address
                print(f"  ✅ Adresse trouvée: {clean_address}")
                address_found = True
                break
        
        if not address_found:
            # Fallback: chercher directement "AIX EN PROVENCE" ou "13100"
            print("  🔄 Fallback: recherche directe...")
            all_text = soup.get_text()
            
            # Chercher les lignes contenant "AIX EN PROVENCE" ou "13100"
            aix_pattern = r'([^.\n]*(?:13100|AIX EN PROVENCE)[^.\n]*)'
            matches = re.findall(aix_pattern, all_text, re.IGNORECASE)
            
            for match in matches:
                clean_match = ' '.join(match.strip().split())
                # Vérifier si ça ressemble à une adresse
                if any(word in clean_match.upper() for word in ['RUE', 'AVENUE', 'BOULEVARD', 'PLACE', 'COURS']):
                    details['adresse'] = clean_match
                    print(f"  ✅ Adresse trouvée (fallback): {clean_match}")
                    address_found = True
                    break
        
        if not address_found:
            print("  ❌ Adresse non trouvée")
        
        # 4. TÉLÉPHONE - Recherche générale
        print("  🔍 Recherche téléphone...")
        phone_patterns = [
            r'(?:\+33|0)[1-9](?:[.\-\s]?\d{2}){4}',
            r'0[1-9](?:\s?\d{2}){4}'
        ]
        
        page_text = soup.get_text()
        for pattern in phone_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                phone = matches[0].strip()
                details['telephone'] = phone
                print(f"  ✅ Téléphone: {phone}")
                break
        
        if not details['telephone']:
            print("  ❌ Téléphone non trouvé")
        
        # Résumé de ce qui a été trouvé
        found_fields = [k for k, v in details.items() if v]
        print(f"  📊 Champs trouvés: {found_fields}")
        
        return details
        
    except Exception as e:
        print(f"❌ Erreur extraction {lawyer_url}: {e}")
        return {}

def save_results(lawyers):
    """Sauvegarde des résultats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "AIX_TEST_AMELIORE"
    
    csv_filename = f"{prefix}_{len(lawyers)}_avocats_{timestamp}.csv"
    json_filename = f"{prefix}_{len(lawyers)}_avocats_{timestamp}.json"
    emails_filename = f"{prefix}_EMAILS_{timestamp}.txt"
    
    # CSV
    if lawyers:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = lawyers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers)
    
    # JSON
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Emails
    emails = [l['email'] for l in lawyers if l.get('email')]
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        emailfile.write('\n'.join(emails))
    
    # Rapport
    report_filename = f"{prefix}_RAPPORT_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as report:
        report.write(f"🔍 RAPPORT TEST AMÉLIORE - BARREAU AIX\n")
        report.write(f"=" * 50 + "\n\n")
        report.write(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        report.write(f"📊 Avocats testés: {len(lawyers)}\n\n")
        
        if lawyers:
            with_email = sum(1 for l in lawyers if l.get('email'))
            with_date = sum(1 for l in lawyers if l.get('date_serment'))
            with_address = sum(1 for l in lawyers if l.get('adresse'))
            with_phone = sum(1 for l in lawyers if l.get('telephone'))
            
            report.write(f"📈 RÉSULTATS :\n")
            report.write(f"- Emails trouvés: {with_email}/{len(lawyers)} ({with_email/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Dates serment: {with_date}/{len(lawyers)} ({with_date/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Adresses: {with_address}/{len(lawyers)} ({with_address/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Téléphones: {with_phone}/{len(lawyers)} ({with_phone/len(lawyers)*100:.1f}%)\n\n")
            
            report.write(f"📋 DÉTAIL DES EXTRACTIONS :\n")
            for i, lawyer in enumerate(lawyers):
                report.write(f"\n{i+1}. {lawyer['prenom']} {lawyer['nom']}\n")
                report.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                report.write(f"   Date serment: {lawyer.get('date_serment', 'N/A')}\n")
                report.write(f"   Adresse: {lawyer.get('adresse', 'N/A')}\n")
                report.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\n")
    
    print(f"\n✅ Résultats sauvegardés :")
    print(f"📄 CSV: {csv_filename}")
    print(f"📧 Emails: {emails_filename} ({len(emails)} emails)")
    print(f"📄 Rapport: {report_filename}")
    
    return csv_filename, emails_filename, report_filename

def main():
    """Test avec 5 avocats et extraction complète"""
    print("🔥 TEST AMÉLIORE - BARREAU AIX-EN-PROVENCE")
    print("=" * 50)
    print("Extraction de 5 avocats avec tous les détails\n")
    
    driver = None
    try:
        # Driver
        driver = setup_driver(headless=True)
        
        # Navigation
        url = "https://barreauaix.com/grand-public/annuaire/"
        print(f"🌐 Navigation vers: {url}")
        driver.get(url)
        
        # Cookies
        accept_cookies(driver)
        time.sleep(5)
        
        # Extraction FacetWP
        facet_data = extract_facet_wp_data(driver)
        if not facet_data:
            print("❌ Impossible d'extraire les données")
            return False
        
        # Prendre les 5 premiers avocats
        test_data = facet_data[:5]
        lawyers = []
        
        print(f"\n📊 Phase 1: Extraction de base ({len(test_data)} avocats)")
        for i, lawyer_data in enumerate(test_data):
            lawyer_info = extract_lawyer_from_facet_data(lawyer_data)
            if lawyer_info:
                lawyers.append(lawyer_info)
                print(f"✅ {i+1}/5: {lawyer_info['prenom']} {lawyer_info['nom']}")
        
        # Phase 2: Détails
        print(f"\n🔍 Phase 2: Extraction des détails")
        for i, lawyer in enumerate(lawyers):
            print(f"\n--- Avocat {i+1}/5: {lawyer['nom_complet']} ---")
            if lawyer.get('url_fiche'):
                details = extract_detailed_info(lawyer['url_fiche'])
                lawyer.update(details)
            else:
                print("❌ Pas d'URL de fiche")
        
        # Résultats
        print(f"\n🎯 RÉSULTATS FINAUX:")
        for lawyer in lawyers:
            print(f"\n👤 {lawyer['nom_complet']}")
            print(f"   📧 Email: {lawyer.get('email', 'N/A')}")
            print(f"   📅 Serment: {lawyer.get('date_serment', 'N/A')}")
            print(f"   📍 Adresse: {lawyer.get('adresse', 'N/A')}")
            print(f"   📞 Téléphone: {lawyer.get('telephone', 'N/A')}")
        
        # Sauvegarde
        save_results(lawyers)
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 TEST RÉUSSI ! Prêt pour la version complète.")
    else:
        print("\n💥 TEST ÉCHOUÉ !")