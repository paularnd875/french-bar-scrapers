#!/usr/bin/env python3
"""
SCRAPER ENHANCED - Barreau d'Arras - Version améliorée
Version optimisée avec reprise automatique, validation, et rapports détaillés
"""

import requests
import json
import os
import pickle
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
import csv
import logging
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin, urlparse
from pathlib import Path

class ArrasEnhancedScraper:
    def __init__(self, delay_between_requests=2, session_file="arras_session.pkl"):
        self.base_url = "https://avocatsarras.com"
        self.annuaire_url = "https://avocatsarras.com/annuaire/"
        self.session = requests.Session()
        self.lawyers_data = []
        self.delay = delay_between_requests
        self.total_pages = 0
        self.processed_count = 0
        self.session_file = session_file
        self.start_time = None
        
        # Configuration logging
        self.setup_logging()
        
        # Headers optimisés
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        # Statistiques améliorées
        self.stats = {
            'total_found': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'emails_found': 0,
            'phones_found': 0,
            'addresses_found': 0,
            'specializations_found': 0,
            'years_found': 0,
            'start_time': None,
            'end_time': None,
            'resumed_from': None
        }
    
    def setup_logging(self):
        """Configure le système de logging"""
        log_format = '[%(asctime)s] %(levelname)s: %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt='%H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'arras_scraper_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: str = "INFO"):
        """Logging unifié"""
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def save_session(self):
        """Sauvegarde l'état de la session pour reprise"""
        session_data = {
            'lawyers_data': self.lawyers_data,
            'processed_count': self.processed_count,
            'total_pages': self.total_pages,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            self.log(f"💾 Session sauvegardée: {len(self.lawyers_data)} avocats")
        except Exception as e:
            self.log(f"❌ Erreur sauvegarde session: {e}", "ERROR")
    
    def load_session(self) -> bool:
        """Charge une session précédente si elle existe"""
        if not os.path.exists(self.session_file):
            return False
        
        try:
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            self.lawyers_data = session_data.get('lawyers_data', [])
            self.processed_count = session_data.get('processed_count', 0)
            self.total_pages = session_data.get('total_pages', 0)
            self.stats = session_data.get('stats', self.stats)
            
            self.stats['resumed_from'] = session_data.get('timestamp')
            
            self.log(f"🔄 Session restaurée: {len(self.lawyers_data)} avocats déjà traités")
            return True
        except Exception as e:
            self.log(f"❌ Erreur chargement session: {e}", "ERROR")
            return False
    
    def validate_email(self, email: str) -> bool:
        """Validation robuste des emails"""
        if not email or '@' not in email:
            return False
        
        # Patterns de validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Vérifications supplémentaires
        if not email_pattern.match(email):
            return False
        
        # Exclusions communes
        invalid_patterns = [
            r'.*@.*\.local$',
            r'.*@.*\.test$',
            r'.*@.*example.*',
            r'.*noreply.*',
            r'.*no-reply.*'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, email, re.IGNORECASE):
                return False
        
        return True
    
    def validate_phone(self, phone: str) -> bool:
        """Validation robuste des téléphones français"""
        if not phone:
            return False
        
        # Nettoyage
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Longueur valide
        if len(clean_phone) < 9 or len(clean_phone) > 12:
            return False
        
        # Patterns français
        french_patterns = [
            r'^0[1-9]\d{8}$',           # 0X XX XX XX XX
            r'^\+33[1-9]\d{8}$',        # +33 X XX XX XX XX
            r'^33[1-9]\d{8}$'           # 33 X XX XX XX XX
        ]
        
        return any(re.match(pattern, clean_phone) for pattern in french_patterns)
    
    def clean_address(self, address: str) -> str:
        """Nettoyage et validation d'adresse"""
        if not address:
            return ""
        
        # Nettoyage basique
        cleaned = re.sub(r'\s+', ' ', address.strip())
        cleaned = re.sub(r'[^\w\s\-,\.°]', ' ', cleaned)
        
        # Longueur raisonnable
        if len(cleaned) < 10 or len(cleaned) > 200:
            return ""
        
        return cleaned
    
    def get_page_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Récupération robuste avec retry et gestion d'erreurs améliorée"""
        for attempt in range(max_retries):
            try:
                self.log(f"🌐 GET {url} (tentative {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Vérification du contenu
                if len(response.text) < 100:
                    raise Exception("Contenu trop court, possible erreur")
                
                self.log(f"✅ OK ({response.status_code}, {len(response.text)} chars)")
                return response.text
                
            except requests.exceptions.Timeout:
                self.log(f"⏱️ Timeout tentative {attempt + 1}", "WARNING")
            except requests.exceptions.ConnectionError:
                self.log(f"🔌 Problème connexion tentative {attempt + 1}", "WARNING")
            except requests.exceptions.HTTPError as e:
                self.log(f"🌐 Erreur HTTP {e.response.status_code} tentative {attempt + 1}", "WARNING")
            except Exception as e:
                self.log(f"❌ Erreur tentative {attempt + 1}: {e}", "WARNING")
            
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                self.log(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                time.sleep(wait_time)
        
        self.log(f"❌ Échec définitif pour {url}", "ERROR")
        return None
    
    def discover_total_pages(self) -> int:
        """Découverte améliorée du nombre de pages"""
        self.log("🔍 Découverte du nombre de pages...")
        
        content = self.get_page_content(self.annuaire_url)
        if not content:
            self.log("❌ Impossible d'accéder à la page principale", "ERROR")
            return 0
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Méthodes multiples de détection pagination
        page_numbers = []
        
        # Méthode 1: liens pagination classiques
        pagination_links = soup.find_all('a', href=re.compile(r'/page/\d+/'))
        for link in pagination_links:
            match = re.search(r'/page/(\d+)/', link.get('href', ''))
            if match:
                page_numbers.append(int(match.group(1)))
        
        # Méthode 2: recherche dans le texte
        text_content = soup.get_text()
        page_text_matches = re.findall(r'page\s+(\d+)', text_content, re.IGNORECASE)
        for match in page_text_matches:
            if 1 <= int(match) <= 50:  # Limite raisonnable
                page_numbers.append(int(match))
        
        # Méthode 3: navigation directe
        nav_elements = soup.find_all(['nav', 'div'], class_=re.compile(r'pag', re.I))
        for nav in nav_elements:
            nav_text = nav.get_text()
            nav_matches = re.findall(r'\b(\d+)\b', nav_text)
            for match in nav_matches:
                if 1 <= int(match) <= 50:
                    page_numbers.append(int(match))
        
        if page_numbers:
            self.total_pages = max(page_numbers)
        else:
            self.total_pages = 1
            self.log("⚠️ Pagination non détectée, assume 1 page", "WARNING")
        
        self.log(f"📊 Nombre de pages détecté: {self.total_pages}")
        return self.total_pages
    
    def get_lawyers_from_page(self, page_num: int) -> List[Dict]:
        """Extraction améliorée des avocats d'une page"""
        if page_num == 1:
            url = self.annuaire_url
        else:
            url = f"{self.annuaire_url}page/{page_num}/"
        
        self.log(f"📄 Traitement page {page_num}/{self.total_pages}")
        
        content = self.get_page_content(url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Patterns de détection des avocats
        lawyer_links = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Critères stricts pour les avocats uniquement
            if '/specialite-avocat/' in href and 'avocatsarras.com' in href:
                # Filtrage du bruit et validation du nom
                excluded_terms = ['mentions', 'contact', 'accueil', 'plan', 'accès', 'avocat', 'articles', 'compte']
                
                if (len(text) > 5 and 
                    len(text.split()) >= 2 and  # Au moins prénom + nom
                    not any(noise in text.lower() for noise in excluded_terms) and
                    re.search(r'[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûü]+', text) and  # Contient des noms propres
                    not text.lower().startswith(('le ', 'la ', 'les ', 'un ', 'une '))):  # Pas d'articles
                    
                    lawyer_links.append({
                        'url': href if href.startswith('http') else urljoin(self.base_url, href),
                        'name': text,
                        'page': page_num
                    })
        
        # Déduplication
        seen_urls = set()
        unique_lawyers = []
        for lawyer in lawyer_links:
            if lawyer['url'] not in seen_urls:
                seen_urls.add(lawyer['url'])
                unique_lawyers.append(lawyer)
        
        self.log(f"👥 {len(unique_lawyers)} avocats uniques trouvés sur la page {page_num}")
        return unique_lawyers
    
    def extract_complete_lawyer_info(self, lawyer_info: Dict) -> Optional[Dict]:
        """Extraction complète optimisée avec validation"""
        url = lawyer_info['url']
        expected_name = lawyer_info['name']
        page = lawyer_info['page']
        
        self.processed_count += 1
        self.log(f"🔍 [{self.processed_count}] Extraction: {expected_name}")
        
        content = self.get_page_content(url)
        if not content:
            self.stats['failed_extractions'] += 1
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
            "description": "",
            "status_extraction": "success",
            "extraction_timestamp": datetime.now().isoformat(),
            "data_quality_score": 0
        }
        
        try:
            text_content = soup.get_text()
            
            # EMAIL - Validation améliorée
            emails = set()
            
            # Liens mailto
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                email = link.get('href', '').lower().replace('mailto:', '').strip()
                if self.validate_email(email):
                    emails.add(email)
            
            # Regex dans le texte avec validation
            email_matches = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text_content)
            for email in email_matches:
                if self.validate_email(email.lower()):
                    emails.add(email.lower())
            
            if emails:
                lawyer_data["email"] = sorted(list(emails))[0]  # Le plus "propre"
                self.stats['emails_found'] += 1
                lawyer_data["data_quality_score"] += 3
            
            # TÉLÉPHONE - Validation améliorée
            phone_text = re.sub(r'[^0-9+\s\-\.]', ' ', text_content)
            phone_patterns = [
                r'(\+33[1-9](?:[\s\-\.]?[0-9]){8})',
                r'(0[1-9](?:[\s\-\.]?[0-9]){8})',
                r'(33[1-9](?:[\s\-\.]?[0-9]){8})'
            ]
            
            phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, phone_text)
                for match in matches:
                    clean_phone = re.sub(r'[^\d+]', '', str(match))
                    if self.validate_phone(clean_phone):
                        phones.add(clean_phone)
            
            if phones:
                lawyer_data["telephone"] = sorted(list(phones))[0]
                self.stats['phones_found'] += 1
                lawyer_data["data_quality_score"] += 2
            
            # FAX
            fax_patterns = [
                r'fax[\s:]*([0-9\s\.\-\+]{9,})',
                r'télécopie[\s:]*([0-9\s\.\-\+]{9,})'
            ]
            
            for pattern in fax_patterns:
                fax_matches = re.findall(pattern, text_content, re.IGNORECASE)
                for fax_match in fax_matches:
                    clean_fax = re.sub(r'[^0-9+]', '', fax_match)
                    if self.validate_phone(clean_fax):
                        lawyer_data["fax"] = clean_fax
                        lawyer_data["data_quality_score"] += 1
                        break
                if lawyer_data["fax"]:
                    break
            
            # ADRESSE - Patterns améliorés
            address_patterns = [
                r'(\d+[^\n]*(?:rue|avenue|place|boulevard|allée|impasse|cours|chemin)[^\n]*)',
                r'([^\n]*(?:rue|avenue|place|boulevard|allée|impasse|cours|chemin)[^\n]*\d+[^\n]*)',
                r'(\d+[^\n]*(?:62\d{3}|Arras)[^\n]*)',
                r'([^\n]*(?:62\d{3}|Arras)[^\n]*\d+[^\n]*)'
            ]
            
            best_address = ""
            best_score = 0
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    cleaned = self.clean_address(match)
                    if cleaned:
                        # Score de qualité d'adresse
                        score = 0
                        if re.search(r'\d+', cleaned): score += 1
                        if re.search(r'(rue|avenue|place|boulevard)', cleaned, re.I): score += 2
                        if re.search(r'62\d{3}', cleaned): score += 3
                        if 'arras' in cleaned.lower(): score += 1
                        
                        if score > best_score:
                            best_address = cleaned
                            best_score = score
            
            if best_address:
                lawyer_data["adresse_complete"] = best_address
                self.stats['addresses_found'] += 1
                lawyer_data["data_quality_score"] += 2
                
                # Extraction code postal et ville
                cp_match = re.search(r'(62\d{3})', best_address)
                if cp_match:
                    lawyer_data["code_postal"] = cp_match.group(1)
                    
                    # Ville après le code postal
                    ville_match = re.search(rf'{cp_match.group(1)}\s*([A-Za-zÀ-ÿ\s\-]+)', best_address)
                    if ville_match:
                        ville = ville_match.group(1).strip()[:50]
                        # Nettoyage ville
                        ville = re.sub(r'[^\w\s\-À-ÿ]', '', ville).strip()
                        if ville:
                            lawyer_data["ville"] = ville
            
            # SPÉCIALISATIONS - Extraction précise depuis la section "product_meta"
            specialisations = []
            
            # Chercher spécifiquement dans la div class="product_meta" pour éviter le menu de navigation
            product_meta = soup.find('div', class_='product_meta')
            if product_meta:
                # Chercher le span "posted_in" qui contient les catégories
                posted_in = product_meta.find('span', class_='posted_in')
                if posted_in:
                    # Extraire le texte entre "Catégorie :" et les liens
                    category_text = posted_in.get_text()
                    # Nettoyer le texte et extraire seulement la spécialisation
                    # Gérer les espaces insécables (\xa0) et les différents formats
                    category_text = category_text.replace('\xa0', ' ')  # Remplacer espace insécable
                    
                    if 'Catégorie' in category_text and ':' in category_text:
                        # Utiliser regex pour extraire ce qui suit "Catégorie" + espaces + ":"
                        category_match = re.search(r'Catégorie\s*:\s*(.+)', category_text, re.IGNORECASE)
                        if category_match:
                            category = category_match.group(1).strip()
                            # Ne pas inclure "Généraliste" car ce n'est pas une vraie spécialisation
                            if category and category.lower() not in ['généraliste', 'generaliste'] and len(category) > 2:
                                specialisations.append(category)
            
            # Si aucune spécialisation trouvée dans product_meta, essayer la méthode alternative
            if not specialisations:
                # Chercher dans le HTML brut pour "Catégorie :" mais seulement dans le contenu principal
                main_content = soup.find('div', class_='et_pb_section')
                if main_content:
                    content_html = str(main_content)
                    category_pattern = r'<span[^>]*class="posted_in"[^>]*>.*?Catégorie\s*:\s*<a[^>]*>([^<]+)</a>'
                    category_match = re.search(category_pattern, content_html, re.IGNORECASE | re.DOTALL)
                    if category_match:
                        category = category_match.group(1).strip()
                        if category and category.lower() not in ['généraliste', 'generaliste'] and len(category) > 2:
                            specialisations.append(category)
                            
            lawyer_data["specialisations"] = specialisations
            
            # ANNÉE D'INSCRIPTION - Patterns étendus
            inscription_patterns = [
                r'inscrit[e]?.*?(?:au\s+)?barreau.*?([12][0-9]{3})',
                r'barreau.*?([12][0-9]{3})',
                r'([12][0-9]{3}).*?inscrit',
                r'serment.*?([12][0-9]{3})',
                r'admission.*?([12][0-9]{3})',
                r'asserment[é]?.*?([12][0-9]{3})'
            ]
            
            for pattern in inscription_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    year = str(match)
                    if 1950 <= int(year) <= 2025:
                        lawyer_data["annee_inscription"] = year
                        self.stats['years_found'] += 1
                        lawyer_data["data_quality_score"] += 1
                        break
                if lawyer_data["annee_inscription"]:
                    break
            
            # STRUCTURE/CABINET
            cabinet_patterns = [
                r'cabinet\s+([^\n\.]{5,100})',
                r'société\s+([^\n\.]{5,100})',
                r'scp\s+([^\n\.]{5,100})',
                r'selarl\s+([^\n\.]{5,100})',
                r'selas\s+([^\n\.]{5,100})',
                r'sel\s+([^\n\.]{5,100})'
            ]
            
            for pattern in cabinet_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    cabinet = matches[0].strip()[:150]
                    cabinet = re.sub(r'\s+', ' ', cabinet)
                    if len(cabinet) > 3:
                        lawyer_data["structure_cabinet"] = cabinet
                        lawyer_data["data_quality_score"] += 1
                        break
            
            # SITE WEB
            web_links = soup.find_all('a', href=re.compile(r'^https?://'))
            for link in web_links:
                href = link.get('href', '')
                if ('avocatsarras.com' not in href and 
                    any(tld in href for tld in ['.com', '.fr', '.org', '.net']) and
                    not any(exclude in href for exclude in ['facebook', 'twitter', 'linkedin', 'google'])):
                    lawyer_data["site_web"] = href
                    lawyer_data["data_quality_score"] += 1
                    break
            
            # DESCRIPTION
            desc_elements = soup.find_all(['p', 'div'], string=re.compile(r'.{50,}'))
            descriptions = []
            for elem in desc_elements[:3]:  # Max 3 paragraphes
                text = elem.get_text(strip=True)
                if 50 <= len(text) <= 500 and expected_name.split()[0].lower() not in text.lower():
                    descriptions.append(text)
            
            if descriptions:
                lawyer_data["description"] = " ".join(descriptions)[:800]
                lawyer_data["data_quality_score"] += 1
            
            # PARSING PRÉNOM/NOM amélioré
            if lawyer_data["nom_complet"]:
                clean_name = lawyer_data["nom_complet"]
                clean_name = re.sub(r'(maitre|me\.?|avocat|cabinet)', '', clean_name, flags=re.IGNORECASE).strip()
                clean_name = re.sub(r'[^a-zA-ZÀ-ÿ\s\-]', '', clean_name)
                
                name_parts = [part for part in clean_name.split() if len(part) > 1]
                if len(name_parts) >= 2:
                    lawyer_data["nom"] = name_parts[-1].upper()
                    lawyer_data["prenom"] = " ".join(name_parts[:-1]).title()
                elif len(name_parts) == 1:
                    lawyer_data["nom"] = name_parts[0].upper()
            
            # Finalisation des stats
            self.stats['successful_extractions'] += 1
            
        except Exception as e:
            self.log(f"❌ Erreur lors de l'extraction de {expected_name}: {e}", "ERROR")
            lawyer_data["status_extraction"] = "partial_error"
            lawyer_data["error_message"] = str(e)
            self.stats['failed_extractions'] += 1
        
        return lawyer_data
    
    def save_progress(self, filename_suffix: str = "") -> Tuple[str, str]:
        """Sauvegarde améliorée avec métadonnées"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Métadonnées
        metadata = {
            "generation_timestamp": timestamp,
            "scraper_version": "enhanced_v1.0",
            "total_extracted": len(self.lawyers_data),
            "stats": self.stats,
            "session_resumed": self.stats.get('resumed_from') is not None
        }
        
        # JSON complet avec métadonnées
        json_file = f"arras_enhanced{filename_suffix}_{timestamp}.json"
        complete_data = {
            "metadata": metadata,
            "lawyers": self.lawyers_data
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(complete_data, f, indent=2, ensure_ascii=False)
        
        # CSV optimisé
        csv_file = f"arras_enhanced{filename_suffix}_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = [
                'ordre_extraction', 'nom_complet', 'prenom', 'nom', 'email', 'telephone', 'fax',
                'adresse_complete', 'ville', 'code_postal', 'specialisations', 'annee_inscription',
                'structure_cabinet', 'site_web', 'description', 'data_quality_score',
                'page_source', 'url', 'status_extraction', 'extraction_timestamp'
            ]
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    row = {k: lawyer.get(k, '') for k in fieldnames}
                    row['specialisations'] = "; ".join(lawyer.get('specialisations', []))
                    writer.writerow(row)
        
        # Rapport détaillé
        report_file = f"arras_report{filename_suffix}_{timestamp}.txt"
        self.generate_detailed_report(report_file)
        
        self.log(f"💾 Sauvegarde: {json_file}, {csv_file}, {report_file}")
        return json_file, csv_file
    
    def generate_detailed_report(self, filename: str):
        """Génère un rapport détaillé"""
        duration = datetime.now() - self.start_time if self.start_time else None
        
        report = f"""
=== RAPPORT DÉTAILLÉ SCRAPER ARRAS ENHANCED ===
Généré le: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}

