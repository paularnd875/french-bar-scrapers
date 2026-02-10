#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

def scrape_caen_lawyers_final():
    """
    Scraper final pour l'annuaire des avocats du barreau de Caen
    """
    base_url = "https://www.barreau-caen.com"
    annuaire_url = f"{base_url}/fr/annuaire"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
    })
    
    all_lawyers = []
    
    def extract_lawyer_data(lawyer_div):
        """
        Extraire les données d'un avocat depuis sa div
        """
        lawyer_info = {}
        
        # Extraction du nom depuis le h3, h4, h5 ou lien
        name_elem = lawyer_div.find(['h3', 'h4', 'h5']) or lawyer_div.find('a')
        if name_elem:
            full_name = name_elem.get_text(strip=True)
            lawyer_info['nom_complet'] = full_name
            
            # Séparer prénom et nom (format: NOM Prénom)
            if ' ' in full_name:
                parts = full_name.split()
                if len(parts) >= 2:
                    lawyer_info['nom'] = parts[0]  # Premier mot = nom de famille
                    lawyer_info['prenom'] = ' '.join(parts[1:])  # Reste = prénom(s)
                else:
                    lawyer_info['nom'] = full_name
                    lawyer_info['prenom'] = ''
            else:
                lawyer_info['nom'] = full_name
                lawyer_info['prenom'] = ''
        
        # Extraction email
        email_elem = lawyer_div.find('a', href=re.compile(r'mailto:'))
        if email_elem:
            lawyer_info['email'] = email_elem.get('href').replace('mailto:', '')
        
        # Extraction téléphone
        phone_elem = lawyer_div.find('a', href=re.compile(r'tel:'))
        if phone_elem:
            phone = phone_elem.get('href').replace('tel:', '')
            # Formater le numéro de téléphone
            if len(phone) == 10:
                phone_formatted = f"{phone[:2]} {phone[2:4]} {phone[4:6]} {phone[6:8]} {phone[8:]}"
                lawyer_info['telephone'] = phone_formatted
            else:
                lawyer_info['telephone'] = phone
        
        # Extraction adresse depuis le texte de la div
        div_text = lawyer_div.get_text()
        
        # Chercher code postal + ville
        postal_match = re.search(r'(\d{5})\s+([A-Z][A-Za-zÀ-ÿ\s\-\']+)', div_text)
        if postal_match:
            lawyer_info['code_postal'] = postal_match.group(1)
            lawyer_info['ville'] = postal_match.group(2).strip()
        
        # Chercher l'adresse rue/avenue/place
        address_match = re.search(r'(\d+.*?)(?=\d{5})', div_text)
        if address_match:
            potential_address = address_match.group(1).strip()
            # Nettoyer l'adresse
            lines = potential_address.split('\n')
            clean_address = []
            for line in lines:
                line = line.strip()
                if (line and 
                    not '@' in line and 
                    not line.startswith('0') and
                    not line.startswith('Voir') and
                    len(line) > 2):
                    # Vérifier si c'est pas le nom de l'avocat
                    if 'nom_complet' not in lawyer_info or lawyer_info['nom_complet'].lower() not in line.lower():
                        clean_address.append(line)
            
            if clean_address:
                lawyer_info['adresse'] = ', '.join(clean_address)
        
        # Lien vers la fiche
        fiche_elem = lawyer_div.find('a', string=re.compile(r'Voir.*fiche'))
        if fiche_elem:
            lawyer_info['lien_fiche'] = urljoin(base_url, fiche_elem.get('href'))
        
        return lawyer_info
    
    try:
        print("=== Scraping de l'annuaire du barreau de Caen ===")
        
        # Test avec la première page
        print("\n--- Test avec la page A ---")
        page_a_url = f"{annuaire_url}?page=A"
        response = session.get(page_a_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher les divs qui contiennent des avocats
        # 1. Par classe spécifique
        lawyer_divs = soup.find_all('div', class_=lambda x: x and 'annuaire' in ' '.join(x) and 'listview' in ' '.join(x))
        print(f"Méthode 1 - Divs avec classes 'annuaire' et 'listview': {len(lawyer_divs)}")
        
        # 2. Si pas trouvé, chercher par email/téléphone
        if len(lawyer_divs) == 0:
            all_divs = soup.find_all('div')
            lawyer_divs = []
            for div in all_divs:
                if (div.find('a', href=re.compile(r'mailto:')) and 
                    div.find('a', href=re.compile(r'tel:'))):
                    lawyer_divs.append(div)
            print(f"Méthode 2 - Divs avec email ET téléphone: {len(lawyer_divs)}")
        
        # Traiter les premiers avocats pour test
        test_lawyers = []
        for lawyer_div in lawyer_divs[:5]:
            lawyer_data = extract_lawyer_data(lawyer_div)
            if lawyer_data.get('nom_complet'):
                test_lawyers.append(lawyer_data)
                print(f"✅ {lawyer_data.get('nom_complet', 'N/A')} | {lawyer_data.get('email', 'N/A')} | {lawyer_data.get('telephone', 'N/A')} | {lawyer_data.get('ville', 'N/A')}")
        
        if test_lawyers:
            print(f"\n🎉 Test réussi! {len(test_lawyers)} avocats extraits")
            
            # Traiter toute la page A
            for lawyer_div in lawyer_divs:
                lawyer_data = extract_lawyer_data(lawyer_div)
                if lawyer_data.get('nom_complet'):
                    all_lawyers.append(lawyer_data)
            
            print(f"Page A: {len(all_lawyers)} avocats extraits")
            
            # Traiter les autres lettres
            letters = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z']
            
            for letter in letters:
                try:
                    print(f"\n--- Traitement de la page {letter} ---")
                    page_url = f"{annuaire_url}?page={letter}"
                    response = session.get(page_url)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Utiliser la même méthode que pour la page A
                    lawyer_divs = soup.find_all('div', class_=lambda x: x and 'annuaire' in ' '.join(x) and 'listview' in ' '.join(x))
                    
                    if len(lawyer_divs) == 0:
                        all_divs = soup.find_all('div')
                        lawyer_divs = []
                        for div in all_divs:
                            if (div.find('a', href=re.compile(r'mailto:')) and 
                                div.find('a', href=re.compile(r'tel:'))):
                                lawyer_divs.append(div)
                    
                    page_count = 0
                    for lawyer_div in lawyer_divs:
                        lawyer_data = extract_lawyer_data(lawyer_div)
                        if lawyer_data.get('nom_complet'):
                            all_lawyers.append(lawyer_data)
                            page_count += 1
                    
                    print(f"Page {letter}: {page_count} avocats (total: {len(all_lawyers)})")
                    time.sleep(0.3)  # Pause respectueuse
                    
                except Exception as e:
                    print(f"Erreur sur la page {letter}: {e}")
                    continue
        else:
            print("❌ Test échoué. Analyse détaillée...")
            # Analyser la structure
            emails = soup.find_all('a', href=re.compile(r'mailto:'))
            phones = soup.find_all('a', href=re.compile(r'tel:'))
            print(f"Emails dans la page: {len(emails)}")
            print(f"Téléphones dans la page: {len(phones)}")
            
            if emails:
                print("Premier email parent div:")
                parent = emails[0].find_parent('div')
                if parent:
                    print(f"Classes: {parent.get('class', [])}")
                    print(f"Contenu: {parent.get_text(strip=True)[:200]}")
        
        return all_lawyers
        
    except Exception as e:
        print(f"Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return all_lawyers

def save_to_csv(lawyers_data, filename='avocats_caen_complet.csv'):
    """
    Sauvegarder les données dans un fichier CSV
    """
    if not lawyers_data:
        print("Aucune donnée à sauvegarder")
        return False
    
    # Déterminer toutes les colonnes disponibles
    all_columns = set()
    for lawyer in lawyers_data:
        all_columns.update(lawyer.keys())
    
    # Ordre des colonnes préféré
    preferred_order = ['nom_complet', 'nom', 'prenom', 'email', 'telephone', 'adresse', 'code_postal', 'ville', 'lien_fiche']
    columns = []
    
    for col in preferred_order:
        if col in all_columns:
            columns.append(col)
            all_columns.remove(col)
    
    columns.extend(sorted(all_columns))
    
    filepath = f'/Users/paularnould/{filename}'
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for lawyer in lawyers_data:
            writer.writerow(lawyer)
    
    print(f"\n✅ Fichier CSV créé: {filename}")
    print(f"📊 {len(lawyers_data)} avocats sauvegardés avec {len(columns)} colonnes")
    print(f"📂 Chemin: {filepath}")
    
    # Afficher un échantillon
    print("\n📋 Échantillon des données:")
    for i, lawyer in enumerate(lawyers_data[:3]):
        print(f"  {i+1}. {lawyer.get('nom_complet', 'N/A')} - {lawyer.get('email', 'N/A')}")
    
    return True

if __name__ == "__main__":
    lawyers = scrape_caen_lawyers_final()
    if lawyers:
        save_to_csv(lawyers)
        print(f"\n🎯 SUCCÈS: {len(lawyers)} avocats du barreau de Caen extraits!")
    else:
        print("\n❌ Aucun avocat extrait. Vérifiez la structure du site.")