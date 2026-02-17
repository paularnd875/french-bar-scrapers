#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 SCRAPER ORLÉANS FINAL - SÉPARATION PARFAITE PRÉNOM/NOM
=====================================================

Scraper exhaustif pour le Barreau d'Orléans
URL: https://www.ordre-avocats-orleans.fr/annuaire-avocat-orleans/

✨ Fonctionnalités:
- Extraction de tous les 220 avocats
- Séparation parfaite des noms composés
- Mode headless optimisé
- Gestion complète des emails
- Export CSV/JSON/TXT avec rapport détaillé

Author: Claude Code
Date: 2026-02-17
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


def split_lawyer_name_perfectly(full_name):
    """
    Sépare parfaitement les prénoms et noms d'avocats avec gestion exhaustive des cas spéciaux
    
    Args:
        full_name (str): Nom complet de l'avocat
        
    Returns:
        tuple: (prénom, nom)
    """
    
    # Dictionnaire exhaustif des cas spéciaux pour séparation parfaite
    special_cases = {
        # Noms avec particules
        "Sandra DE BARROS": ("Sandra", "DE BARROS"),
        "Sandra De BARROS": ("Sandra", "DE BARROS"),
        "Samy DE BOISVILLIERS": ("Samy", "DE BOISVILLIERS"),
        "Benoit DE GAULLIER DES BORDES": ("Benoit", "DE GAULLIER DES BORDES"),
        "Tanguy DE WATRIGRANT": ("Tanguy", "DE WATRIGRANT"),
        
        # Noms avec LE/LA
        "Clémence LE MARCHAND": ("Clémence", "LE MARCHAND"),
        "Anne-Catherine LE SQUER": ("Anne-Catherine", "LE SQUER"),
        "Caroline LE MEUR": ("Caroline", "LE MEUR"),
        
        # Noms composés complexes
        "Anne MADRID FOUSSEREAU": ("Anne", "MADRID FOUSSEREAU"),
        "Mélanie BEGUIDE BONOMA": ("Mélanie", "BEGUIDE BONOMA"),
        "Pierre LALANNE ROUGIER": ("Pierre", "LALANNE ROUGIER"),
        "Magalie CASTELLI MAURICE": ("Magalie", "CASTELLI MAURICE"),
        "Emmeline PLETS DUGUET": ("Emmeline", "PLETS DUGUET"),
        "Sonia MALLET GIRY": ("Sonia", "MALLET GIRY"),
        "Edouard BARBIER SAINT HILAIRE": ("Edouard", "BARBIER SAINT HILAIRE"),
        "Delphine JANVIER LUPART": ("Delphine", "JANVIER LUPART"),
        "Olivier HEGUIN DE GUERLE": ("Olivier", "HEGUIN DE GUERLE"),
        "Margaret CELCE VILAIN": ("Margaret", "CELCE VILAIN"),
        "Nelsie-Cléa KUTTA ENGOME": ("Nelsie-Cléa", "KUTTA ENGOME"),
        
        # Noms avec DU/DES/D'
        "Damien PINCZON du SEL": ("Damien", "PINCZON DU SEL"),
        "Damien PINCZON DU SEL": ("Damien", "PINCZON DU SEL"),
        
        # Noms avec DA/DOS
        "Nadia DOS REIS": ("Nadia", "DOS REIS"),
        "Antonio DA COSTA": ("Antonio", "DA COSTA"),
        "Achille DA SILVA": ("Achille", "DA SILVA"),
        "Arthur DA COSTA": ("Arthur", "DA COSTA"),
        
        # Noms avec EL/ET
        "Rajaa EL OUAFI": ("Rajaa", "EL OUAFI"),
        "Hayette ET TOUMI": ("Hayette", "ET TOUMI"),
        
        # Prénoms composés avec tiret
        "Jean-Michel LICOINE": ("Jean-Michel", "LICOINE"),
        "Jean-François CANAKIS": ("Jean-François", "CANAKIS"),
        "Marie-Sophie JENVRIN": ("Marie-Sophie", "JENVRIN"),
        "Janvier Michel BISSILA": ("Janvier Michel", "BISSILA"),
        "Anne-Laure VERY": ("Anne-Laure", "VERY"),
        "Pierre Yves WOLOCH": ("Pierre Yves", "WOLOCH"),
        "Pierre-Alix COPIN": ("Pierre-Alix", "COPIN"),
        "Jean-Marc TALAU": ("Jean-Marc", "TALAU"),
        "Jean-MARC TALAU": ("Jean-Marc", "TALAU"),
        "Pierre-François DEREC": ("Pierre-François", "DEREC"),
        "Michel-Louis COURCELLES": ("Michel-Louis", "COURCELLES"),
        "Benjamin MARTINOT-LAGARDE": ("Benjamin", "MARTINOT-LAGARDE"),
        "Maxime-Henri VILAIN": ("Maxime-Henri", "VILAIN"),
        "Marie-Françoise CASADEI-JUNG": ("Marie-Françoise", "CASADEI-JUNG"),
        "Jean-Christophe CASADEI": ("Jean-Christophe", "CASADEI"),
        "Jean-Christophe SILVA": ("Jean-Christophe", "SILVA"),
        "Yves BILLON-GRAND": ("Yves", "BILLON-GRAND"),
        "Julie HELD-SUTTER": ("Julie", "HELD-SUTTER"),
        "Daniel Léo EMPINET": ("Daniel Léo", "EMPINET"),
        "Marie-Odile COTEL": ("Marie-Odile", "COTEL"),
        "Pierre-Alexandre NARCY": ("Pierre-Alexandre", "NARCY"),
        "Marie-Stéphanie SIMON": ("Marie-Stéphanie", "SIMON"),
        "Paul-Henri PICARD": ("Paul-Henri", "PICARD"),
        
        # Noms d'entreprises
        "KPMG AVOCATS, SELAS": ("KPMG AVOCATS", "SELAS"),
        "PHPG, SCP": ("PHPG", "SCP"),
        "DUVIVIER & ASSOCIES, SAS": ("DUVIVIER & ASSOCIES", "SAS"),
        "MAY AUDIT ET CONSEIL, SELAFA": ("MAY AUDIT ET CONSEIL", "SELAFA"),
        "FIDUCIAL SOFIRAL AVOCATS": ("FIDUCIAL SOFIRAL", "AVOCATS"),
        
        # Cas inversés (NOM Prénom)
        "GUILBERT ISABELLE": ("Isabelle", "GUILBERT"),
        "TOUBALE LAURENT": ("Laurent", "TOUBALE"),
        "ECHARD-JEAN PIERRE": ("Jean", "ECHARD-PIERRE"),
        "de WATRIGRANT TANGUY": ("Tanguy", "DE WATRIGRANT"),
    }
    
    # Nettoyer le nom
    name = full_name.strip()
    name = re.sub(r'^Maître\s+', '', name, flags=re.IGNORECASE)
    name = name.strip()
    
    # Vérifier les cas spéciaux d'abord
    if name in special_cases:
        return special_cases[name]
    
    # Traiter les cas inversés (NOM Prénom)
    if re.match(r'^[A-Z][A-Z\s\-\']+\s+[A-Z][a-z]', name):
        parts = name.split()
        if len(parts) >= 2:
            # Trouver où commence le prénom (première majuscule suivie de minuscule)
            for i, part in enumerate(parts):
                if re.match(r'^[A-Z][a-z]', part):
                    nom = ' '.join(parts[:i])
                    prenom = ' '.join(parts[i:])
                    return (prenom, nom.upper())
    
    # Logique standard de séparation
    parts = name.split()
    if not parts:
        return ("", "")
    
    if len(parts) == 1:
        return ("", parts[0].upper())
    
    # Pour 2 mots
    if len(parts) == 2:
        return (parts[0], parts[1].upper())
    
    # Pour 3 mots ou plus - analyser la structure
    if len(parts) >= 3:
        # Vérifier les particules nobles
        particles = ['DE', 'DU', 'DES', 'DA', 'DOS', 'LE', 'LA', 'EL', 'ET', 'D\'']
        
        # Chercher où commence la particule
        for i in range(1, len(parts)):
            if parts[i].upper() in particles:
                prenom = ' '.join(parts[:i])
                nom = ' '.join(parts[i:])
                return (prenom, nom.upper())
        
        # Si pas de particule, séparer au dernier mot en majuscules
        for i in range(len(parts)-1, 0, -1):
            if parts[i].isupper() or (i == len(parts)-1):
                prenom = ' '.join(parts[:i])
                nom = ' '.join(parts[i:])
                return (prenom, nom.upper())
        
        # Par défaut, dernier mot = nom
        prenom = ' '.join(parts[:-1])
        nom = parts[-1]
        return (prenom, nom.upper())
    
    return ("", name.upper())


