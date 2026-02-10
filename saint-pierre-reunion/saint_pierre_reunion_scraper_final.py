#!/usr/bin/env python3
"""
Scraper pour le Barreau de Saint-Pierre Réunion
Extrait toutes les informations des avocats via l'API JSON
"""

import requests
import json
import csv
import time
from datetime import datetime
import urllib3

# Désactiver les warnings SSL pour les certificats auto-signés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BarreauSaintPierreReunionScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-saint-pierre-reunion.re"
        self.api_url = f"{self.base_url}/contact/advancedsearch.json"
        self.session = requests.Session()
        # Headers pour simuler un navigateur
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': f'{self.base_url}/annuaire.html?menu=1'
        })
        
        self.lawyers = []
        
    def get_lawyers_page(self, offset=0, limit=6):
        """Récupère une page d'avocats via l'API"""
        params = {
            'conditionals[0][0]': 'user',
            'conditionals[0][1]': 'isnot', 
            'conditionals[0][2]': 'null',
            'conditionals[1][0]': 'contact.user.group.name',
            'conditionals[1][1]': '=',
            'conditionals[1][2]': 'utilisateurs',
            'conditionals[2][0]': 'status',
            'conditionals[2][1]': '=',
            'conditionals[2][2]': 'ACTIVE',
            'conditionals[3][0]': 'trashed',
            'conditionals[3][1]': '=',
            'conditionals[3][2]': 'false',
            'limit': str(limit),
            'offset': str(offset),
            'order': 'lastname asc'
        }
        
        try:
            print(f"Récupération des avocats - offset: {offset}")
            response = self.session.get(self.api_url, params=params, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur lors de la récupération de la page offset {offset}: {e}")
            return None
    
    def clean_phone_number(self, phone):
        """Nettoie et formate les numéros de téléphone"""
        if not phone:
            return ""
        # Supprime les espaces et caractères spéciaux
        phone = phone.strip().replace(" ", "").replace("-", "").replace(".", "")
        return phone
    
    def extract_lawyer_info(self, lawyer_data):
        """Extrait et nettoie les informations d'un avocat"""
        if not lawyer_data:
            return None
            
        # Ignorer l'administrateur
        if lawyer_data.get('firstname', '').strip() == 'Administrateur':
            return None
            
        # Construire l'adresse complète
        address_parts = []
        if lawyer_data.get('address1'):
            address_parts.append(lawyer_data['address1'].strip())
        if lawyer_data.get('address2'):
            address_parts.append(lawyer_data['address2'].strip())
        
        full_address = ", ".join(address_parts) if address_parts else ""
        
        # Construire l'adresse avec code postal et ville
        location_parts = []
        if lawyer_data.get('cp'):
            location_parts.append(lawyer_data['cp'].strip())
        if lawyer_data.get('city'):
            location_parts.append(lawyer_data['city'].strip())
        
        full_location = " ".join(location_parts) if location_parts else ""
        
        return {
            'nom': lawyer_data.get('lastname', '').strip(),
            'prenom': lawyer_data.get('firstname', '').strip(),
            'nom_complet': f"{lawyer_data.get('firstname', '').strip()} {lawyer_data.get('lastname', '').strip()}".strip(),
            'email': lawyer_data.get('email', '').strip(),
            'adresse': full_address,
            'code_postal': lawyer_data.get('cp', '').strip(),
            'ville': lawyer_data.get('city', '').strip(),
            'adresse_complete': f"{full_address}, {full_location}".strip(', '),
            'telephone_fixe': self.clean_phone_number(lawyer_data.get('telfixe', '')),
            'telephone_mobile': self.clean_phone_number(lawyer_data.get('telgsm', '')),
            'fax': self.clean_phone_number(lawyer_data.get('fax', '')),
            'site_web': lawyer_data.get('websiteurl', '').strip(),
            'date_creation': lawyer_data.get('creation_date', '').strip(),
            'id_contact': lawyer_data.get('id', ''),
            'pays': lawyer_data.get('country', '').strip()
        }
    
    def scrape_all_lawyers(self):
        """Récupère tous les avocats du barreau"""
        print("Début du scraping du Barreau de Saint-Pierre Réunion...")
        
        # Première requête pour connaître le nombre total
        first_page = self.get_lawyers_page(offset=0, limit=6)
        if not first_page:
            print("Impossible de récupérer la première page")
            return False
            
        total_lawyers = first_page.get('AvailableResults', 0)
        print(f"Nombre total d'avocats à récupérer: {total_lawyers}")
        
        if total_lawyers == 0:
            print("Aucun avocat trouvé")
            return False
        
        # Récupérer tous les avocats par batch
        offset = 0
        limit = 50  # Récupérer plus d'avocats par requête pour être plus efficace
        
        while offset < total_lawyers:
            page_data = self.get_lawyers_page(offset=offset, limit=limit)
            if not page_data or 'Result' not in page_data:
                print(f"Erreur lors de la récupération à l'offset {offset}")
                break
                
            lawyers_data = page_data['Result']
            
            for lawyer_data in lawyers_data:
                lawyer_info = self.extract_lawyer_info(lawyer_data)
                if lawyer_info:  # Ignore les entrées invalides ou administrateur
                    self.lawyers.append(lawyer_info)
                    print(f"✓ {lawyer_info['nom_complet']} - {lawyer_info['email']}")
            
            offset += limit
            # Pause pour éviter de surcharger le serveur
            time.sleep(0.5)
        
        print(f"\nScraping terminé! {len(self.lawyers)} avocats récupérés")
        return True
    
    def save_to_csv(self, filename):
        """Sauvegarde les données en CSV"""
        if not self.lawyers:
            print("Aucune donnée à sauvegarder")
            return
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'nom', 'prenom', 'nom_complet', 'email', 'adresse', 'code_postal', 
                'ville', 'adresse_complete', 'telephone_fixe', 'telephone_mobile', 
                'fax', 'site_web', 'date_creation', 'id_contact', 'pays'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers)
            
        print(f"Données sauvegardées en CSV: {filename}")
    
    def save_to_json(self, filename):
        """Sauvegarde les données en JSON"""
        if not self.lawyers:
            print("Aucune donnée à sauvegarder")
            return
            
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers, jsonfile, indent=2, ensure_ascii=False)
            
        print(f"Données sauvegardées en JSON: {filename}")
    
    def run(self):
        """Exécute le scraping complet"""
        if self.scrape_all_lawyers():
            # Générer les noms de fichier avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_filename = f"barreau_saint_pierre_reunion_{timestamp}.csv"
            json_filename = f"barreau_saint_pierre_reunion_{timestamp}.json"
            
            # Sauvegarder les résultats
            self.save_to_csv(csv_filename)
            self.save_to_json(json_filename)
            
            # Afficher un résumé
            print(f"\n=== RÉSUMÉ ===")
            print(f"Total d'avocats extraits: {len(self.lawyers)}")
            print(f"Avocats avec email: {len([l for l in self.lawyers if l['email']])}")
            print(f"Avocats avec téléphone: {len([l for l in self.lawyers if l['telephone_fixe'] or l['telephone_mobile']])}")
            print(f"Fichiers générés: {csv_filename}, {json_filename}")
            
            return True
        return False

if __name__ == "__main__":
    scraper = BarreauSaintPierreReunionScraper()
    scraper.run()