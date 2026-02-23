#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU DE BOURGES - VERSION FINALE COMPLÈTE
===================================================
Extraction PARFAITE de TOUTES les données avec correction d'encodage
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
import re
import time
from urllib.parse import urljoin
import html

class BourgesScraperComplete:
    def __init__(self):
        self.base_url = "https://www.barreau-bourges.com"
        self.search_url = "https://www.barreau-bourges.com/recherche/?ville=&nom="
        self.session = self.setup_session()
        self.lawyers = []
        self.errors = []
        self.total_found = 0
        self.processed = 0
        
    def setup_session(self):
        """Configure la session requests"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        return session
        
    def get_all_lawyer_urls(self):
        """Récupère toutes les URLs des profils d'avocats"""
        print("🔍 Récupération de la liste complète des avocats...")
        
        try:
            response = self.session.get(self.search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            avocat_divs = soup.find_all('div', class_='avocat')
            self.total_found = len(avocat_divs)
            
            print(f"✓ {self.total_found} avocats trouvés")
            
            profile_urls = []
            for div in avocat_divs:
                try:
                    h3_elem = div.find('h3')
                    if h3_elem:
                        link = h3_elem.find('a')
                        if link:
                            href = link.get('href', '')
                            if href:
                                full_url = urljoin(self.base_url, href)
                                profile_urls.append(full_url)
                except Exception as e:
                    self.errors.append(f"Erreur extraction URL: {e}")
                    
            print(f"✓ {len(profile_urls)} URLs récupérées")
            return profile_urls
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def fix_encoding(self, text):
        """Corrige tous les problèmes d'encodage"""
        if not text:
            return ""
        
        # Décoder les entités HTML
        text = html.unescape(text)
        
        # Corrections spécifiques pour l'encodage iso-8859-1 mal interprété
        replacements = {
            'Ã©': 'é', 'Ã¨': 'è', 'Ã ': 'à', 'Ã´': 'ô', 
            'Ã§': 'ç', 'Ã¯': 'ï', 'Ã«': 'ë', 'Ã¢': 'â', 
            'Ã®': 'î', 'Ã¹': 'ù', 'Ã»': 'û', 'Ã¶': 'ö',
            'Ã‰': 'É', 'Ã€': 'À', 'Ãˆ': 'È', 'Ã"': 'Ô',
            'Ã‡': 'Ç', 'Ã›': 'Û'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Nettoyer les espaces
        text = re.sub(r'\\s+', ' ', text).strip()
        
        return text
        
    def extract_lawyer_details(self, profile_url):
        """Extrait PARFAITEMENT les informations d'un avocat"""
        try:
            response = self.session.get(profile_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            lawyer_info = {
                'url': profile_url,
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'annee_inscription': '',
                'specialisations': [],
                'structures': [],
                'adresses': [],
                'domaines_intervention': [],
                'formation': '',
                'info_supplementaire': ''
            }
            
            # 1. NOM ET PRÉNOM
            titre_cabinet = soup.find('h3', class_='titre_cabinet')
            if titre_cabinet:
                nom_complet = self.fix_encoding(titre_cabinet.get_text())
                parts = nom_complet.split()
                if len(parts) >= 2:
                    lawyer_info['nom'] = parts[0]
                    lawyer_info['prenom'] = ' '.join(parts[1:])
                    
            # 2. EMAIL
            email_link = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
            if email_link:
                lawyer_info['email'] = email_link.get('href').replace('mailto:', '')
                
            # 3. TÉLÉPHONE - CORRECTION ULTIME
            coordonnees = soup.find('p', class_='coordonnees')
            if coordonnees:
                coord_text = coordonnees.get_text()
                # Patterns multiples pour extraire le téléphone
                tel_patterns = [
                    r'Tél[^:]*:\\s*([0-9]{2}[\\s\\.-]?[0-9]{2}[\\s\\.-]?[0-9]{2}[\\s\\.-]?[0-9]{2}[\\s\\.-]?[0-9]{2})',
                    r'([0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}\\.[0-9]{2})',
                    r'([0-9]{10})'
                ]
                
                for pattern in tel_patterns:
                    tel_match = re.search(pattern, coord_text)
                    if tel_match:
                        tel = tel_match.group(1)
                        # Nettoyer et formater le téléphone
                        tel = re.sub(r'[\\s-]', '.', tel)
                        if len(tel.replace('.', '')) == 10:
                            lawyer_info['telephone'] = tel
                            break
                            
            # 4. ANNÉE D'INSCRIPTION
            h4_elements = soup.find_all('h4')
            for h4 in h4_elements:
                h4_text = h4.get_text()
                if "Ann" in h4_text and "inscription" in h4_text:
                    span = h4.find('span', class_='normal')
                    if span:
                        year_text = span.get_text().strip()
                        if year_text.isdigit() and 1900 <= int(year_text) <= 2025:
                            lawyer_info['annee_inscription'] = year_text
                            break
                            
            # 5. SPÉCIALISATIONS COMPLÈTES
            # Méthode 1: h4 "Spécialisation(s)"
            for h4 in h4_elements:
                if "Sp" in h4.get_text() and "cialisation" in h4.get_text():
                    next_p = h4.find_next_sibling('p')
                    if next_p:
                        spec_text = self.fix_encoding(next_p.get_text())
                        if spec_text:
                            specs = [s.strip() for s in re.split(r'[\\n\\r]', spec_text) if s.strip() and len(s.strip()) > 2]
                            for spec in specs:
                                if spec not in lawyer_info['specialisations']:
                                    lawyer_info['specialisations'].append(spec)
                    break
                    
            # Méthode 2: Sections détaillées (h5 "Mentions de spécialisation")
            mentions_spec = soup.find('h5', string=lambda text: text and 'Mentions de spécialisation' in text)
            if mentions_spec:
                next_ul = mentions_spec.find_next_sibling('ul')
                if next_ul:
                    li_elements = next_ul.find_all('li')
                    for li in li_elements:
                        spec = self.fix_encoding(li.get_text())
                        if spec and spec not in lawyer_info['specialisations']:
                            lawyer_info['specialisations'].append(spec)
                            
            # 6. DOMAINES D'INTERVENTION
            domaines_h5 = soup.find('h5', string=lambda text: text and 'domaines' in text.lower() and 'intervention' in text.lower())
            if domaines_h5:
                domaines_ul = domaines_h5.find_next_sibling('ul')
                if domaines_ul:
                    li_elements = domaines_ul.find_all('li')
                    for li in li_elements:
                        domaine = self.fix_encoding(li.get_text())
                        if domaine:
                            lawyer_info['domaines_intervention'].append(domaine)
                            
            # 7. FORMATION
            formation_h5 = soup.find('h5', string=lambda text: text and 'Formation' in text)
            if formation_h5:
                next_div = formation_h5.find_next('div')
                if next_div:
                    formation_p = next_div.find('p')
                    if formation_p:
                        lawyer_info['formation'] = self.fix_encoding(formation_p.get_text())[:500]
                        
            # 8. INFO SUPPLÉMENTAIRE
            info_h5 = soup.find('h5', string=lambda text: text and 'A savoir' in text)
            if info_h5:
                info_parts = []
                next_p = info_h5.find_next_sibling('p')
                while next_p and len(info_parts) < 3:
                    p_text = self.fix_encoding(next_p.get_text())
                    if p_text:
                        info_parts.append(p_text)
                    next_p = next_p.find_next_sibling('p')
                if info_parts:
                    lawyer_info['info_supplementaire'] = '; '.join(info_parts)[:400]
                    
            # 9. CABINETS/STRUCTURES ET ADRESSES - CORRECTION ULTIME
            for h4 in h4_elements:
                if "Cabinet" in h4.get_text() and "appartenance" in h4.get_text():
                    next_p = h4.find_next_sibling('p')
                    if next_p:
                        # Structures
                        cabinet_links = next_p.find_all('a')
                        for link in cabinet_links:
                            cabinet_name = self.fix_encoding(link.get_text())
                            if cabinet_name and cabinet_name not in lawyer_info['structures']:
                                lawyer_info['structures'].append(cabinet_name)
                                
                        # ADRESSES - Extraction directe du HTML et du texte
                        p_html = str(next_p)
                        p_text = self.fix_encoding(next_p.get_text())
                        
                        # Patterns d'adresse plus larges
                        address_patterns = [
                            r'([0-9]+[^\\n]*?(?:rue|avenue|place|boulevard|cours)[^\\n]*?[0-9]{5}[^\\n]*?)',
                            r'([A-Za-z].*?(?:rue|avenue|place|boulevard|cours)[^\\n]*?[0-9]{5}[^\\n]*?)',
                            r'([0-9]{1,4}.*?-.*?[0-9]{5}.*?[A-Z]{2,})',
                            r'(.*?rue.*?[0-9]{5}.*?)'
                        ]
                        
                        # Essayer d'extraire depuis le HTML brut
                        for pattern in address_patterns:
                            addresses = re.findall(pattern, p_html, re.IGNORECASE | re.MULTILINE)
                            for addr in addresses:
                                clean_addr = self.fix_encoding(re.sub(r'<[^>]+>', '', addr)).strip()
                                if (len(clean_addr) > 15 and 
                                    len(clean_addr) < 200 and 
                                    clean_addr not in lawyer_info['adresses'] and
                                    any(word in clean_addr.lower() for word in ['rue', 'avenue', 'place', 'boulevard'])):
                                    lawyer_info['adresses'].append(clean_addr)
                                    
                        # Si pas d'adresse trouvée, essayer ligne par ligne
                        if not lawyer_info['adresses']:
                            lines = p_text.split('\\n')
                            for line in lines:
                                line = line.strip()
                                if (re.search(r'[0-9]{5}', line) and 
                                    any(word in line.lower() for word in ['rue', 'avenue', 'place', 'boulevard']) and
                                    len(line) > 10):
                                    lawyer_info['adresses'].append(line)
                    break
                    
            return lawyer_info
            
        except Exception as e:
            error_msg = f"Erreur {profile_url.split('/')[-2] if '/' in profile_url else profile_url}: {e}"
            self.errors.append(error_msg)
            return None
            
    def scrape_all_lawyers(self):
        """Lance l'extraction complète"""
        print("🚀 EXTRACTION FINALE COMPLÈTE")
        print("=" * 40)
        
        profile_urls = self.get_all_lawyer_urls()
        if not profile_urls:
            return False
            
        print(f"\\n🎯 Extraction de {len(profile_urls)} profils...")
        start_time = time.time()
        
        for i, url in enumerate(profile_urls):
            self.processed = i + 1
            progress = (self.processed / len(profile_urls)) * 100
            
            lawyer_info = self.extract_lawyer_details(url)
            
            if lawyer_info:
                self.lawyers.append(lawyer_info)
                
                name = f"{lawyer_info['prenom']} {lawyer_info['nom']}".strip()
                email_status = "✓" if lawyer_info['email'] else "✗"
                tel_status = "✓" if lawyer_info['telephone'] else "✗"
                year_status = "✓" if lawyer_info['annee_inscription'] else "✗"  
                spec_count = len(lawyer_info['specialisations'])
                addr_count = len(lawyer_info['adresses'])
                
                print(f"[{self.processed}/{len(profile_urls)}] {name} | E:{email_status} T:{tel_status} A:{year_status} | Sp:{spec_count} Ad:{addr_count}")
            else:
                print(f"[{self.processed}/{len(profile_urls)}] ❌ Échec")
                
            time.sleep(0.1)
                
        elapsed = time.time() - start_time
        
        print(f"\\n✅ EXTRACTION TERMINÉE en {elapsed:.1f}s")
        print(f"Réussis: {len(self.lawyers)}/{self.processed} | Erreurs: {len(self.errors)}")
        
        return True
        
    def save_final_results(self):
        """Sauvegarde finale avec statistiques"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON complet
        json_filename = f"BOURGES_FINAL_COMPLET_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
            
        # 2. CSV 
        csv_filename = f"BOURGES_FINAL_COMPLET_{timestamp}.csv"
        if self.lawyers:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                flattened = []
                for lawyer in self.lawyers:
                    flat = lawyer.copy()
                    flat['specialisations'] = '; '.join(lawyer['specialisations'])
                    flat['structures'] = '; '.join(lawyer['structures'])
                    flat['adresses'] = '; '.join(lawyer['adresses'])
                    flat['domaines_intervention'] = '; '.join(lawyer['domaines_intervention'])
                    flattened.append(flat)
                    
                if flattened:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened)
                    
        # 3. Emails
        emails_filename = f"BOURGES_EMAILS_FINAL_{timestamp}.txt"
        emails = [l['email'] for l in self.lawyers if l['email']]
        with open(emails_filename, 'w', encoding='utf-8') as f:
            for email in sorted(set(emails)):
                f.write(f"{email}\\n")
                
        # 4. Rapport final
        rapport_filename = f"BOURGES_RAPPORT_FINAL_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as f:
            f.write("RAPPORT FINAL COMPLET - BARREAU DE BOURGES\\n")
            f.write("=" * 50 + "\\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\\n\\n")
            
            emails_count = sum(1 for l in self.lawyers if l['email'])
            phones_count = sum(1 for l in self.lawyers if l['telephone'])
            years_count = sum(1 for l in self.lawyers if l['annee_inscription'])
            specs_count = sum(1 for l in self.lawyers if l['specialisations'])
            structs_count = sum(1 for l in self.lawyers if l['structures'])
            addrs_count = sum(1 for l in self.lawyers if l['adresses'])
            
            total = len(self.lawyers)
            
            f.write("RÉSULTATS FINAUX:\\n")
            f.write(f"  Total extraits: {total}/{self.total_found}\\n")
            f.write(f"  Emails: {emails_count}/{total} ({(emails_count/max(1,total))*100:.1f}%)\\n")
            f.write(f"  Téléphones: {phones_count}/{total} ({(phones_count/max(1,total))*100:.1f}%)\\n")
            f.write(f"  Années: {years_count}/{total} ({(years_count/max(1,total))*100:.1f}%)\\n")
            f.write(f"  Spécialisations: {specs_count}/{total} ({(specs_count/max(1,total))*100:.1f}%)\\n")
            f.write(f"  Structures: {structs_count}/{total} ({(structs_count/max(1,total))*100:.1f}%)\\n")
            f.write(f"  Adresses: {addrs_count}/{total} ({(addrs_count/max(1,total))*100:.1f}%)\\n\\n")
            
            # Top spécialisations corrigées
            all_specs = []
            for l in self.lawyers:
                all_specs.extend(l['specialisations'])
            
            if all_specs:
                from collections import Counter
                top_specs = Counter(all_specs).most_common(10)
                f.write("TOP SPÉCIALISATIONS:\\n")
                for spec, count in top_specs:
                    f.write(f"  {spec}: {count} avocats\\n")
                    
        print(f"\\n📊 FICHIERS FINAUX GÉNÉRÉS:")
        print(f"   📄 {json_filename}")
        print(f"   📊 {csv_filename}")
        print(f"   📧 {emails_filename} ({len(set(emails))} emails)")
        print(f"   📋 {rapport_filename}")
        
def main():
    print("🏛️  SCRAPER BARREAU DE BOURGES - VERSION FINALE COMPLÈTE")
    print("=" * 65)
    
    scraper = BourgesScraperComplete()
    
    try:
        success = scraper.scrape_all_lawyers()
        
        if success and scraper.lawyers:
            scraper.save_final_results()
            
            print(f"\\n🎉 EXTRACTION FINALE RÉUSSIE!")
            print(f"📊 {len(scraper.lawyers)} avocats extraits sur {scraper.total_found} trouvés")
            
            # Stats finales
            emails = sum(1 for l in scraper.lawyers if l['email'])
            phones = sum(1 for l in scraper.lawyers if l['telephone'])
            years = sum(1 for l in scraper.lawyers if l['annee_inscription'])
            specs = sum(1 for l in scraper.lawyers if l['specialisations'])
            addrs = sum(1 for l in scraper.lawyers if l['adresses'])
            
            total = len(scraper.lawyers)
            
            print(f"\\n📈 QUALITÉ:")
            print(f"   📧 Emails: {emails}/{total} ({(emails/total)*100:.0f}%)")
            print(f"   📞 Téléphones: {phones}/{total} ({(phones/total)*100:.0f}%)")  
            print(f"   📅 Années: {years}/{total} ({(years/total)*100:.0f}%)")
            print(f"   🎯 Spécialisations: {specs}/{total} ({(specs/total)*100:.0f}%)")
            print(f"   🏢 Adresses: {addrs}/{total} ({(addrs/total)*100:.0f}%)")
            
            # Échantillon final
            print("\\n📋 ÉCHANTILLON:")
            for i, lawyer in enumerate(scraper.lawyers[:2]):
                name = f"{lawyer['prenom']} {lawyer['nom']}".strip()
                print(f"\\n  {i+1}. {name}")
                print(f"     📧 {lawyer['email']}")
                print(f"     📞 {lawyer['telephone'] or 'Non trouvé'}")
                print(f"     📅 {lawyer['annee_inscription']}")
                print(f"     🎯 {', '.join(lawyer['specialisations']) or 'Non trouvé'}")
                print(f"     🏢 {', '.join(lawyer['adresses']) or 'Non trouvé'}")
                
        else:
            print("❌ ÉCHEC")
            
    except KeyboardInterrupt:
        print("\\n⚠️ Arrêt")
        if scraper.lawyers:
            scraper.save_final_results()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()