#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau d'Alençon
Extrait les emails personnels réels des avocats (pas les emails génériques)

Auteur: Claude Code
Date: 25/02/2026
URL cible: https://www.barreau-alencon.fr/copie-de-le-barreau
"""

import time
import csv
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def setup_driver():
    """Configuration du driver Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)
    return driver

def clean_text(text):
    """Nettoie le texte extrait"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_name_parts(full_name):
    """Sépare prénom et nom avec gestion des noms composés français"""
    if not full_name:
        return "", ""
    
    name = clean_text(full_name).strip()
    name = re.sub(r'^(Me\s+|Maître\s+|M\.\s+|Mme\s+)', '', name, flags=re.IGNORECASE)
    
    parts = name.split()
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        # Gestion des noms composés avec particules
        if any(word.lower() in ['de', 'du', 'des', 'le', 'la', 'van', 'von'] for word in parts[:-1]):
            for i, word in enumerate(parts):
                if word.lower() in ['de', 'du', 'des', 'le', 'la', 'van', 'von']:
                    return ' '.join(parts[:i]), ' '.join(parts[i:])
        
        return parts[0], ' '.join(parts[1:])

def search_individual_email_intensively(driver, lawyer_name, popup_id):
    """
    Recherche INTENSIVE d'email individuel - ne retourne que les vrais emails personnels
    Exclut automatiquement les emails génériques du barreau
    """
    
    print(f"   🔍 Recherche intensive d'email pour {lawyer_name}")
    
    try:
        # Cliquer sur le popup pour ouvrir les détails de l'avocat
        link_elements = driver.find_elements(By.CSS_SELECTOR, f"a[data-popupid='{popup_id}']")
        if link_elements:
            link = link_elements[0]
            
            # Cliquer pour ouvrir le popup
            driver.execute_script("arguments[0].click();", link)
            time.sleep(4)  # Attendre que le popup se charge
            
            # Récupérer TOUT le contenu de la page après le clic
            body_text = driver.find_element(By.TAG_NAME, 'body').text
            
            # Chercher TOUS les emails dans le contenu
            all_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', body_text)
            
            print(f"   📧 Emails trouvés dans la page: {all_emails}")
            
            # Filtrer pour exclure les emails génériques du barreau
            generic_emails = [
                'alencon@ordre-avocats.fr',
                'contact@barreau-alencon.fr',
                'info@ordre-avocats.fr'
            ]
            
            personal_emails = []
            for email in all_emails:
                is_generic = False
                for generic in generic_emails:
                    if generic.lower() in email.lower():
                        is_generic = True
                        break
                if not is_generic:
                    personal_emails.append(email)
            
            print(f"   ✅ Emails personnels: {personal_emails}")
            
            # Si on trouve des emails personnels, essayer de déterminer lequel appartient à cet avocat
            if personal_emails:
                # Méthode: chercher l'email qui apparaît près du nom de l'avocat
                for email in personal_emails:
                    # Créer un pattern qui cherche l'email près du nom
                    name_parts = lawyer_name.split()
                    for name_part in name_parts:
                        if len(name_part) > 2:  # Ignorer les petits mots
                            # Chercher si le nom et l'email apparaissent proches dans le texte
                            pattern = f"(.{{0,300}}{re.escape(name_part)}.*?{re.escape(email)}.*?|.*?{re.escape(email)}.*?{re.escape(name_part)}.{{0,300}})"
                            if re.search(pattern, body_text, re.IGNORECASE | re.DOTALL):
                                print(f"   🎯 Email associé trouvé: {email}")
                                return email
                
                # Si pas d'association directe trouvée, prendre le premier email personnel
                print(f"   📋 Premier email personnel: {personal_emails[0]}")
                return personal_emails[0]
            
            # Fermer le popup
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass
    
    except Exception as e:
        print(f"   ❌ Erreur recherche email: {e}")
    
    print(f"   ⚠️ Aucun email personnel trouvé")
    return ""  # Retourner vide si aucun email personnel trouvé

def search_individual_phone(driver, lawyer_name):
    """Recherche téléphone individuel (exclut le téléphone générique du barreau)"""
    try:
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        
        # Chercher tous les téléphones français
        phones = re.findall(r'\b(0[1-9](?:[-.\s]?\d{2}){4})\b', body_text)
        
        # Exclure le téléphone générique du barreau d'Alençon
        personal_phones = [p for p in phones if p != "02 33 26 13 65"]
        
        if personal_phones:
            return personal_phones[0]
    except:
        pass
    
    return ""

def scrape_alencon_lawyers():
    """
    Fonction principale de scraping du Barreau d'Alençon
    Extrait uniquement les emails et téléphones personnels réels
    """
    
    print("🎯 SCRAPER BARREAU D'ALENÇON - EMAILS RÉELS UNIQUEMENT")
    print("=" * 55)
    
    driver = setup_driver()
    
    try:
        # Accéder à la page du barreau d'Alençon
        main_url = "https://www.barreau-alencon.fr/copie-de-le-barreau"
        print(f"🔗 Accès: {main_url}")
        
        driver.get(main_url)
        time.sleep(5)
        
        print(f"📄 Page: {driver.title}")
        
        # Trouver tous les liens d'avocats avec data-popupid
        popup_links = driver.find_elements(By.CSS_SELECTOR, "a[data-popupid]")
        print(f"👥 {len(popup_links)} avocats trouvés")
        
        if not popup_links:
            print("❌ Aucun avocat trouvé")
            return
        
        lawyers_data = []
        
        print(f"🏭 Extraction en cours...")
        
        # Traiter chaque avocat
        for i in range(len(popup_links)):
            link = popup_links[i]
            
            try:
                popup_id = link.get_attribute('data-popupid')
                lawyer_name = clean_text(link.text)
                
                if not lawyer_name or len(lawyer_name) < 3:
                    continue
                
                print(f"\n--- Avocat {i+1}/{len(popup_links)}: {lawyer_name} ---")
                
                # Recherche INTENSIVE d'email personnel uniquement
                personal_email = search_individual_email_intensively(driver, lawyer_name, popup_id)
                personal_phone = search_individual_phone(driver, lawyer_name)
                
                # Séparer prénom/nom avec gestion des noms composés français
                prenom, nom = extract_name_parts(lawyer_name)
                
                # Construire l'enregistrement SANS données génériques
                lawyer_data = {
                    'nom_complet': lawyer_name,
                    'prenom': prenom,
                    'nom': nom,
                    'popup_id': popup_id,
                    'email': personal_email,  # Vide si pas d'email personnel trouvé
                    'telephone': personal_phone,  # Vide si pas de téléphone personnel trouvé
                    'annee_inscription': '',
                    'specialisations': '',
                    'structure': '',
                    'adresse': '',
                    'url_source': main_url
                }
                
                lawyers_data.append(lawyer_data)
                
                # Résumé des données trouvées
                found_items = []
                if personal_email:
                    found_items.append(f"📧 {personal_email}")
                if personal_phone:
                    found_items.append(f"📞 {personal_phone}")
                
                if found_items:
                    print(f"   ✅ Données personnelles: {', '.join(found_items)}")
                else:
                    print(f"   ⚪ Aucune donnée personnelle trouvée")
                
                time.sleep(0.5)  # Pause courte entre chaque avocat
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                continue
        
        # Générer les fichiers de sortie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Compter les vrais emails et téléphones trouvés
        real_emails = [l['email'] for l in lawyers_data if l['email']]
        real_phones = [l['telephone'] for l in lawyers_data if l['telephone']]
        
        print(f"\n📊 RÉSULTATS FINAUX")
        print("=" * 25)
        print(f"Total avocats: {len(lawyers_data)}")
        print(f"Emails personnels trouvés: {len(real_emails)} ({len(real_emails)/len(lawyers_data)*100:.1f}%)")
        print(f"Téléphones personnels trouvés: {len(real_phones)} ({len(real_phones)/len(lawyers_data)*100:.1f}%)")
        print(f"Avocats SANS contact personnel: {len(lawyers_data) - max(len(real_emails), len(real_phones))}")
        
        # CSV complet
        csv_filename = f"ALENCON_FINAL_{len(real_emails)}emails_sur_{len(lawyers_data)}avocats_{timestamp}.csv"
        fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'annee_inscription', 
                     'specialisations', 'structure', 'adresse', 'popup_id', 'url_source']
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lawyers_data)
        
        # JSON complet
        json_filename = f"ALENCON_FINAL_{len(real_emails)}emails_sur_{len(lawyers_data)}avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Liste des emails personnels uniquement
        if real_emails:
            emails_filename = f"ALENCON_EMAILS_PERSONNELS_UNIQUEMENT_{len(real_emails)}_{timestamp}.txt"
            with open(emails_filename, 'w', encoding='utf-8') as emailfile:
                emailfile.write("# EMAILS PERSONNELS UNIQUEMENT - BARREAU D'ALENÇON\n")
                emailfile.write(f"# Extraits le {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                emailfile.write(f"# {len(real_emails)} emails sur {len(lawyers_data)} avocats\n")
                emailfile.write(f"# Taux de réussite: {len(real_emails)/len(lawyers_data)*100:.1f}%\n\n")
                for email in sorted(set(real_emails)):
                    emailfile.write(f"{email}\n")
        
        # Rapport détaillé
        rapport_filename = f"ALENCON_RAPPORT_FINAL_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write("EXTRACTION BARREAU D'ALENÇON - RAPPORT FINAL\n")
            reportfile.write("=" * 50 + "\n\n")
            reportfile.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"URL source: {main_url}\n")
            reportfile.write(f"Script: alencon_scraper_final.py\n\n")
            
            reportfile.write("STATISTIQUES FINALES:\n")
            reportfile.write("-" * 20 + "\n")
            reportfile.write(f"Total avocats: {len(lawyers_data)}\n")
            reportfile.write(f"Emails personnels: {len(real_emails)} ({len(real_emails)/len(lawyers_data)*100:.1f}%)\n")
            reportfile.write(f"Téléphones personnels: {len(real_phones)} ({len(real_phones)/len(lawyers_data)*100:.1f}%)\n")
            reportfile.write(f"Avocats sans contact personnel: {len(lawyers_data) - max(len(real_emails), len(real_phones))}\n\n")
            
            if real_emails:
                reportfile.write("AVOCATS AVEC EMAILS PERSONNELS:\n")
                reportfile.write("-" * 35 + "\n")
                for lawyer in lawyers_data:
                    if lawyer['email']:
                        reportfile.write(f"• {lawyer['nom_complet']} - {lawyer['email']}")
                        if lawyer['telephone']:
                            reportfile.write(f" - {lawyer['telephone']}")
                        reportfile.write("\n")
            
            reportfile.write(f"\nAVOCATS SANS EMAIL PERSONNEL ({len(lawyers_data) - len(real_emails)}):\n")
            reportfile.write("-" * 40 + "\n")
            for lawyer in lawyers_data:
                if not lawyer['email']:
                    reportfile.write(f"• {lawyer['nom_complet']}\n")
        
        print(f"\n📁 FICHIERS GÉNÉRÉS:")
        print(f"   • {csv_filename}")
        print(f"   • {json_filename}")
        if real_emails:
            print(f"   • {emails_filename}")
        print(f"   • {rapport_filename}")
        
        if real_emails:
            print(f"\n✅ EMAILS PERSONNELS EXTRAITS:")
            for email in sorted(set(real_emails)):
                print(f"   📧 {email}")
        
        print(f"\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS !")
        print(f"   📊 {len(real_emails)} emails personnels sur {len(lawyers_data)} avocats")
        print(f"   📈 Taux de réussite: {len(real_emails)/len(lawyers_data)*100:.1f}%")
        
        return lawyers_data
        
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_alencon_lawyers()