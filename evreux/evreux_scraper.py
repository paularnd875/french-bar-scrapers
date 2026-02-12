#!/usr/bin/env python3
"""
SCRAPER OFFICIEL POUR LE BARREAU D'ÉVREUX
Extraction complète des 137 avocats du barreau de l'Eure
Site officiel : https://www.barreau-evreux.avocat.fr/annuaire-des-avocats/liste-et-recherche

Auteur : Script généré automatiquement
Repo : https://github.com/paularnd875/french-bar-scrapers
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from urllib.parse import urljoin
from datetime import datetime

class EvreuxBarScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-evreux.avocat.fr"
        self.list_url = f"{self.base_url}/annuaire-des-avocats/liste-et-recherche"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        self.all_lawyers = []
        self.total_pages = 6  # Évreux a exactement 6 pages d'avocats
        self.extraction_stats = {
            'total_processed': 0,
            'emails_found': 0,
            'phones_found': 0,
            'years_found': 0,
            'addresses_found': 0,
            'specializations_found': 0,
            'errors': 0
        }
    
    def collect_all_lawyer_urls(self):
        """Collecter tous les URLs des avocats de toutes les pages"""
        print("📥 COLLECTE DES URLs DE TOUS LES AVOCATS")
        print("=" * 50)
        
        all_urls = []
        
        for page_num in range(1, self.total_pages + 1):
            url = f"{self.list_url}?page={page_num}"
            print(f"📄 Page {page_num}: {url}")
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Trouver tous les liens d'avocats
                    lawyer_links = []
                    all_links = soup.find_all('a', href=True)
                    
                    for link in all_links:
                        href = link['href']
                        if 'page/annuaire/maitre-' in href and href.endswith('.htm'):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in [l['url'] for l in lawyer_links]:
                                # Extraire le nom depuis l'URL
                                name = self.extract_name_from_url(href)
                                lawyer_links.append({
                                    'url': full_url,
                                    'href': href,
                                    'name_from_url': name,
                                    'page_source': page_num
                                })
                    
                    all_urls.extend(lawyer_links)
                    print(f"   ✅ {len(lawyer_links)} avocats trouvés")
                    
                else:
                    print(f"   ❌ Erreur HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
            
            # Pause entre les pages
            if page_num < self.total_pages:
                time.sleep(1)
        
        print(f"\n📊 Total URLs collectés: {len(all_urls)}")
        return all_urls
    
    def extract_name_from_url(self, href):
        """Extraire le nom de l'avocat depuis l'URL"""
        try:
            parts = href.split('/')[-1].replace('.htm', '')
            if parts.startswith('maitre-'):
                name_part = parts[7:]  # Retirer 'maitre-'
                parts_list = name_part.split('-')
                if parts_list[-1].isdigit():
                    parts_list = parts_list[:-1]
                
                name = ' '.join(word.upper() for word in parts_list)
                return f"Maître {name}"
        except:
            pass
        return "Nom inconnu"
    
    def extract_profile_info(self, lawyer_data):
        """Extraire toutes les informations d'un profil d'avocat"""
        url = lawyer_data['url']
        
        try:
            print(f"   🔍 Extraction: {lawyer_data.get('name_from_url', 'Nom inconnu')}")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"      ❌ HTTP {response.status_code}")
                self.extraction_stats['errors'] += 1
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Données de base
            profile = {
                'url': url,
                'nom_complet': lawyer_data.get('name_from_url'),
                'prenom': None,
                'nom': None,
                'email': None,
                'telephone': None,
                'adresse_complete': None,
                'adresse_rue': None,
                'code_postal': None,
                'ville': None,
                'annee_inscription': None,
                'annee_serment': None,
                'specialisations': [],
                'domaines_competences': [],
                'structure': None,
                'cabinet': None,
                'page_source': lawyer_data.get('page_source'),
                'extraction_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Récupérer tout le texte de la page
            page_text = soup.get_text()
            
            # 1. EXTRACTION DU NOM COMPLET depuis le titre
            try:
                title = soup.title.text if soup.title else ""
                if 'Maître' in title:
                    name_match = re.search(r'Maître ([^|]+)', title)
                    if name_match:
                        full_name = name_match.group(1).strip()
                        profile['nom_complet'] = f"Maître {full_name}"
                        
                        # Séparer prénom et nom si possible
                        name_parts = full_name.split()
                        if len(name_parts) >= 2:
                            profile['prenom'] = name_parts[0]
                            profile['nom'] = ' '.join(name_parts[1:])
            except:
                pass
            
            # 2. EXTRACTION EMAIL
            try:
                # Chercher les liens mailto
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').strip()
                        if '@' in email and '.' in email and 'noreply' not in email:
                            # Filtrer l'email du prestataire technique
                            if 'azko.fr' not in email:
                                profile['email'] = email
                                self.extraction_stats['emails_found'] += 1
                                break
                
                # Si pas trouvé, chercher dans le texte avec regex
                if not profile['email']:
                    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                    emails = re.findall(email_pattern, page_text)
                    for email in emails:
                        if ('noreply' not in email and 'example' not in email and 
                            'azko.fr' not in email):  # Exclure l'email système
                            profile['email'] = email
                            self.extraction_stats['emails_found'] += 1
                            break
            except:
                pass
            
            # 3. EXTRACTION TÉLÉPHONE
            try:
                phone_patterns = [
                    r'(0[1-9](?:\s?\d{2}){4})',
                    r'(\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                    r'(\+33\s?\d\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})'
                ]
                
                for pattern in phone_patterns:
                    phones = re.findall(pattern, page_text)
                    if phones:
                        profile['telephone'] = phones[0].strip()
                        self.extraction_stats['phones_found'] += 1
                        break
            except:
                pass
            
            # 4. EXTRACTION ADRESSE
            try:
                # Pattern pour adresses françaises
                address_patterns = [
                    r'(\d+[^\n]*\n[^\n]*\d{5}\s+[A-ZÀ-Ÿ][^\n]+)',
                    r'(\d+[^,]*,\s*\d{5}\s+[A-ZÀ-Ÿ][^,\n]+)',
                    r'([A-ZÀ-Ÿ][^\n]*\n[^\n]*\d{5}\s+[A-ZÀ-Ÿ][^\n]+)'
                ]
                
                for pattern in address_patterns:
                    addresses = re.findall(pattern, page_text, re.MULTILINE)
                    if addresses:
                        profile['adresse_complete'] = addresses[0].strip()
                        self.extraction_stats['addresses_found'] += 1
                        
                        # Extraire code postal et ville
                        cp_ville_match = re.search(r'(\d{5})\s+([A-ZÀ-Ÿ][^\n,]+)', profile['adresse_complete'])
                        if cp_ville_match:
                            profile['code_postal'] = cp_ville_match.group(1)
                            profile['ville'] = cp_ville_match.group(2).strip()
                        break
            except:
                pass
            
            # 5. EXTRACTION ANNÉE D'INSCRIPTION
            try:
                year_patterns = [
                    r'(?:inscrit|inscription).*?(\d{4})',
                    r'barreau.*?(\d{4})',
                    r'serment.*?(\d{4})',
                    r'prestation.*?(\d{4})'
                ]
                
                for pattern in year_patterns:
                    years = re.findall(pattern, page_text, re.IGNORECASE)
                    for year in years:
                        if 1950 <= int(year) <= 2024:
                            if 'serment' in pattern:
                                profile['annee_serment'] = year
                            else:
                                profile['annee_inscription'] = year
                            self.extraction_stats['years_found'] += 1
                            break
                    if profile['annee_inscription'] or profile['annee_serment']:
                        break
            except:
                pass
            
            # 6. EXTRACTION SPÉCIALISATIONS
            try:
                specialization_keywords = [
                    'spécialisation', 'spécialisé', 'domaine de compétence',
                    'droit pénal', 'droit civil', 'droit commercial', 'droit des affaires',
                    'droit du travail', 'droit de la famille', 'droit immobilier',
                    'droit public', 'droit administratif', 'droit fiscal'
                ]
                
                found_specs = []
                page_text_lower = page_text.lower()
                
                for keyword in specialization_keywords:
                    if keyword in page_text_lower:
                        found_specs.append(keyword.title())
                
                profile['specialisations'] = list(set(found_specs))[:5]
                if profile['specialisations']:
                    self.extraction_stats['specializations_found'] += 1
            except:
                pass
            
            # 7. EXTRACTION STRUCTURE/CABINET
            try:
                structure_patterns = [
                    r'(Cabinet[^.\n]+)',
                    r'(SCP[^.\n]+)',
                    r'(SELARL[^.\n]+)',
                    r'(Société[^.\n]+)',
                    r'(Association[^.\n]+)'
                ]
                
                for pattern in structure_patterns:
                    structures = re.findall(pattern, page_text, re.IGNORECASE)
                    if structures:
                        profile['structure'] = structures[0].strip()
                        break
            except:
                pass
            
            self.extraction_stats['total_processed'] += 1
            
            # Afficher les informations trouvées
            if profile['email']:
                print(f"      ✅ Email: {profile['email']}")
            if profile['telephone']:
                print(f"      📞 Tél: {profile['telephone']}")
            if profile['annee_inscription']:
                print(f"      📅 Année: {profile['annee_inscription']}")
            
            return profile
            
        except Exception as e:
            print(f"      ❌ Erreur extraction: {e}")
            self.extraction_stats['errors'] += 1
            return None
    
    def scrape_all_lawyers(self):
        """Scraper tous les avocats"""
        print("🚀 DÉBUT DU SCRAPING COMPLET")
        print("=" * 50)
        
        # 1. Collecter tous les URLs
        lawyer_urls = self.collect_all_lawyer_urls()
        
        if not lawyer_urls:
            print("❌ Aucun URL collecté!")
            return False
        
        print(f"\n📋 EXTRACTION DES PROFILS ({len(lawyer_urls)} avocats)")
        print("-" * 50)
        
        # 2. Extraire chaque profil
        for i, lawyer_data in enumerate(lawyer_urls, 1):
            print(f"\n[{i}/{len(lawyer_urls)}] Processing...")
            
            profile = self.extract_profile_info(lawyer_data)
            
            if profile:
                self.all_lawyers.append(profile)
            
            # Pause entre les requêtes pour ne pas surcharger le serveur
            if i < len(lawyer_urls):
                time.sleep(1.5)  # Pause de 1.5 secondes
            
            # Sauvegarde intermédiaire tous les 25 profils
            if i % 25 == 0:
                self.save_intermediate_results(i)
        
        return True
    
    def save_intermediate_results(self, count):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"evreux_intermediate_{count}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'partial_count': count,
                'total_extracted': len(self.all_lawyers),
                'lawyers': self.all_lawyers,
                'stats': self.extraction_stats
            }, f, ensure_ascii=False, indent=2)
        
        print(f"      💾 Sauvegarde intermédiaire: {count} profils traités")
    
    def save_final_results(self):
        """Sauvegarder les résultats finaux"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. JSON complet
        json_filename = f"EVREUX_FINAL_COMPLET_{len(self.all_lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': timestamp,
                'total_lawyers': len(self.all_lawyers),
                'extraction_stats': self.extraction_stats,
                'source_url': f"{self.base_url}/annuaire-des-avocats/liste-et-recherche",
                'scraper_version': "1.0",
                'lawyers': self.all_lawyers
            }, f, ensure_ascii=False, indent=2)
        
        # 2. CSV pour Excel
        csv_filename = f"EVREUX_FINAL_COMPLET_{len(self.all_lawyers)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.all_lawyers:
                writer = csv.DictWriter(f, fieldnames=self.all_lawyers[0].keys())
                writer.writeheader()
                writer.writerows(self.all_lawyers)
        
        # 3. Fichier emails uniquement
        emails_filename = f"EVREUX_EMAILS_SEULEMENT_{len(self.all_lawyers)}_avocats_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            f.write(f"EMAILS EXTRAITS DU BARREAU D'ÉVREUX - {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            
            emails_found = 0
            for lawyer in self.all_lawyers:
                if lawyer.get('email'):
                    f.write(f"{lawyer.get('nom_complet', 'Nom inconnu')}: {lawyer['email']}\n")
                    emails_found += 1
            
            f.write(f"\nTotal emails trouvés: {emails_found}\n")
        
        # 4. Rapport d'extraction
        report_filename = f"EVREUX_RAPPORT_FINAL_{len(self.all_lawyers)}_avocats_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION - BARREAU D'ÉVREUX\n")
            f.write(f"Date: {timestamp}\n")
            f.write(f"Site officiel: {self.base_url}/annuaire-des-avocats/liste-et-recherche\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"STATISTIQUES:\n")
            f.write(f"- Total avocats traités: {self.extraction_stats['total_processed']}\n")
            f.write(f"- Emails trouvés: {self.extraction_stats['emails_found']} ({self.extraction_stats['emails_found']/self.extraction_stats['total_processed']*100:.1f}%)\n")
            f.write(f"- Téléphones trouvés: {self.extraction_stats['phones_found']} ({self.extraction_stats['phones_found']/self.extraction_stats['total_processed']*100:.1f}%)\n")
            f.write(f"- Années d'inscription: {self.extraction_stats['years_found']} ({self.extraction_stats['years_found']/self.extraction_stats['total_processed']*100:.1f}%)\n")
            f.write(f"- Adresses trouvées: {self.extraction_stats['addresses_found']} ({self.extraction_stats['addresses_found']/self.extraction_stats['total_processed']*100:.1f}%)\n")
            f.write(f"- Spécialisations: {self.extraction_stats['specializations_found']} ({self.extraction_stats['specializations_found']/self.extraction_stats['total_processed']*100:.1f}%)\n")
            f.write(f"- Erreurs: {self.extraction_stats['errors']}\n\n")
            
            f.write("FICHIERS GÉNÉRÉS:\n")
            f.write(f"- Données complètes JSON: {json_filename}\n")
            f.write(f"- Données complètes CSV: {csv_filename}\n")
            f.write(f"- Emails seulement: {emails_filename}\n")
            f.write(f"- Ce rapport: {report_filename}\n")
        
        return json_filename, csv_filename, emails_filename, report_filename
    
    def print_final_stats(self):
        """Afficher les statistiques finales"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL D'EXTRACTION")
        print("=" * 60)
        
        total = self.extraction_stats['total_processed']
        if total > 0:
            print(f"✅ Avocats traités avec succès: {total}")
            print(f"📧 Emails trouvés: {self.extraction_stats['emails_found']} ({self.extraction_stats['emails_found']/total*100:.1f}%)")
            print(f"📞 Téléphones trouvés: {self.extraction_stats['phones_found']} ({self.extraction_stats['phones_found']/total*100:.1f}%)")
            print(f"📅 Années d'inscription: {self.extraction_stats['years_found']} ({self.extraction_stats['years_found']/total*100:.1f}%)")
            print(f"🏠 Adresses trouvées: {self.extraction_stats['addresses_found']} ({self.extraction_stats['addresses_found']/total*100:.1f}%)")
            print(f"⚖️ Spécialisations trouvées: {self.extraction_stats['specializations_found']} ({self.extraction_stats['specializations_found']/total*100:.1f}%)")
            
            if self.extraction_stats['errors'] > 0:
                print(f"❌ Erreurs: {self.extraction_stats['errors']}")
        else:
            print("❌ Aucun avocat traité!")

def main():
    """Fonction principale"""
    print("🔍 SCRAPER COMPLET - BARREAU D'ÉVREUX")
    print("Site officiel: https://www.barreau-evreux.avocat.fr")
    print("Mode HEADLESS - Pas d'ouverture de fenêtres")
    print("Target: 137 avocats sur 6 pages")
    print("\nDémarrage dans 3 secondes...")
    time.sleep(3)
    
    scraper = EvreuxBarScraper()
    
    try:
        # Lancer le scraping complet
        success = scraper.scrape_all_lawyers()
        
        if success:
            # Sauvegarder les résultats
            files = scraper.save_final_results()
            
            # Afficher les stats
            scraper.print_final_stats()
            
            print(f"\n💾 FICHIERS GÉNÉRÉS:")
            for file in files:
                print(f"   - {file}")
            
            print("\n✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
            
        else:
            print("\n❌ ÉCHEC DE L'EXTRACTION!")
            
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt manuel du scraping")
        if scraper.all_lawyers:
            print(f"💾 Sauvegarde des {len(scraper.all_lawyers)} profils déjà extraits...")
            scraper.save_final_results()
        
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        if scraper.all_lawyers:
            print(f"💾 Sauvegarde d'urgence des {len(scraper.all_lawyers)} profils...")
            scraper.save_final_results()

if __name__ == "__main__":
    main()