#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper CORRIGÉ pour le Barreau de Dijon
CORRECTION DES SPÉCIALISATIONS ET EMAILS
Date: 07/04/2026
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import requests

def nettoyer_texte(texte):
    """Nettoie le texte en supprimant les espaces superflus."""
    if not texte:
        return ""
    return re.sub(r'\s+', ' ', str(texte)).strip()

def separer_prenom_nom(nom_complet):
    """Sépare intelligemment le prénom et le nom depuis l'URL de la fiche."""
    if not nom_complet:
        return "", ""
    
    # Nettoyer
    nom_complet = nettoyer_texte(nom_complet)
    
    # Supprimer les titres
    nom_complet = re.sub(r'^(Me\s+|Maître\s+)', '', nom_complet, flags=re.IGNORECASE)
    
    # Cas spéciaux pour les noms composés
    parties = nom_complet.split()
    
    if not parties:
        return "", ""
    
    if len(parties) == 1:
        return "", parties[0]
    
    # Par défaut : premier mot = prénom, dernier mot = nom
    if len(parties) == 2:
        return parties[0], parties[1]
    
    # Pour plus de 2 mots : essayer de détecter le pattern
    if len(parties) >= 3:
        # Si il y a des tirets, c'est probablement un nom composé à la fin
        if '-' in nom_complet:
            for i, mot in enumerate(parties):
                if '-' in mot:
                    return ' '.join(parties[:i+1]), ' '.join(parties[i+1:]) if i+1 < len(parties) else mot
        
        # Sinon, prendre le dernier mot comme nom et le reste comme prénom
        return ' '.join(parties[:-1]), parties[-1]
    
    return parties[0], parties[1] if len(parties) > 1 else ""

def extraire_nom_depuis_url(url_fiche):
    """Extrait le nom depuis l'URL de la fiche avocat."""
    if not url_fiche:
        return "", ""
    
    # URL format: https://www.barreau-dijon.avocat.fr/avocat/prenom-nom
    match = re.search(r'/avocat/([^/]+)$', url_fiche)
    if match:
        nom_url = match.group(1)
        # Remplacer les tirets par des espaces
        nom_complet = nom_url.replace('-', ' ')
        # Capitaliser chaque mot
        nom_complet = ' '.join(word.capitalize() for word in nom_complet.split())
        
        return separer_prenom_nom(nom_complet)
    
    return "", ""

def accepter_cookies(driver):
    """Gère l'acceptation des cookies."""
    try:
        time.sleep(2)
        
        # Sélecteurs pour les cookies
        cookie_selectors = [
            "button[class*='accept']",
            "button[id*='accept']", 
            ".cmplz-accept",
            "#cmplz-accept",
            "//button[contains(text(), 'Accepter')]",
            "//button[contains(text(), 'J'accepte')]"
        ]
        
        for selector in cookie_selectors:
            try:
                if selector.startswith('//'):
                    button = driver.find_element(By.XPATH, selector)
                else:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].click();", button)
                print("✓ Cookies acceptés")
                time.sleep(1)
                return True
            except:
                continue
                
        return False
    except:
        return False