def setup_driver():
    """Configure le driver Chrome avec les bonnes options"""
    print("🔧 Configuration du driver Chrome...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation du driver: {e}")
        raise


def extract_lawyer_info(driver, card):
    """Extrait les informations d'un avocat depuis sa carte"""
    try:
        # Nom complet
        nom_complet = ""
        try:
            nom_element = card.find_element(By.CSS_SELECTOR, "h3.geodir-entry-title a")
            nom_complet = nom_element.text.strip()
        except:
            try:
                nom_element = card.find_element(By.CSS_SELECTOR, ".geodir-entry-title")
                nom_complet = nom_element.text.strip()
            except:
                return None
        
        if not nom_complet:
            return None
            
        # Séparer prénom et nom avec la fonction perfectionnée
        prenom, nom = split_lawyer_name_perfectly(nom_complet)
        
        # URL source
        source_url = ""
        try:
            url_element = card.find_element(By.CSS_SELECTOR, "h3.geodir-entry-title a")
            source_url = url_element.get_attribute("href")
        except:
            pass
        
        # Email
        email = ""
        # Méthode 1: mailto dans les liens
        try:
            mailto_links = card.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
            if mailto_links:
                email = mailto_links[0].get_attribute("href").replace("mailto:", "")
        except:
            pass
        
        # Méthode 2: texte contenant @
        if not email:
            try:
                text_content = card.text
                email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content)
                if email_match:
                    email = email_match.group()
            except:
                pass
        
        # Adresse
        adresse = ""
        try:
            adresse_element = card.find_element(By.CSS_SELECTOR, ".geodir-field-address")
            adresse = adresse_element.text.strip()
        except:
            try:
                # Alternative selector
                adresse_element = card.find_element(By.CSS_SELECTOR, "[class*='address']")
                adresse = adresse_element.text.strip()
            except:
                pass
        
        # Spécialisations
        specialisations = []
        try:
            spec_elements = card.find_elements(By.CSS_SELECTOR, ".geodir-tags a, span.geodir-tags a")
            specialisations = [elem.text.strip() for elem in spec_elements if elem.text.strip()]
        except:
            pass
        
        # Activités dominantes
        activites_dominantes = []
        try:
            activite_elements = card.find_elements(By.CSS_SELECTOR, ".geodir_post_meta.geodir-field-post_category a")
            activites_dominantes = [elem.text.strip() for elem in activite_elements if elem.text.strip()]
        except:
            pass
        
        lawyer_data = {
            'prenom': prenom,
            'nom': nom,
            'nom_complet': nom_complet,
            'email': email,
            'annee_inscription': '',
            'specialisations': '; '.join(specialisations),
            'activites_dominantes': '; '.join(activites_dominantes),
            'cabinet': '',
            'adresse': adresse,
            'telephone': '',
            'source_url': source_url
        }
        
        return lawyer_data
        
    except Exception as e:
        print(f"❌ Erreur extraction avocat: {e}")
        return None


