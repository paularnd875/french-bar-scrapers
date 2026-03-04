#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU AIX-EN-PROVENCE - PRODUCTION COMPLÈTE
======================================================

Extraction automatique de tous les 940 avocats avec détails complets.
Mode production sans interaction utilisateur.

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
            for i, part in enumerate(parts):
                if "-" in part and i < len(parts) - 1:
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
            'latitude': lawyer_data.get('position', {}).get('lat', ''),
            'longitude': lawyer_data.get('position', {}).get('lng', ''),
            'source': 'https://barreauaix.com/grand-public/annuaire/'
        }
        
    except Exception as e:
        print(f"❌ Erreur parsing avocat : {e}")
        return None

def extract_detailed_info(lawyer_url, session=None):
    """Extraction des informations détaillées selon les sélecteurs spécifiques"""
    if not lawyer_url:
        return {}
    
    try:
        if session is None:
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
        
        # 1. EMAIL - Dans les liens mailto
        email_link = soup.find('a', {'class': 'hoverund lh1', 'href': lambda x: x and x.startswith('mailto:')})
        if email_link:
            details['email'] = email_link.get('href').replace('mailto:', '').strip()
        else:
            # Fallback - tous les liens mailto
            email_link = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
            if email_link:
                details['email'] = email_link.get('href').replace('mailto:', '').strip()
        
        # 2. DATE SERMENT - Dans <h3 class="mb-5">
        serment_h3 = soup.find('h3', class_='mb-5')
        if serment_h3:
            serment_text = serment_h3.get_text()
            # Chercher "prêté serment le [date]"
            serment_pattern = r'prêté serment le (.+?)(?:\n|$|\.)'
            serment_match = re.search(serment_pattern, serment_text, re.IGNORECASE)
            if serment_match:
                details['date_serment'] = serment_match.group(1).strip()
                # Extraire l'année
                year_match = re.search(r'(\d{4})', details['date_serment'])
                if year_match:
                    details['annee_inscription'] = year_match.group(1)
        
        # 3. ADRESSE - Dans <p class="noir400 f14"><i class="fa-location-dot">
        address_paragraphs = soup.find_all('p', class_=lambda x: x and 'noir400' in str(x) and 'f14' in str(x))
        for p in address_paragraphs:
            location_icon = p.find('i', class_=lambda x: x and 'fa-location-dot' in str(x))
            if location_icon:
                full_text = p.get_text().strip()
                details['adresse'] = ' '.join(full_text.split())
                break
        
        # 4. TÉLÉPHONE - Recherche des numéros français
        phone_patterns = [
            r'(?:\+33|0)[1-9](?:[.\-\s]?\d{2}){4}',
            r'0[1-9](?:\s?\d{2}){4}'
        ]
        
        page_text = soup.get_text()
        for pattern in phone_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                for match in matches:
                    if match.startswith(('01', '02', '03', '04', '05', '09', '+33')):
                        details['telephone'] = match.strip()
                        break
                if details['telephone']:
                    break
        
        return details
        
    except Exception as e:
        print(f"❌ Erreur fiche {lawyer_url}: {e}")
        return {}