def extraire_infos_depuis_options(driver):
    """Extrait les informations depuis les options du menu d'accessibilité."""
    avocats = []
    
    try:
        # Attendre que les options soient chargées
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mdp-readabler-useful-links option"))
        )
        
        # Récupérer toutes les options
        options = driver.find_elements(By.CSS_SELECTOR, "#mdp-readabler-useful-links option")
        print(f"📋 {len(options)} options trouvées dans le menu d'accessibilité")
        
        # Variables pour construire les fiches d'avocats
        avocat_actuel = {}
        
        for option in options:
            try:
                value = option.get_attribute('value')
                text = option.text.strip()
                
                if not value or not text:
                    continue
                
                # Détecter les liens vers les fiches d'avocats
                if '/avocat/' in value and 'VOIR LA FICHE' in text:
                    # Si on a un avocat en cours, l'ajouter à la liste
                    if avocat_actuel.get('source'):
                        avocats.append(avocat_actuel.copy())
                    
                    # Commencer un nouvel avocat
                    avocat_actuel = {
                        'nom_complet': '',
                        'prenom': '',
                        'nom': '',
                        'cabinet': '',
                        'adresse': '',
                        'telephone': '',
                        'email': '',
                        'site_web': '',
                        'specialisations': '',
                        'annee_inscription': '',
                        'source': value
                    }
                    
                    # Extraire le nom depuis l'URL
                    prenom, nom = extraire_nom_depuis_url(value)
                    avocat_actuel['prenom'] = prenom
                    avocat_actuel['nom'] = nom
                    avocat_actuel['nom_complet'] = f"{prenom} {nom}".strip()
                
                # Détecter les emails
                elif value.startswith('mailto:') and '@' in value:
                    if avocat_actuel:
                        email = value.replace('mailto:', '')
                        avocat_actuel['email'] = email
                
                # Détecter les téléphones
                elif value.startswith('tel:'):
                    if avocat_actuel:
                        telephone = value.replace('tel:', '').replace('Tél : ', '')
                        avocat_actuel['telephone'] = telephone
                
                # Détecter les sites web
                elif value.startswith('http') and 'barreau-dijon' not in value and 'google.com' not in value:
                    if avocat_actuel and not avocat_actuel.get('site_web'):
                        avocat_actuel['site_web'] = value
                
                # Détecter les adresses (liens Google Maps)
                elif 'google.com/maps' in value:
                    if avocat_actuel:
                        # Extraire l'adresse depuis l'URL
                        match = re.search(r'query=([^&]+)', value)
                        if match:
                            adresse = match.group(1).replace('%20', ' ').replace('%C3%A8', 'è').replace('%C3%A9', 'é')
                            # Nettoyer l'adresse
                            adresse = adresse.split(',')[0] if ',' in adresse else adresse
                            avocat_actuel['adresse'] = adresse
                            
            except Exception as e:
                continue
        
        # Ajouter le dernier avocat s'il existe
        if avocat_actuel.get('source'):
            avocats.append(avocat_actuel)
        
        print(f"✅ {len(avocats)} avocats extraits depuis le menu d'accessibilité")
        return avocats
        
    except Exception as e:
        print(f"❌ Erreur extraction depuis les options: {str(e)}")
        return []