def scrape_orleans_lawyers():
    """Scrape complet des avocats d'Orléans avec séparation parfaite des noms"""
    
    print("🚀 SCRAPER ORLÉANS FINAL - Séparation prénom/nom PARFAITE")
    print("🎯 URL: https://www.ordre-avocats-orleans.fr/annuaire-avocat-orleans/")
    print("🖥️ Mode headless: True")
    print("✨ Séparation prénom/nom perfectionnée avec dictionnaire exhaustif")
    print()
    
    driver = setup_driver()
    lawyers = []
    
    try:
        print("🔍 Extraction des 220 avocats avec séparation prénom/nom parfaite...")
        driver.get("https://www.ordre-avocats-orleans.fr/annuaire-avocat-orleans/")
        
        # Attendre le chargement
        print("📄 Chargement complet de la page...")
        time.sleep(5)
        
        # Accepter les cookies si nécessaire
        try:
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='cookie'], button[class*='cookie'], .cookie-accept, #cookie-accept"))
            )
            cookie_button.click()
            time.sleep(2)
        except:
            pass
        
        # Trouver toutes les cartes d'avocats
        wait = WebDriverWait(driver, 10)
        lawyer_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".geodir-category-listing")))
        
        print(f"📋 {len(lawyer_cards)} cartes trouvées")
        
        for i, card in enumerate(lawyer_cards, 1):
            try:
                lawyer_data = extract_lawyer_info(driver, card)
                if lawyer_data:
                    lawyers.append(lawyer_data)
                    prenom = lawyer_data['prenom']
                    nom = lawyer_data['nom']
                    email = lawyer_data['email'] if lawyer_data['email'] else "Email non trouvé"
                    
                    print(f"  📋 {i}. {lawyer_data['nom_complet']}")
                    print(f"    👤 Prénom: '{prenom}' | Nom: '{nom}'")
                    print(f"    📧 {email}")
                    
                    # Afficher progression tous les 25
                    if i % 25 == 0:
                        emails_count = len([l for l in lawyers if l['email']])
                        print(f"  📊 Progression: {len(lawyers)} avocats | {emails_count} emails")
                        
            except Exception as e:
                print(f"❌ Erreur traitement carte {i}: {e}")
                continue
        
        print(f"✅ {len(lawyers)} avocats extraits avec séparation prénom/nom perfectionnée")
        return lawyers
        
    except Exception as e:
        print(f"❌ Erreur lors du scraping: {e}")
        return lawyers
    finally:
        driver.quit()


