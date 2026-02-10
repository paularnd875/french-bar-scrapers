#!/usr/bin/env python3
"""
Scraper Arras focalisé sur les vrais profils d'avocats
Test avec extraction des informations spécifiques
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
import csv

class ArrasFocusedScraper:
    def __init__(self):
        self.base_url = "https://avocatsarras.com"
        self.annuaire_url = "https://avocatsarras.com/annuaire/"
        self.session = requests.Session()
        self.lawyers_data = []
        
        # Headers optimisés
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
    
    def get_page_content(self, url):
        """Récupère le contenu d'une page avec gestion d'erreurs"""
        try:
            print(f"📡 GET: {url}")
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            print(f"✅ OK ({response.status_code})")
            return response.text
        except Exception as e:
            print(f"❌ Erreur {url}: {e}")
            return None
    
    def get_real_lawyer_links(self):
        """Récupère seulement les vrais liens d'avocats"""
        content = self.get_page_content(self.annuaire_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Rechercher spécifiquement les liens contenant /specialite-avocat/
        lawyer_links = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if '/specialite-avocat/' in href and 'avocatsarras.com' in href:
                text = link.get_text(strip=True)
                # Vérifier que le texte ressemble à un nom d'avocat (2 mots minimum)
                if len(text.split()) >= 2 and not any(word in text.lower() for word in ['accueil', 'contact', 'mentions']):
                    lawyer_links.append({
                        'url': href,
                        'name': text
                    })
                    print(f"👤 Avocat trouvé: {text} - {href}")
        
        return lawyer_links[:5]  # Limiter pour le test
    
    def extract_detailed_lawyer_info(self, lawyer_info):
        """Extraction détaillée des informations d'avocat"""
        url = lawyer_info['url']
        expected_name = lawyer_info['name']
        
        content = self.get_page_content(url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Structure complète des données
        lawyer_data = {
            "url": url,
            "nom_complet": expected_name,
            "prenom": "",
            "nom": "",
            "email": "",
            "telephone": "",
            "fax": "",
            "adresse_complete": "",
            "specialisations": [],
            "annee_inscription": "",
            "structure_cabinet": "",
            "description": "",
            "langues": [],
            "diplomes": []
        }
        
        print(f"\n🔍 Extraction pour: {expected_name}")
        
        # 1. Extraction des emails (priorité aux liens mailto)
        emails = set()
        
        # Mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link.get('href', '').lower().replace('mailto:', '').strip()
            if email and '@' in email:
                emails.add(email)
                
        # Regex dans le texte
        text_content = soup.get_text()
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        found_emails = re.findall(email_pattern, text_content)
        for email in found_emails:
            if '.com' in email or '.fr' in email:  # Filtrer les emails valides
                emails.add(email.lower())
        
        if emails:
            lawyer_data["email"] = list(emails)[0]  # Prendre le premier
            print(f"📧 Email: {lawyer_data['email']}")
        
        # 2. Extraction du téléphone
        phones = set()
        phone_patterns = [
            r'(\+33|0)[1-9][\s\.\-]?(?:[0-9][\s\.\-]?){8}',
            r'(\+33|0)[1-9](?:[0-9]){8}',
            r'0[1-9][\s\.\-](?:[0-9][\s\.\-]){8}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content.replace(' ', '').replace('.', '').replace('-', ''))
            for match in matches:
                phone = str(match)
                if len(phone) >= 9:
                    phones.add(phone)
        
        if phones:
            lawyer_data["telephone"] = list(phones)[0]
            print(f"📞 Téléphone: {lawyer_data['telephone']}")
        
        # 3. Extraction du fax (similaire au téléphone mais recherche "fax")
        fax_context = re.findall(r'fax[\s:]*([0-9\s\.\-\+]{10,})', text_content, re.IGNORECASE)
        if fax_context:
            clean_fax = re.sub(r'[^\d\+]', '', fax_context[0])
            if len(clean_fax) >= 9:
                lawyer_data["fax"] = clean_fax
                print(f"📠 Fax: {lawyer_data['fax']}")
        
        # 4. Extraction de l'adresse
        address_indicators = ['rue', 'avenue', 'place', 'boulevard', 'allée', 'impasse']
        paragraphs = soup.find_all(['p', 'div'], string=re.compile('|'.join(address_indicators), re.I))
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if any(indicator in text.lower() for indicator in address_indicators) and len(text) < 200:
                lawyer_data["adresse_complete"] = text
                print(f"🏠 Adresse: {text}")
                break
        
        # 5. Extraction des spécialisations
        specializations = set()
        
        # Recherche dans les titres et listes
        spec_elements = soup.find_all(['h3', 'h4', 'li', 'p'], 
                                     string=re.compile(r'(droit|spécialis|compétenc|domain)', re.I))
        
        droit_keywords = [
            'droit pénal', 'droit civil', 'droit commercial', 'droit des affaires',
            'droit de la famille', 'droit immobilier', 'droit du travail',
            'droit fiscal', 'droit des sociétés', 'droit public', 'droit administratif'
        ]
        
        for keyword in droit_keywords:
            if keyword.lower() in text_content.lower():
                specializations.add(keyword.title())
        
        lawyer_data["specialisations"] = list(specializations)[:5]  # Max 5
        if lawyer_data["specialisations"]:
            print(f"⚖️ Spécialisations: {', '.join(lawyer_data['specialisations'])}")
        
        # 6. Extraction de l'année d'inscription au barreau
        inscription_patterns = [
            r'inscrit[e]?.*?barreau.*?([1-2][0-9]{3})',
            r'barreau.*?([1-2][0-9]{3})',
            r'([1-2][0-9]{3}).*?inscrit',
            r'serment.*?([1-2][0-9]{3})'
        ]
        
        for pattern in inscription_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                year = str(match)
                if 1950 <= int(year) <= 2025:
                    lawyer_data["annee_inscription"] = year
                    print(f"📅 Inscription: {year}")
                    break
            if lawyer_data["annee_inscription"]:
                break
        
        # 7. Extraction du cabinet/structure
        cabinet_patterns = [
            r'cabinet\s+([^\.]+)',
            r'société\s+([^\.]+)',
            r'scp\s+([^\.]+)',
            r'selarl\s+([^\.]+)'
        ]
        
        for pattern in cabinet_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                cabinet = matches[0].strip()[:100]  # Limiter la taille
                lawyer_data["structure_cabinet"] = cabinet
                print(f"🏢 Cabinet: {cabinet}")
                break
        
        # 8. Séparation prénom/nom
        if lawyer_data["nom_complet"]:
            # Nettoyer le nom
            clean_name = lawyer_data["nom_complet"]
            clean_name = re.sub(r'(maitre|me|avocat)', '', clean_name, flags=re.IGNORECASE).strip()
            
            name_parts = clean_name.split()
            if len(name_parts) >= 2:
                # Dernier mot = nom, le reste = prénom(s)
                lawyer_data["nom"] = name_parts[-1].upper()
                lawyer_data["prenom"] = " ".join(name_parts[:-1]).title()
            else:
                lawyer_data["nom"] = clean_name.upper()
            
            print(f"👤 Nom parsé: {lawyer_data['prenom']} {lawyer_data['nom']}")
        
        return lawyer_data
    
    def run_focused_test(self):
        """Lance le test focalisé sur les vrais avocats"""
        try:
            print("🚀 Test focalisé - Extraction avocats Arras")
            print("="*50)
            
            # Récupérer les liens d'avocats réels
            lawyer_links = self.get_real_lawyer_links()
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                return False
            
            print(f"\n📋 {len(lawyer_links)} avocats à traiter:")
            for i, lawyer in enumerate(lawyer_links, 1):
                print(f"   {i}. {lawyer['name']}")
            
            # Traiter chaque avocat
            for i, lawyer_info in enumerate(lawyer_links, 1):
                print(f"\n{'='*50}")
                print(f"📄 AVOCAT {i}/{len(lawyer_links)}")
                print(f"{'='*50}")
                
                result = self.extract_detailed_lawyer_info(lawyer_info)
                
                if result:
                    self.lawyers_data.append(result)
                    print(f"✅ Extraction réussie")
                else:
                    print(f"❌ Échec extraction")
                
                # Pause entre les requêtes
                if i < len(lawyer_links):
                    print("⏳ Pause de 2 secondes...")
                    time.sleep(2)
            
            # Sauvegarde
            self.save_detailed_results()
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur pendant le test: {e}")
            return False
    
    def save_detailed_results(self):
        """Sauvegarde détaillée des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f"arras_focused_test_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        # CSV détaillé
        csv_file = f"arras_focused_test_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = [
                'nom_complet', 'prenom', 'nom', 'email', 'telephone', 'fax',
                'adresse_complete', 'specialisations', 'annee_inscription',
                'structure_cabinet', 'url'
            ]
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    row = {k: v for k, v in lawyer.items() if k in fieldnames}
                    row['specialisations'] = "; ".join(lawyer.get('specialisations', []))
                    writer.writerow(row)
        
        print(f"\n{'='*50}")
        print(f"💾 RÉSULTATS SAUVEGARDÉS")
        print(f"{'='*50}")
        print(f"📄 JSON: {json_file}")
        print(f"📊 CSV:  {csv_file}")
        print(f"📈 Total: {len(self.lawyers_data)} avocats")
        
        # Résumé détaillé
        print(f"\n📋 RÉSUMÉ DES EXTRACTIONS:")
        print(f"{'='*50}")
        
        for i, lawyer in enumerate(self.lawyers_data, 1):
            print(f"\n{i}. {lawyer['nom_complet']}")
            print(f"   👤 Nom: {lawyer['prenom']} {lawyer['nom']}")
            print(f"   📧 Email: {lawyer['email'] or 'Non trouvé'}")
            print(f"   📞 Téléphone: {lawyer['telephone'] or 'Non trouvé'}")
            print(f"   📅 Inscription: {lawyer['annee_inscription'] or 'Non trouvée'}")
            print(f"   ⚖️ Spécialisations: {len(lawyer['specialisations'])} trouvée(s)")
            if lawyer['specialisations']:
                print(f"      → {', '.join(lawyer['specialisations'])}")

def main():
    scraper = ArrasFocusedScraper()
    success = scraper.run_focused_test()
    
    if success:
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS!")
        print("Les données extraites sont maintenant disponibles dans les fichiers CSV et JSON.")
        print("Vérifiez la qualité des extractions avant de lancer le scraping complet.")
    else:
        print("\n❌ Le test a échoué")

if __name__ == "__main__":
    main()