🎯 RÉSULTATS GLOBAUX
═══════════════════════════════════════════════════════════
📊 Total avocats traités: {len(self.lawyers_data)}
✅ Extractions réussies: {self.stats['successful_extractions']}
❌ Extractions échouées: {self.stats['failed_extractions']}
📈 Taux de réussite: {(self.stats['successful_extractions']/(self.stats['successful_extractions']+self.stats['failed_extractions'])*100):.1f}%
⏱️ Durée totale: {duration if duration else 'N/A'}

🔍 QUALITÉ DES DONNÉES EXTRAITES
═══════════════════════════════════════════════════════════
📧 Emails trouvés: {self.stats['emails_found']}/{len(self.lawyers_data)} ({(self.stats['emails_found']/len(self.lawyers_data)*100) if self.lawyers_data else 0:.1f}%)
📞 Téléphones trouvés: {self.stats['phones_found']}/{len(self.lawyers_data)} ({(self.stats['phones_found']/len(self.lawyers_data)*100) if self.lawyers_data else 0:.1f}%)
🏠 Adresses trouvées: {self.stats['addresses_found']}/{len(self.lawyers_data)} ({(self.stats['addresses_found']/len(self.lawyers_data)*100) if self.lawyers_data else 0:.1f}%)
⚖️ Spécialisations trouvées: {self.stats['specializations_found']}/{len(self.lawyers_data)} ({(self.stats['specializations_found']/len(self.lawyers_data)*100) if self.lawyers_data else 0:.1f}%)
📅 Années inscription trouvées: {self.stats['years_found']}/{len(self.lawyers_data)} ({(self.stats['years_found']/len(self.lawyers_data)*100) if self.lawyers_data else 0:.1f}%)

