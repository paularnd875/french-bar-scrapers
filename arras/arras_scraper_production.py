#!/usr/bin/env python3
"""
SCRAPER PRODUCTION - Barreau d'Arras - Extraction complète automatique
Version sans interaction utilisateur pour lancement direct
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
import csv

class ArrasProductionScraper:
    def __init__(self, delay_between_requests=3):
        self.base_url = "https://avocatsarras.com"
        self.annuaire_url = "https://avocatsarras.com/annuaire/"
        self.session = requests.Session()
        self.lawyers_data = []
        self.delay = delay_between_requests
        self.total_pages = 0
        self.processed_count = 0
        
        # Headers optimisés
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
    
    def log(self, message, level="INFO"):
        """Logging avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def get_page_content(self, url, max_retries=3):
        """Récupération robuste avec retry"""
        for attempt in range(max_retries):
            try:
                self.log(f"GET {url} (tentative {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                self.log(f"OK ({response.status_code})")
                return response.text
            except Exception as e:
                self.log(f"Erreur tentative {attempt + 1}: {e}", "ERROR")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                else:
                    self.log(f"Échec définitif pour {url}", "ERROR")
                    return None
    
    def discover_total_pages(self):
        """Découvre le nombre total de pages"""
        self.log("🔍 Découverte du nombre de pages...")
        
        content = self.get_page_content(self.annuaire_url)
        if not content:
            return 1
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Rechercher la pagination
        pagination_links = soup.find_all('a', href=re.compile(r'/page/\d+/'))
        page_numbers = []
        
        for link in pagination_links:
            href = link.get('href', '')
            match = re.search(r'/page/(\d+)/', href)
            if match:
                page_numbers.append(int(match.group(1)))
        
        if page_numbers:
            self.total_pages = max(page_numbers)
        else:
            self.total_pages = 1
        
        self.log(f"📊 Nombre de pages détecté: {self.total_pages}")
        return self.total_pages
    
    def get_lawyers_from_page(self, page_num):
        """Extrait tous les avocats d'une page donnée"""
        if page_num == 1:
            url = self.annuaire_url
        else:
            url = f"{self.annuaire_url}page/{page_num}/"
        
        self.log(f"📄 Traitement page {page_num}/{self.total_pages}")
        
        content = self.get_page_content(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Récupérer tous les liens d'avocats
        lawyer_links = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if '/specialite-avocat/' in href and 'avocatsarras.com' in href:
                text = link.get_text(strip=True)
                if len(text.split()) >= 2:
                    lawyer_links.append({
                        'url': href,
                        'name': text,
                        'page': page_num
                    })
        
        self.log(f"👥 {len(lawyer_links)} avocats trouvés sur la page {page_num}")
        return lawyer_links
    
    def extract_complete_lawyer_info(self, lawyer_info):
        """Extraction complète optimisée"""
        url = lawyer_info['url']
        expected_name = lawyer_info['name']
        page = lawyer_info['page']
        
        self.processed_count += 1
        self.log(f"🔍 [{self.processed_count}] Extraction: {expected_name}")
        
        content = self.get_page_content(url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Structure complète des données
        lawyer_data = {
            "ordre_extraction": self.processed_count,
            "page_source": page,
            "url": url,
            "nom_complet": expected_name,
            "prenom": "",
            "nom": "",
            "email": "",
            "telephone": "",
            "fax": "",
            "adresse_complete": "",
            "ville": "",
            "code_postal": "",
            "specialisations": [],
            "annee_inscription": "",
            "structure_cabinet": "",
            "site_web": "",
            "status_extraction": "success"
        }
        
        try:
            # EMAIL
            emails = set()
            
            # Liens mailto
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                email = link.get('href', '').lower().replace('mailto:', '').strip()
                if '@' in email and '.' in email:
                    emails.add(email)
            
            # Regex dans le texte
            text_content = soup.get_text()
            email_matches = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text_content)
            for email in email_matches:
                if any(domain in email.lower() for domain in ['.com', '.fr', '.org', '.net']):
                    emails.add(email.lower())
            
            if emails:
                lawyer_data["email"] = list(emails)[0]
            
            # TÉLÉPHONE
            phone_text = re.sub(r'[^0-9+\s\-\.]', ' ', text_content)
            phone_patterns = [
                r'(\+33|0)[1-9](?:[\s\-\.]?[0-9]){8}',
                r'0[1-9](?:[0-9]){8}'
            ]
            
            phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, phone_text)
                for match in matches:
                    clean_phone = re.sub(r'[^0-9+]', '', str(match))
                    if 9 <= len(clean_phone) <= 12:
                        phones.add(clean_phone)
            
            if phones:
                lawyer_data["telephone"] = list(phones)[0]
            
            # FAX
            fax_context = re.findall(r'fax[\s:]*([0-9\s\.\-\+]{9,})', text_content, re.IGNORECASE)
            if fax_context:
                clean_fax = re.sub(r'[^0-9+]', '', fax_context[0])
                if len(clean_fax) >= 9:
                    lawyer_data["fax"] = clean_fax
            
            # ADRESSE
            address_patterns = [
                r'(\d+[^\n]*(?:rue|avenue|place|boulevard|allée|impasse)[^\n]*)',
                r'([^\n]*(?:rue|avenue|place|boulevard|allée|impasse)[^\n]*\d+[^\n]*)',
                r'(\d+[^\n]*62\d{3}[^\n]*)',
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if 15 < len(match) < 150:
                        lawyer_data["adresse_complete"] = match.strip()
                        
                        # Code postal et ville
                        cp_match = re.search(r'(62\d{3})', match)
                        if cp_match:
                            lawyer_data["code_postal"] = cp_match.group(1)
                            ville_match = re.search(rf'{cp_match.group(1)}\s*([A-Za-zÀ-ÿ\s\-]+)', match)
                            if ville_match:
                                lawyer_data["ville"] = ville_match.group(1).strip()[:50]
                        break
            
            # SPÉCIALISATIONS
            specializations = set()
            droit_keywords = [
                'droit pénal', 'droit civil', 'droit commercial', 'droit des affaires',
                'droit de la famille', 'droit immobilier', 'droit du travail', 'droit social',
                'droit fiscal', 'droit des sociétés', 'droit public', 'droit administratif',
                'droit de la construction', 'droit médical', 'droit international'
            ]
            
            text_lower = text_content.lower()
            for keyword in droit_keywords:
                if keyword in text_lower:
                    specializations.add(keyword.title())
            
            lawyer_data["specialisations"] = list(specializations)[:8]
            
            # ANNÉE D'INSCRIPTION
            inscription_patterns = [
                r'inscrit[e]?.*?(?:au\s+)?barreau.*?([12][0-9]{3})',
                r'barreau.*?([12][0-9]{3})',
                r'([12][0-9]{3}).*?inscrit',
                r'serment.*?([12][0-9]{3})'
            ]
            
            for pattern in inscription_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    year = str(match)
                    if 1950 <= int(year) <= 2025:
                        lawyer_data["annee_inscription"] = year
                        break
                if lawyer_data["annee_inscription"]:
                    break
            
            # STRUCTURE/CABINET
            cabinet_patterns = [
                r'cabinet\s+([^\n\.]{5,80})',
                r'société\s+([^\n\.]{5,80})',
                r'scp\s+([^\n\.]{5,80})',
                r'selarl\s+([^\n\.]{5,80})'
            ]
            
            for pattern in cabinet_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    cabinet = matches[0].strip()[:100]
                    if len(cabinet) > 3:
                        lawyer_data["structure_cabinet"] = cabinet
                        break
            
            # SITE WEB
            web_links = soup.find_all('a', href=re.compile(r'^https?://'))
            for link in web_links:
                href = link.get('href', '')
                if 'avocatsarras.com' not in href and any(tld in href for tld in ['.com', '.fr', '.org']):
                    lawyer_data["site_web"] = href
                    break
            
            # PRÉNOM/NOM parsing
            if lawyer_data["nom_complet"]:
                clean_name = lawyer_data["nom_complet"]
                clean_name = re.sub(r'(maitre|me\.?|avocat)', '', clean_name, flags=re.IGNORECASE).strip()
                clean_name = re.sub(r'[^a-zA-ZÀ-ÿ\s\-]', '', clean_name)
                
                name_parts = clean_name.split()
                if len(name_parts) >= 2:
                    lawyer_data["nom"] = name_parts[-1].upper()
                    lawyer_data["prenom"] = " ".join(name_parts[:-1]).title()
                elif len(name_parts) == 1:
                    lawyer_data["nom"] = name_parts[0].upper()
            
        except Exception as e:
            self.log(f"Erreur lors de l'extraction de {expected_name}: {e}", "ERROR")
            lawyer_data["status_extraction"] = "partial_error"
        
        return lawyer_data
    
    def save_progress(self, filename_suffix=""):
        """Sauvegarde des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f"arras_production{filename_suffix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        # CSV
        csv_file = f"arras_production{filename_suffix}_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = [
                'ordre_extraction', 'nom_complet', 'prenom', 'nom', 'email', 'telephone', 'fax',
                'adresse_complete', 'ville', 'code_postal', 'specialisations', 'annee_inscription',
                'structure_cabinet', 'site_web', 'page_source', 'url', 'status_extraction'
            ]
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    row = {k: lawyer.get(k, '') for k in fieldnames}
                    row['specialisations'] = "; ".join(lawyer.get('specialisations', []))
                    writer.writerow(row)
        
        self.log(f"💾 Sauvegarde: {json_file} & {csv_file}")
        return json_file, csv_file
    
    def run_production_scraping(self):
        """Lance le scraping complet"""
        start_time = datetime.now()
        
        self.log("🚀 DÉMARRAGE SCRAPER PRODUCTION ARRAS - MODE AUTOMATIQUE")
        self.log("=" * 60)
        self.log(f"⚙️ Configuration: délai entre requêtes = {self.delay}s")
        
        try:
            # Découverte du nombre de pages
            total_pages = self.discover_total_pages()
            if total_pages == 0:
                self.log("❌ Impossible de déterminer le nombre de pages", "ERROR")
                return False
            
            # Collecte de tous les liens d'avocats
            self.log("📋 Collecte des liens d'avocats...")
            all_lawyers = []
            
            for page_num in range(1, total_pages + 1):
                lawyers_on_page = self.get_lawyers_from_page(page_num)
                all_lawyers.extend(lawyers_on_page)
                
                if page_num < total_pages:
                    time.sleep(self.delay)
            
            self.log(f"👥 TOTAL: {len(all_lawyers)} avocats à traiter")
            
            if not all_lawyers:
                self.log("❌ Aucun avocat trouvé", "ERROR")
                return False
            
            # Extraction des données pour chaque avocat
            self.log("🔍 Démarrage extraction individuelle...")
            successful_extractions = 0
            failed_extractions = 0
            
            for i, lawyer_info in enumerate(all_lawyers, 1):
                try:
                    progress = f"[{i}/{len(all_lawyers)}]"
                    self.log(f"📄 {progress} {lawyer_info['name']}")
                    
                    lawyer_data = self.extract_complete_lawyer_info(lawyer_info)
                    
                    if lawyer_data:
                        self.lawyers_data.append(lawyer_data)
                        successful_extractions += 1
                        
                        # Log des infos essentielles
                        info_summary = []
                        if lawyer_data.get('email'):
                            info_summary.append(f"📧 {lawyer_data['email']}")
                        if lawyer_data.get('telephone'):
                            info_summary.append(f"📞 {lawyer_data['telephone']}")
                        if lawyer_data.get('annee_inscription'):
                            info_summary.append(f"📅 {lawyer_data['annee_inscription']}")
                        
                        if info_summary:
                            self.log(f"✅ Données: {' | '.join(info_summary)}")
                        else:
                            self.log("✅ Extraction OK (données minimales)")
                    else:
                        failed_extractions += 1
                        self.log("❌ Échec extraction", "ERROR")
                    
                    # Sauvegarde intermédiaire tous les 10 avocats
                    if i % 10 == 0:
                        self.save_progress(f"_partial_{i}")
                        self.log(f"💾 Sauvegarde intermédiaire ({i} traités)")
                    
                    if i < len(all_lawyers):
                        time.sleep(self.delay)
                        
                except KeyboardInterrupt:
                    self.log("⏸️ INTERRUPTION UTILISATEUR", "WARNING")
                    break
                except Exception as e:
                    failed_extractions += 1
                    self.log(f"❌ Erreur inattendue pour {lawyer_info.get('name', 'N/A')}: {e}", "ERROR")
                    continue
            
            # Sauvegarde finale
            self.log("💾 Sauvegarde finale...")
            final_files = self.save_progress("_FINAL")
            
            # Rapport final
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.log("=" * 60)
            self.log("📊 RAPPORT FINAL")
            self.log("=" * 60)
            self.log(f"⏱️ Durée totale: {duration}")
            self.log(f"📄 Pages traitées: {total_pages}")
            self.log(f"👥 Avocats découverts: {len(all_lawyers)}")
            self.log(f"✅ Extractions réussies: {successful_extractions}")
            self.log(f"❌ Extractions échouées: {failed_extractions}")
            if len(all_lawyers) > 0:
                self.log(f"📈 Taux de réussite: {(successful_extractions/len(all_lawyers)*100):.1f}%")
            self.log(f"💾 Fichiers finaux: {final_files[0]} & {final_files[1]}")
            
            # Statistiques détaillées
            if successful_extractions > 0:
                emails_found = sum(1 for l in self.lawyers_data if l.get('email'))
                phones_found = sum(1 for l in self.lawyers_data if l.get('telephone'))
                years_found = sum(1 for l in self.lawyers_data if l.get('annee_inscription'))
                
                self.log(f"📧 Emails trouvés: {emails_found}/{successful_extractions} ({emails_found/successful_extractions*100:.1f}%)")
                self.log(f"📞 Téléphones trouvés: {phones_found}/{successful_extractions} ({phones_found/successful_extractions*100:.1f}%)")
                self.log(f"📅 Années inscription trouvées: {years_found}/{successful_extractions} ({years_found/successful_extractions*100:.1f}%)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERREUR CRITIQUE: {e}", "ERROR")
            return False

def main():
    """Fonction principale automatique"""
    print("\n🚀 LANCEMENT AUTOMATIQUE DU SCRAPER ARRAS")
    print("=" * 50)
    
    # Lancement automatique avec délai de 3 secondes
    scraper = ArrasProductionScraper(delay_between_requests=3)
    success = scraper.run_production_scraping()
    
    if success:
        print("\n🎉 SCRAPING TERMINÉ AVEC SUCCÈS!")
        print("Les fichiers CSV et JSON contiennent toutes les données extraites.")
    else:
        print("\n❌ Le scraping a échoué.")
        print("Vérifiez les logs pour plus d'informations.")

if __name__ == "__main__":
    main()