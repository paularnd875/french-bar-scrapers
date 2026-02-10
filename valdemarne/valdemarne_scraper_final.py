#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper PRODUCTION FINAL pour l'annuaire des avocats du Barreau du Val de Marne
Version corrigée avec pagination forcée - Sans cache Python
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from datetime import datetime
import re
from urllib.parse import urljoin
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class ValdeMarneProductionFinalScraper:
    def __init__(self):
        self.base_url = "https://avocats-valdemarne.com"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
        
    def get_lawyers_urls_from_page(self, page_num):
        """Récupère les URLs des avocats d'une page spécifique"""
        try:
            url = f"{self.base_url}/annuaire?recherche=1&page={page_num}&mode=&nom=&ville=&langue=&specialite="
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire les liens vers les fiches d'avocats
            lawyer_links = soup.find_all('a', href=re.compile(r'avocat_id=\d+'))
            urls = []
            
            for link in lawyer_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
                        
            print(f"✓ Page {page_num}: {len(urls)} avocats trouvés")
            return urls
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction de la page {page_num}: {e}")
            return []
            
    def decode_email_from_script(self, script_text):
        """Décode l'email depuis le JavaScript d'obfuscation"""
        try:
            # Pattern amélioré pour extraire les variables du script
            addy_match = re.search(r"var addy[^=]*=\s*'([^']+)'", script_text)
            if not addy_match:
                return None
                
            local_part = addy_match.group(1)
            
            # Chercher la partie domaine
            domain_match = re.search(r"addy[^=]*=\s*addy[^+]*\+\s*'([^']+)'", script_text)
            if not domain_match:
                return None
                
            domain_part = domain_match.group(1)
            
            # Décoder les entités HTML
            html_entities = {
                '&#97;': 'a', '&#117;': 'u', '&#64;': '@', '&#105;': 'i',
                '&#46;': '.', '&#111;': 'o', '&#101;': 'e', '&#114;': 'r',
                '&#110;': 'n', '&#115;': 's', '&#99;': 'c', '&#109;': 'm',
                '&#108;': 'l', '&#116;': 't', '&#118;': 'v', '&#102;': 'f'
            }
            
            for entity, char in html_entities.items():
                local_part = local_part.replace(entity, char)
                domain_part = domain_part.replace(entity, char)
            
            email = local_part + domain_part
            
            # Validation basique de l'email
            if '@' in email and '.' in email.split('@')[1]:
                return email
                
        except Exception:
            pass
        return None
        
    def extract_lawyer_details(self, lawyer_url, retry_count=0):
        """Extrait les détails d'un avocat depuis sa page"""
        try:
            response = self.session.get(lawyer_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            lawyer_data = {
                'url': lawyer_url,
                'avocat_id': '',
                'prenom': '',
                'nom': '',
                'email': '',
                'annee_inscription': '',
                'numero_toque': '',
                'specialisations': [],
                'structure': '',
                'adresse_complete': '',
                'ville': '',
                'code_postal': '',
                'telephone_fixe': '',
                'telephone_fax': '',
                'langues': []
            }
            
            # Extraire l'ID de l'avocat depuis l'URL
            id_match = re.search(r'avocat_id=(\d+)', lawyer_url)
            if id_match:
                lawyer_data['avocat_id'] = id_match.group(1)
                
            # Extraction depuis la section lawyer-detail
            lawyer_detail = soup.find('div', class_='lawyer-detail')
            if not lawyer_detail:
                return None
                
            # Extraction du nom (depuis le h3)
            name_element = lawyer_detail.find('h3')
            if name_element:
                full_name = name_element.get_text(strip=True)
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    lawyer_data['prenom'] = name_parts[0]
                    lawyer_data['nom'] = ' '.join(name_parts[1:])
                else:
                    lawyer_data['nom'] = full_name
                    
            # Extraction du téléphone fixe et fax
            phone_links = lawyer_detail.find_all('a', href=re.compile(r'tel:'))
            for i, phone_link in enumerate(phone_links):
                phone = phone_link.get_text(strip=True)
                if i == 0 and phone:  # Premier numéro = fixe
                    lawyer_data['telephone_fixe'] = phone
                elif i == 1 and phone:  # Deuxième = fax
                    lawyer_data['telephone_fax'] = phone
                    
            # Extraction de l'email depuis le JavaScript
            script_tags = soup.find_all('script', type='text/javascript')
            for script in script_tags:
                if script.string and 'addy' in script.string:
                    email = self.decode_email_from_script(script.string)
                    if email:
                        lawyer_data['email'] = email
                        break
                        
            # Si pas d'email trouvé via JavaScript, chercher dans les liens mailto
            if not lawyer_data['email']:
                mailto_links = soup.find_all('a', href=re.compile(r'mailto:'))
                for link in mailto_links:
                    href = link.get('href', '')
                    email_match = re.search(r'mailto:([^?&]+)', href)
                    if email_match:
                        lawyer_data['email'] = email_match.group(1)
                        break
                        
            # Extraction de l'adresse complète
            page_text = soup.get_text()
            
            # Patterns d'adresses améliorés
            address_patterns = [
                r'(\d+[^,\n]*(?:rue|avenue|boulevard|place|allée|impasse|chemin)[^,\n]*\d{5}\s+[A-Z][A-Z\s]+)',
                r'(\d+[^\n]*(?:rue|avenue|boulevard|place|allée|impasse|chemin)[^\n]{10,80})',
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    address = matches[0].strip()
                    # Nettoyer l'adresse
                    address = re.sub(r'\s+', ' ', address)
                    if 15 < len(address) < 200:  # Longueur raisonnable
                        lawyer_data['adresse_complete'] = address
                        
                        # Extraire code postal et ville
                        cp_ville_match = re.search(r'(\d{5})\s+([A-Z][A-Z\s]+)', address)
                        if cp_ville_match:
                            lawyer_data['code_postal'] = cp_ville_match.group(1)
                            lawyer_data['ville'] = cp_ville_match.group(2).strip()
                        break
                        
            # Extraction du numéro de toque
            toque_patterns = [
                r'toque\s*:?\s*(\d+)',
                r'n°\s*toque\s*:?\s*(\d+)',
                r'numéro\s*toque\s*:?\s*(\d+)'
            ]
            
            for pattern in toque_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    lawyer_data['numero_toque'] = matches[0]
                    break
                    
            # Extraction de l'année d'inscription avec patterns plus précis
            year_patterns = [
                r'inscrit[e]?\s+(?:au\s+barreau\s+)?(?:en|depuis)\s+(\d{4})',
                r'inscription\s+(?:au\s+barreau\s+)?:?\s*(\d{4})',
                r'barreau\s+(?:depuis|en|de)\s+(\d{4})',
                r'asserment[é]?[e]?\s+en\s+(\d{4})',
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if 1950 <= int(match) <= 2024:
                        lawyer_data['annee_inscription'] = match
                        break
                if lawyer_data['annee_inscription']:
                    break
                    
            # Extraction des spécialisations avec une approche plus large
            specialisation_keywords = [
                'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
                'droit de la famille', 'droit immobilier', 'droit des affaires',
                'droit fiscal', 'droit social', 'divorce', 'succession',
                'préjudice corporel', 'accident de la route', 'dommage corporel',
                'responsabilité civile', 'contrat', 'propriété intellectuelle',
                'droit public', 'droit administratif', 'droit des sociétés',
                'droit bancaire', 'droit de l\'urbanisme', 'droit de la construction'
            ]
            
            text_lower = page_text.lower()
            for keyword in specialisation_keywords:
                if keyword in text_lower and keyword.title() not in lawyer_data['specialisations']:
                    lawyer_data['specialisations'].append(keyword.title())
                    
            # Extraction de la structure/cabinet avec patterns améliorés
            structure_patterns = [
                r'cabinet\s+([A-Z][^.\n]+)',
                r'société\s+([A-Z][^.\n]+)',
                r'scp\s+([^.\n]+)',
                r'selarl\s+([^.\n]+)',
                r'selas\s+([^.\n]+)',
                r'aarpi\s+([^.\n]+)',
            ]
            
            for pattern in structure_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    structure = matches[0].strip()
                    if 5 < len(structure) < 100:  # Longueur raisonnable
                        lawyer_data['structure'] = structure
                    break
                    
            # Si pas de structure trouvée, utiliser "Individuel"
            if not lawyer_data['structure']:
                lawyer_data['structure'] = f"Individuel {lawyer_data['prenom']} {lawyer_data['nom']}".strip()
                
            return lawyer_data
            
        except requests.RequestException as e:
            if retry_count < 2:
                print(f"    ⚠ Erreur réseau, nouvelle tentative... ({retry_count + 1}/3)")
                time.sleep(1)
                return self.extract_lawyer_details(lawyer_url, retry_count + 1)
            else:
                print(f"    ❌ Erreur définitive pour {lawyer_url}: {e}")
                return None
        except Exception as e:
            print(f"    ❌ Erreur lors de l'extraction de {lawyer_url}: {e}")
            return None
            
    def process_lawyer_batch(self, lawyer_urls, batch_id):
        """Traite un lot d'avocats"""
        results = []
        for i, url in enumerate(lawyer_urls, 1):
            avocat_id = url.split('=')[-1]
            print(f"    📂 Batch {batch_id} [{i}/{len(lawyer_urls)}] Avocat ID {avocat_id}")
            
            lawyer_data = self.extract_lawyer_details(url)
            if lawyer_data:
                results.append(lawyer_data)
                print(f"      ✅ {lawyer_data['prenom']} {lawyer_data['nom']}")
                print(f"      📧 Email: {lawyer_data['email'] or 'Non trouvé'}")
                
            # Pause entre les requêtes (optimisée pour production)
            time.sleep(0.3)
            
        return results
        
    def scrape_all_lawyers_production(self, start_page=1, end_page=69, max_workers=4):
        """🚀 SCRAPE TOUS LES AVOCATS - MODE PRODUCTION FINAL"""
        try:
            print("🚀 === SCRAPING PRODUCTION FINAL - BARREAU VAL DE MARNE ===")
            print(f"📋 Pages à traiter: {start_page} à {end_page} (TOTAL: {end_page} pages)")
            print(f"⚡ Parallélisation: {max_workers} workers")
            print(f"🎯 Estimation: ~{end_page * 9} avocats à extraire")
            print(f"⏱️ Temps estimé: {end_page * 2:.0f}-{end_page * 3:.0f} minutes")
            
            all_lawyers = []
            total_processed = 0
            
            for page_num in range(start_page, end_page + 1):
                print(f"\n📄 --- TRAITEMENT DE LA PAGE {page_num}/{end_page} ---")
                
                # Récupérer les URLs des avocats de cette page
                lawyer_urls = self.get_lawyers_urls_from_page(page_num)
                
                if not lawyer_urls:
                    print(f"⚠️ Aucun avocat trouvé sur la page {page_num}")
                    continue
                    
                # Diviser les URLs en lots pour la parallélisation
                batch_size = max(1, len(lawyer_urls) // max_workers)
                batches = [lawyer_urls[i:i + batch_size] for i in range(0, len(lawyer_urls), batch_size)]
                
                print(f"🔄 Traitement parallèle en {len(batches)} batches...")
                
                # Traitement parallèle des lots
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_batch = {executor.submit(self.process_lawyer_batch, batch, i+1): i+1 
                                     for i, batch in enumerate(batches)}
                    
                    for future in as_completed(future_to_batch):
                        batch_id = future_to_batch[future]
                        try:
                            batch_results = future.result()
                            all_lawyers.extend(batch_results)
                            total_processed += len(batch_results)
                        except Exception as e:
                            print(f"    ❌ Erreur dans le batch {batch_id}: {e}")
                            
                print(f"✅ Page {page_num} terminée: {len(lawyer_urls)} avocats traités")
                print(f"📊 Total cumulé: {total_processed} avocats extraits")
                
                # Pause entre les pages pour éviter la surcharge
                if page_num < end_page:
                    time.sleep(1)
                
            # Sauvegarder les résultats
            if all_lawyers:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                print(f"\n💾 === SAUVEGARDE DES RÉSULTATS ===")
                
                # Sauvegarde JSON
                json_filename = f"valdemarne_COMPLET_{timestamp}.json"
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_lawyers, f, indent=2, ensure_ascii=False)
                    
                # Sauvegarde CSV
                csv_filename = f"valdemarne_COMPLET_{timestamp}.csv"
                if all_lawyers:
                    fieldnames = all_lawyers[0].keys()
                    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for lawyer in all_lawyers:
                            row = lawyer.copy()
                            # Convertir les listes en chaînes pour le CSV
                            for key, value in row.items():
                                if isinstance(value, list):
                                    row[key] = '; '.join(value)
                            writer.writerow(row)
                            
                # Statistiques finales
                emails_found = sum(1 for l in all_lawyers if l.get('email'))
                phones_found = sum(1 for l in all_lawyers if l.get('telephone_fixe'))
                addresses_found = sum(1 for l in all_lawyers if l.get('adresse_complete'))
                years_found = sum(1 for l in all_lawyers if l.get('annee_inscription'))
                toques_found = sum(1 for l in all_lawyers if l.get('numero_toque'))
                
                print(f"\n🎉 === RÉSULTATS FINAUX ===")
                print(f"👥 Total avocats extraits: {len(all_lawyers)}")
                print(f"📧 Emails trouvés: {emails_found}/{len(all_lawyers)} ({emails_found/len(all_lawyers)*100:.1f}%)")
                print(f"📞 Téléphones trouvés: {phones_found}/{len(all_lawyers)} ({phones_found/len(all_lawyers)*100:.1f}%)")
                print(f"🏠 Adresses trouvées: {addresses_found}/{len(all_lawyers)} ({addresses_found/len(all_lawyers)*100:.1f}%)")
                print(f"📅 Années d'inscription: {years_found}/{len(all_lawyers)} ({years_found/len(all_lawyers)*100:.1f}%)")
                print(f"🏷️ Numéros de toque: {toques_found}/{len(all_lawyers)} ({toques_found/len(all_lawyers)*100:.1f}%)")
                print(f"\n📁 Fichiers générés:")
                print(f"  • {json_filename}")
                print(f"  • {csv_filename}")
                
            return all_lawyers
            
        except Exception as e:
            print(f"❌ Erreur durant le scraping: {e}")
            return []

def main():
    """LANCEMENT DU SCRAPER PRODUCTION FINAL"""
    
    print("🚀 INITIALISATION DU SCRAPER FINAL...")
    scraper = ValdeMarneProductionFinalScraper()
    
    try:
        print("\n🔥 LANCEMENT DU SCRAPING COMPLET DE L'ANNUAIRE")
        results = scraper.scrape_all_lawyers_production(start_page=1, end_page=69, max_workers=4)
        
        if results:
            print(f"\n✅ SCRAPING TERMINÉ AVEC SUCCÈS !")
            print(f"🎯 Nombre total d'avocats extraits: {len(results)}")
        else:
            print(f"\n❌ Aucun résultat obtenu")
            
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()