📈 ANALYSE DE QUALITÉ
═══════════════════════════════════════════════════════════
"""
        
        if self.lawyers_data:
            # Statistiques de qualité
            quality_scores = [lawyer.get('data_quality_score', 0) for lawyer in self.lawyers_data]
            avg_quality = sum(quality_scores) / len(quality_scores)
            high_quality = len([s for s in quality_scores if s >= 7])
            
            report += f"Score de qualité moyen: {avg_quality:.1f}/10\n"
            report += f"Avocats haute qualité (≥7/10): {high_quality}/{len(self.lawyers_data)} ({high_quality/len(self.lawyers_data)*100:.1f}%)\n\n"
            
            # Top spécialisations
            all_specs = []
            for lawyer in self.lawyers_data:
                all_specs.extend(lawyer.get('specialisations', []))
            
            if all_specs:
                from collections import Counter
                spec_counts = Counter(all_specs)
                report += "🔝 TOP SPÉCIALISATIONS\n"
                report += "═══════════════════════════════════════════════════════════\n"
                for spec, count in spec_counts.most_common(10):
                    report += f"{spec}: {count} avocats\n"
        
        report += f"""

⚙️ CONFIGURATION TECHNIQUE
═══════════════════════════════════════════════════════════
Délai entre requêtes: {self.delay}s
Pages traitées: {self.total_pages}
Session reprise: {'Oui' if self.stats.get('resumed_from') else 'Non'}
Version scraper: Enhanced v1.0
Site cible: {self.base_url}

