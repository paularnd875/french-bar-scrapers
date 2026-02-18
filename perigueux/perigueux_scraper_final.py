#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper final pour le Barreau de Périgueux
Extraction complète des données des 91 avocats avec dates de serment
"""

import json
import csv
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Configuration du driver Chrome en mode headless"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def parse_name(full_name):
    """Parsing amélioré pour les noms français avec particules"""
    if not full_name or "Ordre des avocats" in full_name:
        return "", ""
    
    full_name = full_name.strip().replace('\n', ' ').replace('\t', ' ')
    full_name = ' '.join(full_name.split())
    
    words = full_name.split()
    if len(words) < 2:
        return full_name, ""
    
    particles = ['de', 'du', 'des', 'de la', 'van', 'da', 'di']
    
    # Gestion des noms tout en majuscules
    all_upper = all(word.isupper() for word in words)
    if all_upper and len(words) >= 2:
        if len(words) == 2:
            return words[1], words[0]
        else:
            return words[-1], " ".join(words[:-1])
    
    # Logique standard pour les noms mixtes
    for i in range(1, len(words)):
        if words[i].lower() in particles or words[i].isupper():
            return " ".join(words[:i]), " ".join(words[i:])
    
    return words[0], " ".join(words[1:])

def extract_lawyer_complete_avec_serment(driver, profile_url):
    """Extraction complète des données d'avocat avec date de serment"""
    try:
        driver.get(profile_url)
        time.sleep(2)
        
        lawyer_data = {
            'prenom': '', 'nom': '', 'email': '', 'annee_inscription': '',
            'specialisations': '', 'structure': '', 'adresse': '', 
            'telephone': '', 'annee_serment': '', 'source_url': profile_url
        }
        
        # Extraction du nom depuis plusieurs sources
        name_candidates = []
        
        # 1. Sélecteurs de titre
        try:
            title_selectors = ["h1", "h2", ".contentheading", ".componentheading", ".cb_template"]
            for selector in title_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and "Ordre des avocats" not in text and len(text) > 3:
                        name_candidates.append(text)
        except: pass
        
        # 2. Titre de la page
        try:
            page_title = driver.title
            if page_title and " - " in page_title:
                title_part = page_title.split(" - ")[0].strip()
                if title_part and "Ordre des avocats" not in title_part:
                    name_candidates.append(title_part)
        except: pass
        
        # 3. Patterns dans le contenu
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            name_patterns = [
                r'(?:Maître|Me\.?|Avocat)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'^([A-Z][A-Z\s]+[A-Z])$',
                r'([A-Z][a-z]+\s+[A-Z][A-Z]+)'
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, page_text, re.MULTILINE)
                for match in matches:
                    if len(match.strip()) > 3:
                        name_candidates.append(match.strip())
        except: pass
        
        # 4. URL comme dernier recours
        try:
            url_name = profile_url.split('/')[-1].replace('.html', '').replace('%20', ' ')
            if url_name and len(url_name) > 2:
                import urllib.parse
                url_name = urllib.parse.unquote(url_name)
                name_candidates.append(url_name)
        except: pass
        
        # Sélectionner le meilleur nom
        best_name = ""
        for candidate in name_candidates:
            candidate = candidate.strip()
            if (len(candidate) > len(best_name) and 
                candidate not in ["Ordre des avocats au Barreau de Périgueux"] and
                not candidate.lower().startswith("http")):
                best_name = candidate
        
        if best_name:
            prenom, nom = parse_name(best_name)
            lawyer_data['prenom'] = prenom
            lawyer_data['nom'] = nom
        
        # *** EXTRACTION DATE DE SERMENT depuis h3 elements ***
        try:
            h3_elements = driver.find_elements(By.TAG_NAME, "h3")
            for h3 in h3_elements:
                text = h3.text.strip()
                if "Prestation de serment" in text:
                    match = re.search(r'Prestation de serment\s*:\s*(\d{4})', text)
                    if match:
                        year = match.group(1)
                        if 1950 <= int(year) <= 2025:
                            lawyer_data['annee_serment'] = year
                            break
        except: pass
        
        # Email
        try:
            email_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'mailto:')]")
            for link in email_links:
                email = link.get_attribute('href').replace('mailto:', '').strip()
                if (email and '@' in email and 
                    'barreau' not in email.lower() and 
                    'contact@avocats-perigueux' not in email.lower()):
                    lawyer_data['email'] = email
                    break
            
            if not lawyer_data['email']:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
                emails = re.findall(email_pattern, page_text)
                for email in emails:
                    if ('barreau' not in email.lower() and 
                        'contact@avocats-perigueux' not in email.lower()):
                        lawyer_data['email'] = email
                        break
        except: pass
        
        # Téléphone
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            phone_patterns = [
                r'(?:Tel|Tél|Téléphone|Phone)[:\s]*([0-9\.\s\-]{10,})',
                r'([0-9]{2}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2})',
                r'([0-9]{3}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2}[.\s\-]?[0-9]{2})'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    phone = re.sub(r'[^\d\.\-\s]', '', match).strip()
                    if (len(phone.replace('.', '').replace('-', '').replace(' ', '')) >= 10 and
                        phone not in ['05.53.35.32.18', '05 53 35 32 18', '05 53 53 21 34']):
                        lawyer_data['telephone'] = phone
                        break
                if lawyer_data['telephone']:
                    break
        except: pass
        
        # Année d'inscription (fallback si pas de serment)
        if not lawyer_data['annee_serment']:
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                year_patterns = [
                    r'(?:inscrit|admission|barreau).*?(?:en\s*)?(\d{4})',
                    r'(\d{4}).*?(?:inscrit|admission)'
                ]
                
                for pattern in year_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        year = match.group(1)
                        if 1970 <= int(year) <= 2025:
                            lawyer_data['annee_inscription'] = year
                            break
            except: pass
        
        return lawyer_data
        
    except Exception as e:
        print(f"      ❌ Erreur extraction: {str(e)[:50]}...")
        return None

# Liste complète des 91 URLs des profils d'avocats
PERIGUEUX_LAWYER_URLS = [
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/77/dalonso.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/160/ALVES%20AMANDINE.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/116/famblard.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/144/CAMIRTAHMASSEB.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/172/ARACIL.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/100/jathanaze.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/78/ebarateau.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/136/ebarret.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/79/bbaylac.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/80/hbenichou.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/81/gbenichou.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/156/mbernard.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/132/dbertol.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/82/sbertrandon.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/101/lbineaud.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/125/dbondat.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/146/ANNEBONIS.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/155/cborel.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/117/sbourdeix.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/83/mboutot.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/84/mbrus.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/133/lchevalier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/102/cchevallier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/85/fcoiffe.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/126/dcorvee.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/118/scoudert.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/134/ccourapied.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/86/pdaniel%20lamaziere.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/127/VICTORDAUDET.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/165/2SOUSA.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/119/gdeglane.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/147/adelaire.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/103/cdevise.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/162/vdotal.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/139/cdubech.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/104/oenyenge.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/148/VESTAGER.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/161/MELISSAFERREIRA.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/157/vfournier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/135/sgaultier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/140/cgenevay.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/152/fgluckstein.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/105/pgokelaere.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/158/AMGORDON.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/128/wgraire.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/87/ggrand.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/163/rhammouche.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/129/jherbreteau.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/120/ajaulhac.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/141/cjollivet.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/121/sjulien.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/159/bkaoula.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/88/plabroue.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/122/flafaye.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/149/rlaferrere.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/106/blagarde.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/89/nlandon.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/107/slaporte.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/150/LLAVERGNE.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/90/plaviale.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/153/Jlefournis.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/91/aleguay.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/154/Jlebon.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/164/Clegermaury.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/92/vlemaire.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/108/alemercier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/109/mlenglen.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/166/MALAURIE%20ESTHER.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/142/mmaridet.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/110/vmaris.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/123/nmarrache.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/130/fmarsat.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/143/dmarsollier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/124/rmartins.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/111/nmayaud.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/167/CMORA.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/151/AMOUILLAC-DELAGE.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/112/fmoustrou.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/93/mnoel.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/94/fpohu.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/168/CRIOU.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/169/criviere.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/137/croc.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/170/mrostaing.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/171/Gsantax.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/131/ssoulier.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/95/bthomas.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/113/ctierney.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/114/ntrion.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/115/cvergne.html",
    "https://www.avocats-perigueux.com/component/comprofiler/userprofile/173/YOUBO.html"
]

def main():
    """Fonction principale d'extraction"""
    print("🏛️ SCRAPER BARREAU DE PÉRIGUEUX - EXTRACTION COMPLÈTE")
    print("=" * 65)
    print(f"📋 {len(PERIGUEUX_LAWYER_URLS)} URLs d'avocats à traiter avec dates de serment")
    
    driver = setup_driver()
    all_lawyers = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        for i, profile_url in enumerate(PERIGUEUX_LAWYER_URLS, 1):
            url_name = profile_url.split('/')[-1]
            print(f"\n👤 {i:2d}/{len(PERIGUEUX_LAWYER_URLS)}: {url_name}")
            
            lawyer = extract_lawyer_complete_avec_serment(driver, profile_url)
            if lawyer:
                if lawyer['annee_serment']:
                    print(f"         📅 Serment en {lawyer['annee_serment']}")
                    
                all_lawyers.append(lawyer)
                print(f"    ✅ {lawyer['prenom']} {lawyer['nom']}")
                
                if lawyer['email']:
                    print(f"       📧 {lawyer['email']}")
                if lawyer['telephone']:
                    print(f"       📞 {lawyer['telephone']}")
                if lawyer['annee_serment']:
                    print(f"       ⚖️ Serment: {lawyer['annee_serment']}")
            else:
                print(f"      ❌ Extraction échouée")
            
            # Sauvegarde intermédiaire tous les 20 profils
            if i % 20 == 0:
                backup_file = f"backup_perigueux_{i}avocats_{timestamp}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(all_lawyers, f, indent=2, ensure_ascii=False)
                print(f"    💾 Backup: {len(all_lawyers)} avocats sauvegardés")
        
        print(f"\n🏆 EXTRACTION TERMINÉE AVEC DATES DE SERMENT!")
        print(f"📊 TOTAL: {len(all_lawyers)} avocats extraits sur {len(PERIGUEUX_LAWYER_URLS)} URLs")
        
        # Statistiques finales
        with_email = len([l for l in all_lawyers if l['email']])
        with_phone = len([l for l in all_lawyers if l['telephone']])
        with_serment = len([l for l in all_lawyers if l['annee_serment']])
        
        print(f"\n📈 QUALITÉ:")
        print(f"  📧 Emails: {with_email}/{len(all_lawyers)} ({with_email/len(all_lawyers)*100:.1f}%)")
        print(f"  📞 Téléphones: {with_phone}/{len(all_lawyers)} ({with_phone/len(all_lawyers)*100:.1f}%)")
        print(f"  ⚖️ Dates serment: {with_serment}/{len(all_lawyers)} ({with_serment/len(all_lawyers)*100:.1f}%)")
        
        # Génération des fichiers finaux
        csv_file = f"PERIGUEUX_FINAL_COMPLET_{len(all_lawyers)}_avocats_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if all_lawyers:
                writer = csv.DictWriter(f, fieldnames=all_lawyers[0].keys())
                writer.writeheader()
                writer.writerows(all_lawyers)
        
        json_file = f"PERIGUEUX_FINAL_COMPLET_{len(all_lawyers)}_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_lawyers, f, indent=2, ensure_ascii=False)
        
        unique_emails = list(set([l['email'] for l in all_lawyers if l['email']]))
        email_file = f"PERIGUEUX_EMAILS_FINAL_{len(unique_emails)}_uniques_{timestamp}.txt"
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(sorted(unique_emails)))
        
        print(f"\n💾 FICHIERS GÉNÉRÉS:")
        print(f"📊 {csv_file}")
        print(f"📄 {json_file}")
        print(f"📧 {email_file}")
        
        print(f"\n🎉 MISSION ACCOMPLIE AVEC DATES DE SERMENT!")
        print(f"✅ Extraction complète de {len(all_lawyers)} avocats")
        print(f"✅ {len(unique_emails)} emails uniques collectés")
        if with_serment:
            print(f"⚖️ {with_serment} dates de serment récupérées")
        
        return len(all_lawyers)
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return 0
        
    finally:
        driver.quit()

if __name__ == "__main__":
    total = main()
    print(f"\n🏁 EXTRACTION FINALE TERMINÉE: {total} avocats avec dates de serment")