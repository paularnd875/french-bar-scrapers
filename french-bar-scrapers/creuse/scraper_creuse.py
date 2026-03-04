#!/usr/bin/env python3
"""
Scraper PRODUCTION pour l'annuaire des avocats du barreau de Creuse
URL: https://cdad-creuse.justice.fr/annuaire-des-professionnels#avocats
Méthode: Requests + BeautifulSoup (HTML statique)

Extraction complète:
- 20 avocats du barreau
- Emails, téléphones, adresses
- Identification du Bâtonnier
- Mode headless (sans interface graphique)

Auteur: French Bar Scrapers
Date: 2026-02-11
"""

import re
import json
import csv
import html
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import os

class CreuseAvocatsScraper:
    def __init__(self):
        self.avocats_data = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def extract_contact_from_popover(self, content):
        """Extraire les informations de contact depuis le contenu du popover"""
        if not content:
            return None
            
        content = html.unescape(content)
        
        # Email
        email_match = re.search(r'mailto:([^"\']+)', content)
        if email_match:
            return {'type': 'email', 'value': email_match.group(1).strip()}
        
        # Téléphone  
        tel_match = re.search(r'tel:([^"\']+)', content)
        if tel_match:
            phone = tel_match.group(1).strip()
            phone_cleaned = re.sub(r'[^\d]', '', phone)
            if len(phone_cleaned) == 10:
                # Formater le numéro français
                phone = f"{phone_cleaned[:2]}.{phone_cleaned[2:4]}.{phone_cleaned[4:6]}.{phone_cleaned[6:8]}.{phone_cleaned[8:]}"
            return {'type': 'telephone', 'value': phone}
        
        # Adresse
        if '<span>' in content and 'mailto:' not in content and 'tel:' not in content:
            address_match = re.search(r'<span>([^<]+)</span>', content)
            if address_match:
                return {'type': 'adresse', 'value': address_match.group(1).strip()}
        
        return None
    
    def parse_name(self, full_name):
        """Parser le nom complet pour extraire prénom et nom"""
        clean_name = full_name.replace('Maître', '').replace('MAITRE', '').strip()
        
        titre = ''
        if 'Bâtonnier' in full_name:
            titre = 'Bâtonnier'
            clean_name = clean_name.replace('- Bâtonnier', '').strip()
        
        nom = ''
        prenom = ''
        
        if clean_name:
            parts = clean_name.split()
            if len(parts) >= 2:
                nom = parts[0]
                prenom = ' '.join(parts[1:])
            else:
                nom = clean_name
        
        return nom, prenom, titre
    
    def is_avocat_card(self, card_soup):
        """Vérifier si la carte correspond à un avocat (pas notaire/commissaire)"""
        # Les avocats ont des boutons btn-primary, notaires ont btn-info
        buttons = card_soup.find_all('button', class_=['btn-primary', 'btn-info', 'btn-danger'])
        primary_buttons = [b for b in buttons if 'btn-primary' in b.get('class', [])]
        return len(primary_buttons) > 0
    
    def extract_avocats_data(self):
        """Extraire toutes les données des avocats depuis la page"""
        print("🌐 Récupération de la page web...")
        
        try:
            response = self.session.get('https://cdad-creuse.justice.fr/annuaire-des-professionnels', timeout=30)
            response.raise_for_status()
            
            print(f"✅ Page récupérée (status: {response.status_code})")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trouver la section avocats
            avocats_section = soup.find('div', id='avocats')
            if not avocats_section:
                print("❌ Section avocats non trouvée")
                return False
            
            print("✅ Section avocats trouvée")
            
            # Trouver le container avec les cartes
            container = avocats_section.find_next_sibling('div', class_='container')
            if not container:
                container = avocats_section.find_parent().find('div', class_='container')
            
            if not container:
                print("❌ Container des avocats non trouvé")
                return False
            
            lawyer_cards = container.find_all('div', class_='col-sm-6')
            print(f"📊 Nombre total de cartes trouvées: {len(lawyer_cards)}")
            
            avocats_count = 0
            for i, card in enumerate(lawyer_cards):
                if not self.is_avocat_card(card):
                    continue
                
                try:
                    name_element = card.find('h4')
                    if not name_element:
                        continue
                        
                    full_name = name_element.text.strip()
                    nom, prenom, titre = self.parse_name(full_name)
                    
                    avocat_data = {
                        'nom_complet': full_name,
                        'nom': nom,
                        'prenom': prenom,
                        'email': '',
                        'telephone': '',
                        'adresse': '',
                        'specialisations': [],
                        'structure': '',
                        'titre': titre,
                        'annee_inscription': ''
                    }
                    
                    # Information sur la structure
                    structure_info = card.find('p')
                    if structure_info:
                        structure_text = structure_info.text.strip()
                        if structure_text:
                            avocat_data['structure'] = structure_text
                    
                    # Informations de contact
                    popover_buttons = card.find_all('button', attrs={'data-bs-toggle': 'popover'})
                    
                    for button in popover_buttons:
                        content = button.get('data-bs-content', '')
                        contact_info = self.extract_contact_from_popover(content)
                        
                        if contact_info:
                            if contact_info['type'] == 'email':
                                avocat_data['email'] = contact_info['value']
                            elif contact_info['type'] == 'telephone':
                                avocat_data['telephone'] = contact_info['value']
                            elif contact_info['type'] == 'adresse':
                                avocat_data['adresse'] = contact_info['value']
                    
                    self.avocats_data.append(avocat_data)
                    avocats_count += 1
                    
                    print(f"✅ Avocat {avocats_count}: {avocat_data['nom_complet']}")
                    if avocat_data['email']:
                        print(f"   📧 {avocat_data['email']}")
                    
                except Exception as e:
                    print(f"⚠️  Erreur avocat {i+1}: {e}")
                    continue
            
            print(f"📊 Total avocats extraits: {len(self.avocats_data)}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction: {e}")
            return False
    
    def save_results(self, output_dir='.'):
        """Sauvegarder les résultats en CSV et JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Créer le répertoire de sortie s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON
        json_filename = os.path.join(output_dir, f"creuse_avocats_{timestamp}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.avocats_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_filename = os.path.join(output_dir, f"creuse_avocats_{timestamp}.csv")
        if self.avocats_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 'titre', 'structure', 'specialisations', 'annee_inscription']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.avocats_data)
        
        # Emails uniquement
        emails_filename = os.path.join(output_dir, f"creuse_emails_{timestamp}.txt")
        with open(emails_filename, 'w', encoding='utf-8') as f:
            emails_found = []
            for avocat in self.avocats_data:
                if avocat.get('email') and avocat['email'] not in emails_found:
                    f.write(f"{avocat['email']}\n")
                    emails_found.append(avocat['email'])
        
        # Rapport complet
        report_filename = os.path.join(output_dir, f"creuse_rapport_{timestamp}.txt")
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION - BARREAU DE CREUSE\n")
            f.write(f"Date extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL source: https://cdad-creuse.justice.fr/annuaire-des-professionnels#avocats\n")
            f.write(f"Méthode: Requests + BeautifulSoup (HTML statique)\n")
            f.write(f"\n" + "="*70 + "\n")
            f.write(f"RÉSULTATS D'EXTRACTION:\n")
            f.write(f"- Nombre total d'avocats: {len(self.avocats_data)}\n")
            f.write(f"- Avocats avec email: {sum(1 for a in self.avocats_data if a.get('email'))}\n")
            f.write(f"- Avocats avec téléphone: {sum(1 for a in self.avocats_data if a.get('telephone'))}\n")
            f.write(f"- Avocats avec adresse: {sum(1 for a in self.avocats_data if a.get('adresse'))}\n")
            f.write(f"- Bâtonnier(s) identifié(s): {sum(1 for a in self.avocats_data if a.get('titre'))}\n")
            
            # Statistiques des domaines email
            emails_with_domain = {}
            for avocat in self.avocats_data:
                if avocat.get('email'):
                    domain = avocat['email'].split('@')[1] if '@' in avocat['email'] else 'invalid'
                    emails_with_domain[domain] = emails_with_domain.get(domain, 0) + 1
            
            if emails_with_domain:
                f.write(f"\nRÉPARTITION DES DOMAINES EMAIL:\n")
                for domain, count in sorted(emails_with_domain.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"- {domain}: {count} avocat(s)\n")
            
            f.write(f"\n" + "="*70 + "\n")
            f.write(f"LISTE COMPLÈTE DES AVOCATS:\n")
            
            for i, avocat in enumerate(self.avocats_data, 1):
                f.write(f"\n{i:2d}. {avocat.get('nom_complet', 'N/A')}\n")
                if avocat.get('prenom') and avocat.get('nom'):
                    f.write(f"     Nom: {avocat['nom']}, Prénom: {avocat['prenom']}\n")
                if avocat.get('email'):
                    f.write(f"     📧 Email: {avocat['email']}\n")
                if avocat.get('telephone'):
                    f.write(f"     📞 Téléphone: {avocat['telephone']}\n")
                if avocat.get('adresse'):
                    f.write(f"     📍 Adresse: {avocat['adresse']}\n")
                if avocat.get('titre'):
                    f.write(f"     🎖️  Titre: {avocat['titre']}\n")
                if avocat.get('structure'):
                    f.write(f"     🏢 Structure: {avocat['structure']}\n")
        
        print(f"\n💾 FICHIERS GÉNÉRÉS:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📊 CSV: {csv_filename}")
        print(f"   📧 Emails: {emails_filename}")
        print(f"   📋 Rapport: {report_filename}")
        
        return {
            'json': json_filename,
            'csv': csv_filename,
            'emails': emails_filename,
            'report': report_filename
        }
    
    def run_extraction(self, output_dir='.'):
        """Exécuter l'extraction complète"""
        print(f"🚀 EXTRACTION BARREAU DE CREUSE")
        print("Méthode: Requests + BeautifulSoup (rapide, headless)")
        print("=" * 60)
        
        try:
            success = self.extract_avocats_data()
            
            if not success:
                print("❌ Échec de l'extraction")
                return False
            
            if not self.avocats_data:
                print("❌ Aucune donnée extraite")
                return False
            
            files = self.save_results(output_dir)
            
            print(f"\n🎉 EXTRACTION TERMINÉE!")
            print(f"📊 {len(self.avocats_data)} avocat(s) extrait(s)")
            print(f"📧 {sum(1 for a in self.avocats_data if a.get('email'))} email(s) trouvé(s)")
            print(f"📞 {sum(1 for a in self.avocats_data if a.get('telephone'))} téléphone(s) trouvé(s)")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur pendant l'extraction: {e}")
            return False

def main():
    """Fonction principale"""
    print("🎯 SCRAPER BARREAU DE CREUSE")
    print("https://cdad-creuse.justice.fr/annuaire-des-professionnels#avocats")
    print("=" * 60)
    
    # Déterminer le répertoire de sortie
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'results')
    
    scraper = CreuseAvocatsScraper()
    success = scraper.run_extraction(output_dir)
    
    if success:
        print("\n✅ MISSION ACCOMPLIE!")
        print(f"📁 Résultats sauvegardés dans: {output_dir}")
    else:
        print("\n❌ Échec de l'extraction")

if __name__ == "__main__":
    main()