📁 FICHIERS GÉNÉRÉS
═══════════════════════════════════════════════════════════
- Données JSON complètes avec métadonnées
- Export CSV pour analyse
- Log détaillé de l'exécution
- Ce rapport de synthèse

=== FIN DU RAPPORT ===
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
    
    def run_enhanced_scraping(self, resume_session: bool = True) -> bool:
        """Lance le scraping complet avec fonctionnalités avancées"""
        self.start_time = datetime.now()
        self.stats['start_time'] = self.start_time.isoformat()
        
        self.log("🚀 DÉMARRAGE SCRAPER ARRAS ENHANCED")
        self.log("=" * 60)
        
        # Tentative de reprise de session
        if resume_session and self.load_session():
            self.log(f"🔄 Reprise de session: {len(self.lawyers_data)} avocats déjà traités")
            response = input("Voulez-vous reprendre la session existante ? (oui/non): ").lower().strip()
            if response not in ['oui', 'o', 'yes', 'y']:
                self.lawyers_data = []
                self.processed_count = 0
                self.stats = {key: 0 if isinstance(value, int) else value for key, value in self.stats.items()}
                self.log("🔄 Session réinitialisée")
        
        try:
            # 1. Découverte du nombre de pages
            if self.total_pages == 0:
                total_pages = self.discover_total_pages()
                if total_pages == 0:
                    self.log("❌ Impossible de déterminer le nombre de pages", "ERROR")
                    return False
            
            # 2. Collecte de tous les liens d'avocats (uniquement les nouveaux si reprise)
            self.log("📋 Collecte des liens d'avocats...")
            all_lawyers = []
            
            # URLs déjà traitées (si reprise)
            processed_urls = {lawyer['url'] for lawyer in self.lawyers_data}
            
            for page_num in range(1, self.total_pages + 1):
                lawyers_on_page = self.get_lawyers_from_page(page_num)
                
                # Filtrer les avocats déjà traités
                new_lawyers = [l for l in lawyers_on_page if l['url'] not in processed_urls]
                all_lawyers.extend(new_lawyers)
                
                if page_num < self.total_pages:
                    time.sleep(self.delay)
            
            self.stats['total_found'] = len(all_lawyers) + len(self.lawyers_data)
            self.log(f"👥 TOTAL: {len(all_lawyers)} nouveaux avocats à traiter")
            self.log(f"📊 Déjà traités: {len(self.lawyers_data)} avocats")
            
            if not all_lawyers and not self.lawyers_data:
                self.log("❌ Aucun avocat trouvé", "ERROR")
                return False
            
            # 3. Extraction des données pour chaque avocat
            if all_lawyers:
                self.log("🔍 Démarrage extraction individuelle...")
                
                for i, lawyer_info in enumerate(all_lawyers, 1):
                    try:
                        # Progress
                        progress = f"[{i}/{len(all_lawyers)}]"
                        total_progress = f"[Global: {len(self.lawyers_data)+i}/{self.stats['total_found']}]"
                        self.log(f"📄 {progress} {total_progress} {lawyer_info['name']}")
                        
                        # Extraction
                        lawyer_data = self.extract_complete_lawyer_info(lawyer_info)
                        
                        if lawyer_data:
                            self.lawyers_data.append(lawyer_data)
                            
                            # Log des infos essentielles avec score qualité
                            info_summary = []
                            if lawyer_data.get('email'):
                                info_summary.append(f"📧 {lawyer_data['email']}")
                            if lawyer_data.get('telephone'):
                                info_summary.append(f"📞 {lawyer_data['telephone']}")
                            if lawyer_data.get('annee_inscription'):
                                info_summary.append(f"📅 {lawyer_data['annee_inscription']}")
                            
                            quality = lawyer_data.get('data_quality_score', 0)
                            info_summary.append(f"🎯 Q:{quality}/10")
                            
                            if info_summary:
                                self.log(f"✅ Données: {' | '.join(info_summary)}")
                            else:
                                self.log("✅ Extraction OK (données minimales)")
                        else:
                            self.log("❌ Échec extraction", "ERROR")
                        
                        # Sauvegarde intermédiaire et session
                        if i % 10 == 0:
                            self.save_progress(f"_partial_{len(self.lawyers_data)}")
                            self.save_session()
                            self.log(f"💾 Sauvegarde intermédiaire ({len(self.lawyers_data)} traités)")
                        
                        # Pause entre les requêtes
                        if i < len(all_lawyers):
                            time.sleep(self.delay)
                            
                    except KeyboardInterrupt:
                        self.log("⏸️ INTERRUPTION UTILISATEUR", "WARNING")
                        self.save_session()
                        break
                    except Exception as e:
                        self.log(f"❌ Erreur inattendue pour {lawyer_info.get('name', 'N/A')}: {e}", "ERROR")
                        continue
            
            # 4. Sauvegarde finale
            self.log("💾 Sauvegarde finale...")
            self.stats['end_time'] = datetime.now().isoformat()
            final_files = self.save_progress("_FINAL")
            
            # Nettoyage session
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            
            # 5. Rapport final détaillé
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            self.log("=" * 60)
            self.log("📊 RAPPORT FINAL ENHANCED")
            self.log("=" * 60)
            self.log(f"⏱️ Durée totale: {duration}")
            self.log(f"📄 Pages traitées: {self.total_pages}")
            self.log(f"👥 Avocats découverts: {self.stats['total_found']}")
            self.log(f"✅ Extractions réussies: {self.stats['successful_extractions']}")
            self.log(f"❌ Extractions échouées: {self.stats['failed_extractions']}")
            
            if self.stats['total_found'] > 0:
                success_rate = (self.stats['successful_extractions']/self.stats['total_found']*100)
                self.log(f"📈 Taux de réussite: {success_rate:.1f}%")
            
            self.log(f"💾 Fichiers finaux: {final_files[0]} & {final_files[1]}")
            
            # Statistiques qualité détaillées
            if self.lawyers_data:
                avg_quality = sum(l.get('data_quality_score', 0) for l in self.lawyers_data) / len(self.lawyers_data)
                high_quality = len([l for l in self.lawyers_data if l.get('data_quality_score', 0) >= 7])
                
                self.log(f"🎯 Score qualité moyen: {avg_quality:.1f}/10")
                self.log(f"⭐ Avocats haute qualité: {high_quality}/{len(self.lawyers_data)} ({high_quality/len(self.lawyers_data)*100:.1f}%)")
                
                self.log(f"📧 Emails: {self.stats['emails_found']}/{len(self.lawyers_data)} ({self.stats['emails_found']/len(self.lawyers_data)*100:.1f}%)")
                self.log(f"📞 Téléphones: {self.stats['phones_found']}/{len(self.lawyers_data)} ({self.stats['phones_found']/len(self.lawyers_data)*100:.1f}%)")
                self.log(f"🏠 Adresses: {self.stats['addresses_found']}/{len(self.lawyers_data)} ({self.stats['addresses_found']/len(self.lawyers_data)*100:.1f}%)")
            
            return True
            
        except Exception as e:
            self.log(f"❌ ERREUR CRITIQUE: {e}", "ERROR")
            self.save_session()  # Sauvegarde d'urgence
            return False