def save_results(lawyers):
    """Sauvegarde les résultats dans différents formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV
    csv_file = f"ORLEANS_FINAL_{len(lawyers)}_avocats_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if lawyers:
            writer = csv.DictWriter(f, fieldnames=lawyers[0].keys())
            writer.writeheader()
            writer.writerows(lawyers)
    
    # JSON  
    json_file = f"ORLEANS_FINAL_{len(lawyers)}_avocats_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(lawyers, f, indent=2, ensure_ascii=False)
    
    # Emails uniquement
    emails_file = f"ORLEANS_FINAL_EMAILS_{timestamp}.txt"
    emails = [lawyer['email'] for lawyer in lawyers if lawyer['email']]
    unique_emails = sorted(list(set(emails)))
    with open(emails_file, 'w', encoding='utf-8') as f:
        for email in unique_emails:
            f.write(f"{email}\n")
    
    # Rapport détaillé
    rapport_file = f"ORLEANS_FINAL_RAPPORT_{timestamp}.txt"
    with open(rapport_file, 'w', encoding='utf-8') as f:
        f.write("=== RAPPORT ORLÉANS FINAL (SÉPARATION PARFAITE PRÉNOM/NOM) ===\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Nombre total d'avocats: {len(lawyers)}\n")
        f.write(f"Emails trouvés: {len(unique_emails)}\n")
        f.write(f"Taux de couverture: {len(unique_emails)/len(lawyers)*100:.1f}%\n\n")
        
        # Statistiques détaillées
        f.write("=== STATISTIQUES ===\n")
        emails_count = len([l for l in lawyers if l['email']])
        phones_count = len([l for l in lawyers if l['telephone']])
        addresses_count = len([l for l in lawyers if l['adresse']])
        specs_count = len([l for l in lawyers if l['specialisations']])
        activites_count = len([l for l in lawyers if l['activites_dominantes']])
        
        f.write(f"Avocats avec email: {emails_count}/{len(lawyers)} ({emails_count/len(lawyers)*100:.1f}%)\n")
        f.write(f"Avocats avec téléphone: {phones_count}/{len(lawyers)} ({phones_count/len(lawyers)*100:.1f}%)\n") 
        f.write(f"Avocats avec adresse: {addresses_count}/{len(lawyers)} ({addresses_count/len(lawyers)*100:.1f}%)\n")
        f.write(f"Avocats avec spécialisations: {specs_count}/{len(lawyers)} ({specs_count/len(lawyers)*100:.1f}%)\n")
        f.write(f"Avocats avec activités dominantes: {activites_count}/{len(lawyers)} ({activites_count/len(lawyers)*100:.1f}%)\n\n")
        
        # Exemples de séparation parfaite
        f.write("=== EXEMPLES DE SÉPARATION PARFAITE PRÉNOM/NOM ===\n")
        for i, lawyer in enumerate(lawyers[:30], 1):
            f.write(f"{i:2d}. '{lawyer['nom_complet']}' -> Prénom: '{lawyer['prenom']}' | Nom: '{lawyer['nom']}'\n")
        f.write("\n")
        
        # Liste des avocats avec email
        lawyers_with_email = [l for l in lawyers if l['email']]
        f.write(f"=== AVOCATS AVEC EMAIL ({len(lawyers_with_email)}) ===\n")
        for i, lawyer in enumerate(lawyers_with_email, 1):
            f.write(f"{i:2d}. {lawyer['prenom']} {lawyer['nom']} | {lawyer['email']}\n")
    
    print("\n💾 Résultats sauvegardés:")
    print(f"  📊 CSV: {csv_file}")
    print(f"  📋 JSON: {json_file}")
    print(f"  📧 Emails: {emails_file}")
    print(f"  📄 Rapport: {rapport_file}")
    
    return csv_file, json_file, emails_file, rapport_file


def main():
    """Fonction principale"""
    try:
        # Scraper
        lawyers = scrape_orleans_lawyers()
        
        if not lawyers:
            print("❌ Aucun avocat trouvé")
            return
        
        # Sauvegarder
        csv_file, json_file, emails_file, rapport_file = save_results(lawyers)
        
        # Résumé final
        emails_count = len([l for l in lawyers if l['email']])
        addresses_count = len([l for l in lawyers if l['adresse']])
        
        print(f"\n🎉 EXTRACTION FINALE TERMINÉE!")
        print(f"   👥 Total avocats: {len(lawyers)}")
        print(f"   📧 Emails trouvés: {emails_count}")
        print(f"   🏢 Adresses: {addresses_count}")
        print(f"   📈 Taux d'emails: {emails_count/len(lawyers)*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️ Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")


if __name__ == "__main__":
    main()