def scraper_fiche_detaillee(url):
    """Scrape les informations détaillées depuis une fiche individuelle CORRIGÉ."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        html_text = soup.get_text()
        info = {}
        
        # CORRECTION 1: Extraction EMAIL améliorée depuis les fiches
        try:
            emails = soup.find_all('a', href=lambda x: x and 'mailto:' in x)
            if emails:
                email_href = emails[0].get('href', '')
                if email_href.startswith('mailto:'):
                    info['email'] = email_href.replace('mailto:', '').strip()
                    print(f"  ✅ Email trouvé: {info['email']}")
        except:
            pass
        
        # Chercher l'année d'inscription/serment
        text_content = response.text.lower()
        
        # Patterns pour l'année d'inscription
        patterns_annee = [
            r'serment[^\d]*(\d{4})',
            r'inscription[^\d]*(\d{4})',
            r'admission[^\d]*(\d{4})',
            r'asserment[eé][^\d]*(\d{4})',
            r'date\s+de\s+prestation\s+de\s+serment[^\d]*(\d{1,2}/\d{1,2}/(\d{4}))',
            r'prestation\s+de\s+serment[^\d]*(\d{1,2}/\d{1,2}/(\d{4}))'
        ]
        
        for pattern in patterns_annee:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) > 1:
                        annee_int = int(match[1])
                    else:
                        annee_int = int(match)
                    if 1950 <= annee_int <= 2026:
                        info['annee_inscription'] = str(annee_int)
                        break
                except ValueError:
                    continue
            if info.get('annee_inscription'):
                break
        
        # CORRECTION 2: Spécialisations corrigées pour "Domaines traités"
        spec_patterns = [
            r'Domaines\s+traités[\s\n]*([\w\s,.-]+?)(?=\n\n|\nSpécialisations|\nStructure|\nCabinet|$)',
            r'domaines?\s+traités[\s\n]*([\w\s,.-]+?)(?=\n\n|$)',
            r'spécialisations[\s\n]*([\w\s,.-]+?)(?=\n\n|\nStructure|$)',
            r'sp[eé]cialisation[^:]*:([^<]+)',
            r'domaine[^:]*:([^<]+)',
            r'comp[eé]tence[^:]*:([^<]+)',
            r'expertise[^:]*:([^<]+)'
        ]
        
        for i, pattern in enumerate(spec_patterns):
            if i < 3:  # Patterns corrigés avec DOTALL
                match = re.search(pattern, html_text, re.IGNORECASE | re.DOTALL)
            else:  # Anciens patterns
                match = re.search(pattern, text_content)
            
            if match:
                spec = nettoyer_texte(match.group(1))
                # Filtrer "Structure" et autres faux positifs
                if (len(spec) > 5 and 
                    not spec.lower().startswith('structure') and 
                    'structure' not in spec.lower()[:20] and
                    len(spec) < 300):  # Éviter les extractions trop longues
                    info['specialisations'] = spec[:200]
                    print(f"  ✅ Spécialisations trouvées (pattern {i+1}): {spec[:50]}...")
                    break
        
        return info
        
    except Exception as e:
        print(f"  ⚠ Erreur fiche détaillée: {str(e)}")
        return {}

def main():
    """Fonction principale."""
    
    print("=" * 80)
    print("SCRAPER CORRIGÉ - BARREAU DE DIJON")
    print("CORRECTION DES SPÉCIALISATIONS ET EMAILS")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("-" * 80)
    
    # Configuration Chrome
    options = Options()
    options.add_argument('--headless')  # Mode headless pour production
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    
    tous_les_avocats = []
    
    try:
        # 1. Accéder à la page de recherche
        url_base = "https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/"
        print(f"\n📍 Accès à la page d'annuaire: {url_base}")
        driver.get(url_base)
        time.sleep(3)
        
        # 2. Accepter les cookies
        accepter_cookies(driver)
        
        # 3. Soumettre le formulaire pour obtenir tous les résultats
        print("\n🔍 Recherche de tous les avocats...")
        try:
            # Chercher le bouton "TROUVER"
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'TROUVER')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", submit_button)
            print("✓ Bouton TROUVER cliqué")
            time.sleep(5)
        except Exception as e:
            print(f"⚠ Erreur soumission formulaire: {e}")
            # Essayer d'aller directement aux résultats
            driver.get("https://www.barreau-dijon.avocat.fr/annuaire-des-avocats-barreau-de-dijon/annuaire-des-avocats-barreau-de-dijon-resultats/")
            time.sleep(5)
        
        # 4. Extraire les avocats depuis le menu d'accessibilité
        print("\n📊 Extraction des avocats depuis le menu d'accessibilité...")
        tous_les_avocats = extraire_infos_depuis_options(driver)
        
        # PRODUCTION COMPLÈTE - AUCUNE LIMITATION
        print(f"📋 Extraction complète: {len(tous_les_avocats)} avocats trouvés")
        
        print(f"\n✅ Total extrait: {len(tous_les_avocats)} avocats")
        
        # 5. Enrichir avec les fiches détaillées
        if tous_les_avocats:
            print("\n🔎 Enrichissement des informations depuis les fiches détaillées...")
            
            for idx, avocat in enumerate(tous_les_avocats, 1):
                if avocat.get('source'):
                    print(f"  [{idx:02d}/{len(tous_les_avocats)}] {avocat['prenom']} {avocat['nom']}...", end='')
                    
                    info_detaillee = scraper_fiche_detaillee(avocat['source'])
                    
                    # Fusionner les infos
                    for key, value in info_detaillee.items():
                        if value and not avocat.get(key):
                            avocat[key] = value
                    
                    if info_detaillee:
                        details = []
                        if info_detaillee.get('annee_inscription'):
                            details.append(f"inscrit en {info_detaillee['annee_inscription']}")
                        if info_detaillee.get('specialisations'):
                            details.append("avec spécialisations")
                        
                        if details:
                            print(f" ✓ {', '.join(details)}")
                        else:
                            print(" ✓")
                    else:
                        print(" -")
                    
                    # Petite pause entre les requêtes
                    time.sleep(0.5)
        
        # 6. Sauvegarder les résultats
        if tous_les_avocats:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # JSON
            json_file = f'DIJON_CORRIGE_{len(tous_les_avocats)}_avocats_{timestamp}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(tous_les_avocats, f, ensure_ascii=False, indent=2)
            print(f"\n💾 JSON: {json_file}")
            
            # CSV
            csv_file = f'DIJON_CORRIGE_{len(tous_les_avocats)}_avocats_{timestamp}.csv'
            fieldnames = ['nom_complet', 'prenom', 'nom', 'cabinet', 'adresse', 
                         'telephone', 'email', 'site_web', 'specialisations', 'annee_inscription', 'source']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for avocat in tous_les_avocats:
                    row = {field: avocat.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            print(f"💾 CSV: {csv_file}")
            
            # Emails uniques
            emails = list(set([a['email'] for a in tous_les_avocats if a.get('email')]))
            if emails:
                email_file = f'DIJON_CORRIGE_EMAILS_{len(emails)}uniques_{timestamp}.txt'
                with open(email_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(sorted(emails)))
                print(f"📧 Emails: {email_file} ({len(emails)} uniques)")
            
            # Rapport complet
            rapport_file = f'DIJON_CORRIGE_RAPPORT_{timestamp}.txt'
            with open(rapport_file, 'w', encoding='utf-8') as f:
                f.write("RAPPORT D'EXTRACTION CORRIGÉ - BARREAU DE DIJON\n")
                f.write("=" * 70 + "\n\n")
                f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"URL source: {url_base}\n")
                f.write(f"\n")
                f.write("STATISTIQUES\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total avocats extraits: {len(tous_les_avocats)}\n")
                f.write(f"Avec email: {len([a for a in tous_les_avocats if a.get('email')])}\n")
                f.write(f"Avec téléphone: {len([a for a in tous_les_avocats if a.get('telephone')])}\n")
                f.write(f"Avec adresse: {len([a for a in tous_les_avocats if a.get('adresse')])}\n")
                f.write(f"Avec site web: {len([a for a in tous_les_avocats if a.get('site_web')])}\n")
                f.write(f"Avec spécialisations: {len([a for a in tous_les_avocats if a.get('specialisations')])}\n")
                f.write(f"Avec année d'inscription: {len([a for a in tous_les_avocats if a.get('annee_inscription')])}\n")
                f.write(f"\n")
                f.write("LISTE DES AVOCATS\n")
                f.write("-" * 40 + "\n")
                
                for i, avocat in enumerate(tous_les_avocats, 1):
                    f.write(f"\n{i:02d}. {avocat.get('prenom', '')} {avocat.get('nom', '')}\n")
                    if avocat.get('email'):
                        f.write(f"    📧 {avocat['email']}\n")
                    if avocat.get('telephone'):
                        f.write(f"    📞 {avocat['telephone']}\n")
                    if avocat.get('adresse'):
                        f.write(f"    📍 {avocat['adresse']}\n")
                    if avocat.get('site_web'):
                        f.write(f"    🌐 {avocat['site_web']}\n")
                    if avocat.get('specialisations'):
                        f.write(f"    🎯 {avocat['specialisations']}\n")
                    if avocat.get('annee_inscription'):
                        f.write(f"    📅 Inscrit en {avocat['annee_inscription']}\n")
                    f.write(f"    🔗 {avocat.get('source', '')}\n")
            
            print(f"📄 Rapport: {rapport_file}")
            
            # Résumé
            print("\n" + "=" * 70)
            print("RÉSUMÉ DE L'EXTRACTION CORRIGÉE")
            print("=" * 70)
            print(f"✅ {len(tous_les_avocats)} avocats extraits avec succès")
            print(f"📧 {len(emails) if emails else 0} emails uniques")
            print(f"📞 {len([a for a in tous_les_avocats if a.get('telephone')])} numéros de téléphone")
            print(f"🌐 {len([a for a in tous_les_avocats if a.get('site_web')])} sites web")
            print(f"🎯 {len([a for a in tous_les_avocats if a.get('specialisations')])} avec spécialisations")
            print(f"📅 {len([a for a in tous_les_avocats if a.get('annee_inscription')])} avec année d'inscription")
            
            # Exemples
            print("\n📋 Exemples d'avocats extraits:")
            for i, avocat in enumerate(tous_les_avocats[:5], 1):
                print(f"\n  {i}. {avocat.get('prenom', '')} {avocat.get('nom', '')}")
                if avocat.get('email'):
                    print(f"     📧 {avocat['email']}")
                if avocat.get('telephone'):
                    print(f"     📞 {avocat['telephone']}")
                if avocat.get('specialisations'):
                    print(f"     🎯 {avocat['specialisations']}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n" + "=" * 80)
        print("FIN DU SCRAPING CORRIGÉ")
        print("=" * 80)

if __name__ == "__main__":
    main()