#!/usr/bin/env python3
"""
Scraper Arras avec requests/BeautifulSoup - plus simple et rapide
Test initial pour comprendre la structure
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

class ArrasRequestsScraper:
    def __init__(self):
        self.base_url = "https://avocatsarras.com"
        self.annuaire_url = "https://avocatsarras.com/annuaire/"
        self.session = requests.Session()
        self.lawyers_data = []
        
        # Headers pour éviter la détection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_page_content(self, url):
        """Récupère le contenu d'une page"""
        try:
            print(f"📡 Récupération: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            print(f"✅ Status: {response.status_code}")
            return response.text
        except Exception as e:
            print(f"❌ Erreur {url}: {e}")
            return None
    
    def analyze_homepage(self):
        """Analyse la page d'accueil de l'annuaire"""
        content = self.get_page_content(self.annuaire_url)
        if not content:
            return False
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Sauvegarder pour analyse
        with open("arras_homepage_analysis.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        
        print("📄 HTML sauvegardé dans arras_homepage_analysis.html")
        
        # Rechercher des liens d'avocats
        links = soup.find_all('a', href=True)
        lawyer_links = []
        
        for link in links:
            href = link.get('href', '')
            if '/avocat' in href.lower() or '/annuaire' in href.lower():
                full_url = href if href.startswith('http') else self.base_url + href
                if full_url not in lawyer_links:
                    lawyer_links.append(full_url)
                    text = link.get_text(strip=True)[:50]
                    print(f"🔗 Lien trouvé: {full_url} - {text}")
        
        # Analyser la structure générale
        print(f"\n📊 Analyse de la page:")
        print(f"   Total liens: {len(links)}")
        print(f"   Liens avocats potentiels: {len(lawyer_links)}")
        
        # Rechercher des structures spécifiques
        cards = soup.find_all(['div', 'article'], class_=re.compile(r'(card|lawyer|avocat|profile)', re.I))
        print(f"   Cartes/profils trouvés: {len(cards)}")
        
        return lawyer_links[:5]  # Limiter pour le test
    
    def extract_lawyer_info(self, lawyer_url):
        """Extrait les infos d'un avocat avec BeautifulSoup"""
        content = self.get_page_content(lawyer_url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        lawyer_data = {
            "url": lawyer_url,
            "nom_complet": "",
            "prenom": "",
            "nom": "",
            "email": "",
            "telephone": "",
            "specialisations": [],
            "adresse": "",
            "annee_inscription": "",
            "structure": ""
        }
        
        # Extraction du nom depuis le titre
        title = soup.find('title')
        if title:
            lawyer_data["nom_complet"] = title.get_text(strip=True)
            print(f"📋 Titre: {lawyer_data['nom_complet']}")
        
        # Recherche de h1, h2 pour le nom
        headers = soup.find_all(['h1', 'h2', 'h3'])
        for header in headers:
            text = header.get_text(strip=True)
            if len(text) > 5 and any(word in text.lower() for word in ['maître', 'avocat', 'me ']):
                if not lawyer_data["nom_complet"]:
                    lawyer_data["nom_complet"] = text
                    print(f"📋 Nom (header): {text}")
                break
        
        # Extraction email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        if emails:
            lawyer_data["email"] = emails[0]
            print(f"📧 Email: {emails[0]}")
        
        # Recherche mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        for link in mailto_links:
            email = link.get('href', '').replace('mailto:', '')
            if email:
                lawyer_data["email"] = email
                print(f"📧 Email (mailto): {email}")
                break
        
        # Extraction téléphone
        phone_pattern = r'(\+33|0)[1-9](?:[0-9]{8})'
        phones = re.findall(phone_pattern, content.replace(' ', '').replace('.', ''))
        if phones:
            lawyer_data["telephone"] = phones[0]
            print(f"📞 Téléphone: {phones[0]}")
        
        # Recherche année inscription
        year_pattern = r'(inscrit|inscription|barreau).*?([1-2][0-9]{3})|([1-2][0-9]{3}).*(inscrit|inscription|barreau)'
        year_matches = re.findall(year_pattern, content, re.IGNORECASE)
        for match in year_matches:
            year = match[1] or match[2]
            if year and 1950 <= int(year) <= 2024:
                lawyer_data["annee_inscription"] = year
                print(f"📅 Année inscription: {year}")
                break
        
        # Extraction spécialisations
        specialization_keywords = ['droit', 'pénal', 'civil', 'commercial', 'famille', 'immobilier', 'travail', 'fiscal']
        text_content = soup.get_text().lower()
        
        for keyword in specialization_keywords:
            if keyword in text_content:
                # Rechercher le contexte autour du mot-clé
                context_pattern = rf'([^.]*{keyword}[^.]*)'
                contexts = re.findall(context_pattern, text_content, re.IGNORECASE)
                for context in contexts:
                    if len(context) < 100:  # Éviter les phrases trop longues
                        lawyer_data["specialisations"].append(context.strip())
                        break
        
        # Nettoyage des spécialisations
        lawyer_data["specialisations"] = list(set(lawyer_data["specialisations"]))[:3]  # Max 3
        if lawyer_data["specialisations"]:
            print(f"⚖️ Spécialisations: {lawyer_data['specialisations']}")
        
        # Tentative de séparation prénom/nom
        if lawyer_data["nom_complet"]:
            name_clean = lawyer_data["nom_complet"].replace('Maître', '').replace('Me ', '').replace('Avocat', '').strip()
            name_parts = name_clean.split()
            if len(name_parts) >= 2:
                lawyer_data["prenom"] = " ".join(name_parts[:-1])
                lawyer_data["nom"] = name_parts[-1]
            else:
                lawyer_data["nom"] = name_clean
        
        return lawyer_data
    
    def run_test(self):
        """Lance le test avec requests"""
        try:
            print("🚀 Test scraper Arras avec requests/BeautifulSoup")
            
            # Analyse de la page d'accueil
            lawyer_links = self.analyze_homepage()
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                # Test avec URLs manuelles
                test_urls = [
                    "https://avocatsarras.com/annuaire/avocats/droit-penal/maitre-dumont-avocat-arras/",
                    "https://avocatsarras.com/annuaire/avocats/droit-civil/maitre-bernard-avocat-arras/"
                ]
                
                for url in test_urls:
                    print(f"\n🔄 Test manuel avec: {url}")
                    result = self.extract_lawyer_info(url)
                    if result:
                        self.lawyers_data.append(result)
            else:
                # Traitement des liens trouvés
                for i, link in enumerate(lawyer_links, 1):
                    print(f"\n📄 Avocat {i}/{len(lawyer_links)}")
                    result = self.extract_lawyer_info(link)
                    if result:
                        self.lawyers_data.append(result)
                    
                    time.sleep(1)  # Pause pour éviter surcharge
            
            self.save_results()
            return True
            
        except Exception as e:
            print(f"❌ Erreur pendant le test: {e}")
            return False
    
    def save_results(self):
        """Sauvegarde les résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON détaillé
        json_file = f"arras_requests_test_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        # CSV simple
        csv_file = f"arras_requests_test_{timestamp}.csv"
        if self.lawyers_data:
            import csv
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'specialisations', 'annee_inscription', 'url']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    row = {k: v for k, v in lawyer.items() if k in fieldnames}
                    row['specialisations'] = "; ".join(lawyer['specialisations']) if lawyer['specialisations'] else ""
                    writer.writerow(row)
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   📄 {json_file}")
        print(f"   📊 {csv_file}")
        print(f"   📈 {len(self.lawyers_data)} avocats traités")
        
        # Affichage résumé
        for i, lawyer in enumerate(self.lawyers_data, 1):
            print(f"\n📋 Avocat {i}:")
            print(f"   Nom: {lawyer['nom_complet']}")
            print(f"   Email: {lawyer['email'] or 'Non trouvé'}")
            print(f"   Téléphone: {lawyer['telephone'] or 'Non trouvé'}")
            print(f"   Spécialisations: {len(lawyer['specialisations'])} trouvée(s)")

def main():
    scraper = ArrasRequestsScraper()
    success = scraper.run_test()
    
    if success:
        print("\n🎉 Test terminé avec succès!")
    else:
        print("\n❌ Le test a échoué")

if __name__ == "__main__":
    main()