def main():
    """Fonction principale avec options avancées"""
    print("\n🚀 SCRAPER BARREAU D'ARRAS - VERSION ENHANCED")
    print("=" * 55)
    print("✨ Nouvelles fonctionnalités:")
    print("   • Reprise automatique en cas d'interruption")
    print("   • Validation avancée des données")
    print("   • Score de qualité des données")
    print("   • Rapports détaillés")
    print("   • Logging complet")
    print("")
    
    # Configuration
    delay = 2
    try:
        custom_delay = input(f"Délai entre requêtes (défaut: {delay}s): ").strip()
        if custom_delay:
            delay = float(custom_delay)
    except ValueError:
        pass
    
    resume = True
    resume_input = input("Activer la reprise automatique ? (oui/non, défaut: oui): ").strip().lower()
    if resume_input in ['non', 'n', 'no']:
        resume = False
    
    print(f"\n⚙️ Configuration:")
    print(f"   • Délai: {delay}s")
    print(f"   • Reprise: {'Activée' if resume else 'Désactivée'}")
    print("🚀 Démarrage du scraping enhanced...\n")
    
    # Lancement du scraper
    scraper = ArrasEnhancedScraper(delay_between_requests=delay)
    success = scraper.run_enhanced_scraping(resume_session=resume)
    
    if success:
        print("\n🎉 SCRAPING ENHANCED TERMINÉ AVEC SUCCÈS!")
        print("📁 Fichiers générés:")
        print("   • JSON avec métadonnées complètes")
        print("   • CSV pour analyse")
        print("   • Rapport détaillé")
        print("   • Logs d'exécution")
    else:
        print("\n❌ Le scraping enhanced a échoué.")
        print("📋 Vérifiez les logs pour plus d'informations.")

if __name__ == "__main__":
    main()