def save_results(lawyers, mode="PRODUCTION"):
    """Sauvegarde des résultats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"AIX_{mode}"
    
    csv_filename = f"{prefix}_{len(lawyers)}_avocats_{timestamp}.csv"
    json_filename = f"{prefix}_{len(lawyers)}_avocats_{timestamp}.json"
    
    # Sauvegarde CSV
    if lawyers:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = lawyers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers)
    
    # Sauvegarde JSON
    with open(json_filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
    
    # Sauvegarde emails uniquement
    emails_filename = f"{prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
    emails = [l['email'] for l in lawyers if l.get('email')]
    with open(emails_filename, 'w', encoding='utf-8') as emailfile:
        emailfile.write('\n'.join(emails))
    
    # Rapport détaillé
    report_filename = f"{prefix}_RAPPORT_COMPLET_{timestamp}.txt"
    with open(report_filename, 'w', encoding='utf-8') as report:
        report.write(f"🔍 RAPPORT PRODUCTION - BARREAU AIX-EN-PROVENCE\n")
        report.write(f"=" * 60 + "\n\n")
        report.write(f"📅 Date/Heure : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        report.write(f"🌐 URL Source : https://barreauaix.com/grand-public/annuaire/\n")
        report.write(f"📊 Total avocats extraits : {len(lawyers)}\n")
        report.write(f"📁 Fichier CSV : {csv_filename}\n")
        report.write(f"📁 Fichier JSON : {json_filename}\n")
        report.write(f"📧 Fichier Emails : {emails_filename}\n\n")
        
        if lawyers:
            # Statistiques détaillées
            with_specializations = sum(1 for l in lawyers if l.get('specialisations'))
            with_email = sum(1 for l in lawyers if l.get('email'))
            with_phone = sum(1 for l in lawyers if l.get('telephone'))
            with_address = sum(1 for l in lawyers if l.get('adresse'))
            with_structure = sum(1 for l in lawyers if l.get('structure'))
            with_year = sum(1 for l in lawyers if l.get('annee_inscription'))
            with_date_serment = sum(1 for l in lawyers if l.get('date_serment'))
            
            report.write(f"📈 STATISTIQUES DÉTAILLÉES :\n")
            report.write(f"- Avocats avec spécialisations : {with_specializations}/{len(lawyers)} ({with_specializations/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec email : {with_email}/{len(lawyers)} ({with_email/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec téléphone : {with_phone}/{len(lawyers)} ({with_phone/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec adresse : {with_address}/{len(lawyers)} ({with_address/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec structure : {with_structure}/{len(lawyers)} ({with_structure/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec année inscription : {with_year}/{len(lawyers)} ({with_year/len(lawyers)*100:.1f}%)\n")
            report.write(f"- Avocats avec date serment complète : {with_date_serment}/{len(lawyers)} ({with_date_serment/len(lawyers)*100:.1f}%)\n\n")
            
            # Top spécialisations
            all_specs = []
            for lawyer in lawyers:
                if lawyer.get('specialisations'):
                    specs = lawyer['specialisations'].split('; ')
                    all_specs.extend(specs)
            
            from collections import Counter
            if all_specs:
                spec_counts = Counter(all_specs)
                report.write(f"🏆 TOP 10 SPÉCIALISATIONS :\n")
                for spec, count in spec_counts.most_common(10):
                    report.write(f"- {spec}: {count} avocats\n")
                report.write("\n")
            
            # Échantillon d'emails
            if emails:
                report.write(f"📧 ÉCHANTILLON D'EMAILS (10 premiers) :\n")
                for email in emails[:10]:
                    report.write(f"- {email}\n")
    
    print(f"\n✅ Résultats sauvegardés :")
    print(f"📄 CSV: {csv_filename}")
    print(f"📄 JSON: {json_filename}")
    print(f"📧 Emails: {emails_filename} ({len(emails)} emails)")
    print(f"📄 Rapport: {report_filename}")
    
    return csv_filename, json_filename, report_filename

def main():
    """Extraction automatique complète"""
    print("🔥 EXTRACTION PRODUCTION - BARREAU AIX-EN-PROVENCE")
    print("=" * 60)
    print("Mode automatique : extraction complète de tous les avocats\n")
    
    driver = None
    try:
        # Configuration du driver
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
            print("❌ Impossible d'extraire les données FacetWP")
            return False
        
        # Traitement des avocats
        lawyers = []
        print(f"\n📊 Phase 1: Extraction de base ({len(facet_data)} avocats)")
        
        for i, lawyer_data in enumerate(facet_data):
            lawyer_info = extract_lawyer_from_facet_data(lawyer_data)
            if lawyer_info:
                lawyers.append(lawyer_info)
                if (i + 1) % 100 == 0:
                    print(f"✅ {i+1}/{len(facet_data)} avocats traités")
        
        print(f"\n🎯 Phase 1 terminée : {len(lawyers)} avocats extraits")
        
        # Sauvegarde intermédiaire de la liste
        save_results(lawyers, "LISTE_BASE")
        
        # Phase 2: Détails complets
        print(f"\n🔍 Phase 2 : Extraction des détails complets...")
        print(f"⏱️  Temps estimé : ~{len(lawyers) * 3 // 60} minutes")
        
        # Session partagée
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Traitement en lots
        batch_size = 20
        total_processed = 0
        
        for i in range(0, len(lawyers), batch_size):
            batch = lawyers[i:i+batch_size]
            batch_num = i//batch_size + 1
            print(f"\n📦 Lot {batch_num}/{(len(lawyers)-1)//batch_size + 1} ({len(batch)} avocats)")
            
            for j, lawyer in enumerate(batch):
                try:
                    if lawyer.get('url_fiche'):
                        details = extract_detailed_info(lawyer['url_fiche'], session)
                        lawyer.update(details)
                        total_processed += 1
                        
                        # Affichage périodique
                        if total_processed % 10 == 0:
                            print(f"✅ {total_processed}/{len(lawyers)}: {lawyer['prenom']} {lawyer['nom']}")
                    
                    # Pause entre les requêtes
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Erreur {lawyer.get('nom_complet', 'Unknown')}: {e}")
                    continue
            
            # Sauvegarde intermédiaire tous les 100 avocats
            if total_processed % 100 == 0:
                print(f"\n💾 Sauvegarde intermédiaire ({total_processed} avocats)...")
                save_results(lawyers[:total_processed + i + len(batch)], f"PARTIEL_{total_processed}")
        
        # Sauvegarde finale
        print(f"\n💾 Sauvegarde finale...")
        save_results(lawyers, "FINAL_COMPLET")
        
        # Résumé final
        print(f"\n🎉 EXTRACTION TERMINÉE !")
        print(f"📊 Total : {len(lawyers)} avocats")
        
        # Statistiques finales
        with_email = sum(1 for l in lawyers if l.get('email'))
        with_phone = sum(1 for l in lawyers if l.get('telephone'))
        with_address = sum(1 for l in lawyers if l.get('adresse'))
        with_date_serment = sum(1 for l in lawyers if l.get('date_serment'))
        
        print(f"📧 Emails trouvés : {with_email}/{len(lawyers)} ({with_email/len(lawyers)*100:.1f}%)")
        print(f"📞 Téléphones : {with_phone}/{len(lawyers)} ({with_phone/len(lawyers)*100:.1f}%)")
        print(f"📍 Adresses : {with_address}/{len(lawyers)} ({with_address/len(lawyers)*100:.1f}%)")
        print(f"📅 Dates serment : {with_date_serment}/{len(lawyers)} ({with_date_serment/len(lawyers)*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("🔚 Driver fermé")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🏆 MISSION ACCOMPLIE ! Tous les avocats ont été extraits.")
    else:
        print("\n💥 ÉCHEC DE L'EXTRACTION.")