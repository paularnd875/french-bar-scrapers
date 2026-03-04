#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper simple et efficace pour le barreau de Montluçon
Version finale optimisée qui récupère tous les avocats réels
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin
import json
from datetime import datetime

class MontluconSimpleScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = "https://barreaudemontlucon.com"
        self.lawyers = []
    
    def get_page(self, url, retries=3):
        """Récupère une page avec gestion d'erreurs"""
        for attempt in range(retries):
            try:
                print(f"Récupération: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"Erreur tentative {attempt + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    return None
    
    def separate_first_last_name(self, full_name):
        """Sépare prénom et nom - Format: NOM Prénom ou NOM COMPOSÉ Prénom"""
        if not full_name:
            return "", ""
        
        # Nettoyer
        name_clean = re.sub(r'\\s+', ' ', full_name.strip())
        parts = name_clean.split()
        
        if len(parts) < 2:
            return "", parts[0] if parts else ""
        
        # Cas simple avec 2 parties
        if len(parts) == 2:
            return parts[1], parts[0]
        
        # Plus de 2 parties - identifier les noms de famille composés
        # Règle: les mots consécutifs en MAJUSCULES au début sont le nom de famille
        last_name_parts = [parts[0]]  # Premier mot toujours dans le nom
        first_name_start = 1
        
        # Chercher d'autres mots en majuscules consécutifs
        for i in range(1, len(parts)):
            if parts[i].isupper():
                last_name_parts.append(parts[i])
                first_name_start = i + 1
            else:
                break
        
        # Le reste sont les prénoms
        first_name_parts = parts[first_name_start:]
        
        # Si pas de prénom trouvé, prendre le dernier mot comme prénom
        if not first_name_parts:
            first_name_parts = [last_name_parts.pop()]
        
        first_name = " ".join(first_name_parts)
        last_name = " ".join(last_name_parts)
        
        return first_name, last_name
    
    def extract_detailed_info(self, detail_url):
        """Extrait les informations détaillées d'un avocat"""
        if not detail_url:
            return {}
        
        response = self.get_page(detail_url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        details = {}
        
        # Récupérer le contenu principal
        content_selectors = ['.wpbdp-listing-content', '.content', '.entry-content', 'main', '.wpbdp-listing']
        content_text = ""
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_text = content_elem.get_text()
                break
        
        if not content_text:
            content_text = soup.get_text()
        
        # Rechercher l'année d'inscription (patterns courants)
        year_patterns = [
            r'inscrit[e]?\\s+(?:au\\s+barreau\\s+)?(?:en\\s+|depuis\\s+)?(\\d{4})',
            r'barreau\\s+(?:en\\s+|depuis\\s+|de\\s+)?(\\d{4})',
            r'admission\\s+(?:en\\s+|depuis\\s+)?(\\d{4})',
            r'serment\\s+(?:en\\s+|depuis\\s+)?(\\d{4})'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, content_text, re.IGNORECASE)
            if matches:
                for match in matches:
                    year = match if isinstance(match, str) else match[0] if match else ""
                    if year and 1970 <= int(year) <= datetime.now().year:
                        details['annee_inscription'] = year
                        break
                if details.get('annee_inscription'):
                    break
        
        # Rechercher les spécialisations
        specialization_patterns = [
            r'sp[eé]cialis[eé]s?\\s+en\\s+([^\\n.;]+)',
            r'domaines?\\s+de\\s+comp[eé]tences?\\s*:([^\\n.;]+)',
            r'comp[eé]tences?\\s*:([^\\n.;]+)',
            r'pratique\\s+en\\s+([^\\n.;]+)',
            r'droit\\s+([a-záàâäéèêëíìîïóòôöúùûü\\s]+)'
        ]
        
        for pattern in specialization_patterns:
            match = re.search(pattern, content_text, re.IGNORECASE)
            if match:
                specialities = match.group(1).strip()
                if 5 <= len(specialities) <= 200:
                    details['specialites'] = specialities
                    break
        
        # Rechercher la structure/cabinet
        structure_patterns = [
            r'cabinet\\s+([^\\n.;]+)',
            r'structure\\s*:([^\\n.;]+)',
            r'société\\s+([^\\n.;]+)',
            r'sCP\\s+([^\\n.;]+)',
            r'sELARL\\s+([^\\n.;]+)'
        ]
        
        for pattern in structure_patterns:
            match = re.search(pattern, content_text, re.IGNORECASE)
            if match:
                structure = match.group(1).strip()
                if 3 <= len(structure) <= 100:
                    details['structure'] = structure
                    break
        
        return details
    
    def run_complete(self):
        """Lance le scraping de tous les avocats du barreau"""
        print("=== SCRAPING COMPLET BARREAU DE MONTLUCON ===")
        start_time = datetime.now()
        
        # URL principale
        main_url = "https://barreaudemontlucon.com/index.php/annuaire-professionnel/wpbdp_category/avocat/"
        response = self.get_page(main_url)
        
        if not response:
            print("Impossible d'accéder à la page principale")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraire tous les avocats de la page principale
        lawyer_elements = soup.select('.wpbdp-listing')
        print(f"Nombre d'avocats trouvés: {len(lawyer_elements)}")
        
        if not lawyer_elements:
            print("Aucun avocat trouvé sur la page")
            return []
        
        # Traiter chaque avocat
        for i, element in enumerate(lawyer_elements):
            try:
                print(f"\\n--- Avocat {i+1}/{len(lawyer_elements)} ---")
                
                # Extraire les informations de base
                name_link = element.select_one('h3 a')
                if not name_link:
                    print("Aucun nom trouvé, passage au suivant")
                    continue
                
                full_name = name_link.get_text(strip=True)
                detail_url = name_link.get('href')
                
                # Séparer prénom et nom
                first_name, last_name = self.separate_first_last_name(full_name)
                
                lawyer_info = {
                    'nom_complet': full_name,
                    'prenom': first_name,
                    'nom': last_name,
                    'lien_detail': urljoin(self.base_url, detail_url) if detail_url else None,
                    'source': 'page_principale'
                }
                
                print(f"Nom: {full_name} -> Prénom: '{first_name}', Nom: '{last_name}'")
                
                # Email
                email_elem = element.select_one('a[href^="mailto:"]')
                if email_elem:
                    lawyer_info['email'] = email_elem.get('href').replace('mailto:', '')
                    print(f"Email: {lawyer_info['email']}")
                
                # Téléphone
                phone_elem = element.select_one('a[href^="tel:"]')
                if phone_elem:
                    lawyer_info['telephone'] = phone_elem.get_text(strip=True)
                    print(f"Téléphone: {lawyer_info['telephone']}")
                
                # Adresse
                address_elem = element.select_one('[class*="address"], .wpbdp-field-address')
                if address_elem:
                    address_text = address_elem.get_text(strip=True)
                    if address_text and len(address_text) > 5:
                        address_text = re.sub(r'^Adresse', '', address_text).strip()
                        lawyer_info['adresse'] = address_text
                        print(f"Adresse: {address_text}")
                
                # Récupérer les informations détaillées
                if lawyer_info.get('lien_detail'):
                    print(f"Récupération des détails...")
                    details = self.extract_detailed_info(lawyer_info['lien_detail'])
                    lawyer_info.update(details)
                    
                    # Afficher ce qui a été trouvé
                    if details.get('specialites'):
                        print(f"Spécialisations: {details['specialites']}")
                    if details.get('annee_inscription'):
                        print(f"Année inscription: {details['annee_inscription']}")
                    if details.get('structure'):
                        print(f"Structure: {details['structure']}")
                    
                    # Pause entre les requêtes
                    time.sleep(0.5)
                
                self.lawyers.append(lawyer_info)
                
            except Exception as e:
                print(f"Erreur lors du traitement de l'avocat {i+1}: {e}")
        
        # Fin du traitement
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\\n=== SCRAPING TERMINE ===")
        print(f"Durée totale: {duration}")
        print(f"Nombre d'avocats traités: {len(self.lawyers)}")
        
        # Sauvegarder les résultats
        self.save_results()
        
        return self.lawyers
    
    def save_results(self):
        """Sauvegarde tous les résultats"""
        if not self.lawyers:
            print("Aucun résultat à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Préparer les données pour le CSV
        df_data = []
        for lawyer in self.lawyers:
            row = {
                'prenom': lawyer.get('prenom', ''),
                'nom': lawyer.get('nom', ''),
                'nom_complet': lawyer.get('nom_complet', ''),
                'email': lawyer.get('email', ''),
                'telephone': lawyer.get('telephone', ''),
                'adresse': lawyer.get('adresse', ''),
                'annee_inscription': lawyer.get('annee_inscription', ''),
                'specialites': lawyer.get('specialites', ''),
                'structure': lawyer.get('structure', ''),
                'source': lawyer.get('lien_detail', '')
            }
            df_data.append(row)
        
        # Sauvegarder en CSV
        df = pd.DataFrame(df_data)
        csv_filename = f"MONTLUCON_FINAL_{len(self.lawyers)}_avocats_{timestamp}.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\\n📄 Fichier CSV sauvegardé: {csv_filename}")
        
        # Sauvegarder en JSON
        json_filename = f"MONTLUCON_FINAL_{len(self.lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, indent=2, ensure_ascii=False)
        print(f"📄 Fichier JSON sauvegardé: {json_filename}")
        
        # Sauvegarder les emails uniquement
        emails = [l.get('email') for l in self.lawyers if l.get('email')]
        emails_filename = f"MONTLUCON_FINAL_EMAILS_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write('\\n'.join(emails))
        print(f"📧 Emails sauvegardés: {emails_filename}")
        
        # Rapport détaillé
        report_filename = f"MONTLUCON_FINAL_RAPPORT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT FINAL - BARREAU DE MONTLUCON ===\\n")
            f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\\n")
            f.write(f"URL source: https://barreaudemontlucon.com/index.php/annuaire-professionnel/wpbdp_category/avocat/\\n\\n")
            
            f.write("=== STATISTIQUES ===\\n")
            f.write(f"Nombre total d'avocats: {len(self.lawyers)}\\n")
            f.write(f"Avocats avec email: {len(emails)} ({len(emails)/len(self.lawyers)*100:.1f}%)\\n")
            f.write(f"Avocats avec téléphone: {sum(1 for l in self.lawyers if l.get('telephone'))} ({sum(1 for l in self.lawyers if l.get('telephone'))/len(self.lawyers)*100:.1f}%)\\n")
            f.write(f"Avocats avec adresse: {sum(1 for l in self.lawyers if l.get('adresse'))} ({sum(1 for l in self.lawyers if l.get('adresse'))/len(self.lawyers)*100:.1f}%)\\n")
            f.write(f"Avocats avec spécialisations: {sum(1 for l in self.lawyers if l.get('specialites'))} ({sum(1 for l in self.lawyers if l.get('specialites'))/len(self.lawyers)*100:.1f}%)\\n")
            f.write(f"Avocats avec année d'inscription: {sum(1 for l in self.lawyers if l.get('annee_inscription'))} ({sum(1 for l in self.lawyers if l.get('annee_inscription'))/len(self.lawyers)*100:.1f}%)\\n")
            f.write(f"Avocats avec structure: {sum(1 for l in self.lawyers if l.get('structure'))} ({sum(1 for l in self.lawyers if l.get('structure'))/len(self.lawyers)*100:.1f}%)\\n\\n")
            
            # Liste complète des emails
            f.write("=== LISTE COMPLETE DES EMAILS ===\\n")
            for i, email in enumerate(emails, 1):
                f.write(f"{i:2d}. {email}\\n")
            
            f.write("\\n=== EXEMPLES D'AVOCATS AVEC DETAILS ===\\n")
            detailed_lawyers = [l for l in self.lawyers if l.get('specialites') or l.get('annee_inscription') or l.get('structure')]
            for i, lawyer in enumerate(detailed_lawyers[:5]):
                f.write(f"\\nAvocat {i+1}:\\n")
                for key, value in lawyer.items():
                    if value and key != 'source':
                        f.write(f"  {key}: {value}\\n")
        
        print(f"📊 Rapport détaillé: {report_filename}")
        
        # Résumé final
        print(f"\\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print(f"📈 {len(self.lawyers)} avocats extraits au total")
        print(f"📧 {len(emails)} emails récupérés")
        print(f"📞 {sum(1 for l in self.lawyers if l.get('telephone'))} numéros de téléphone")
        print(f"🏠 {sum(1 for l in self.lawyers if l.get('adresse'))} adresses")
        print(f"⭐ {sum(1 for l in self.lawyers if l.get('specialites'))} avocats avec spécialisations")
        
        return {
            'csv': csv_filename,
            'json': json_filename, 
            'emails': emails_filename,
            'rapport': report_filename
        }


if __name__ == "__main__":
    scraper = MontluconSimpleScraper()
    scraper.run_complete()