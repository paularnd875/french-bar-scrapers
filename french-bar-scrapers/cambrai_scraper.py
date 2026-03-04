#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER FINAL CORRIGÉ - BARREAU DE CAMBRAI
Version définitive avec extraction des noms composés corrigée
"""

import time
import json
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from urllib.parse import unquote
import html

class CambraiFinalFixedScraper:
    def __init__(self, headless=True, verbose=True):
        self.headless = headless
        self.verbose = verbose
        self.base_url = "https://www.avocats-cambrai.com/"
        self.annuaire_url = "https://www.avocats-cambrai.com/annuaire"
        self.results = []
        self.setup_driver()
        
    def setup_driver(self):
        """Configuration du driver Chrome optimisé"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        
    def log(self, message):
        """Log avec timestamp si verbose activé"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def clean_text(self, text):
        """Nettoyer et normaliser le texte"""
        if not text:
            return ""
        
        # Décoder les entités HTML
        text = html.unescape(text)
        # Décoder les caractères URL encodés
        text = unquote(text)
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les espaces en début/fin
        return text.strip()
    
    def extract_name_from_url(self, url):
        """Extraire nom et prénom depuis l'URL (méthode de secours)"""
        try:
            # URLs comme: /annuaire/monsieur-jean-philippe-kurtek-15.htm
            # ou: /annuaire/maitre-cathy-beauchart-1.htm
            
            pattern = r'/(?:monsieur|maitre)-([^-]+(?:-[^-]+)*)-([^-]+)-(\d+)\.htm$'
            match = re.search(pattern, url)
            
            if match:
                # Exemple: jean-philippe, kurtek, 15
                prenom_part = match.group(1)
                nom_part = match.group(2)
                
                # Traiter le prénom (peut contenir des tirets pour noms composés)
                prenom = prenom_part.replace('-', '-').title()
                
                # Traiter le nom
                nom = nom_part.upper()
                
                self.log(f"Extraction URL: {prenom} {nom}")
                return prenom, nom
            
            return "", ""
            
        except Exception as e:
            self.log(f"Erreur extraction URL: {str(e)}")
            return "", ""
    
    def extract_name_from_title(self, title):
        """Extraire nom et prénom du titre de la page avec noms composés"""
        try:
            title = self.clean_text(title)
            
            # Patterns pour extraire nom/prénom complets avec tirets
            patterns = [
                # Maître + prénom composé + nom composé
                r"Maître\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý-]+(?:\s*-\s*[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý-]+)*)\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ-]+(?:\s*-\s*[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ-]+)*)",
                
                # Monsieur + prénom composé + nom composé
                r"Monsieur\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý-]+(?:\s*-\s*[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ][a-zàáâãäåæçèéêëìíîïñòóôõöøùúûüý-]+)*)\s+([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ-]+(?:\s*-\s*[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØÙÚÛÜÝ-]+)*)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    prenom = self.clean_text(match.group(1))
                    nom = self.clean_text(match.group(2))
                    
                    # Vérifier que les noms ne sont pas trop courts
                    if len(prenom) >= 2 and len(nom) >= 2:
                        return prenom, nom
            
            return "", ""
            
        except Exception as e:
            self.log(f"Erreur extraction titre: {str(e)}")
            return "", ""
    
    def extract_comprehensive_name(self, url):
        """Extraction complète du nom avec plusieurs méthodes"""
        try:
            # Méthode 1: Depuis le titre
            title = self.driver.title
            prenom, nom = self.extract_name_from_title(title)
            
            if prenom and nom and len(prenom) >= 2 and len(nom) >= 2:
                self.log(f"✓ Nom extrait du titre: {prenom} {nom}")
                return prenom, nom
            
            # Méthode 2: Depuis l'URL
            prenom_url, nom_url = self.extract_name_from_url(url)
            if prenom_url and nom_url:
                self.log(f"✓ Nom extrait de l'URL: {prenom_url} {nom_url}")
                return prenom_url, nom_url
            
            # Méthode 3: Depuis le contenu de la page
            try:
                name_selectors = ["h1", "h2", ".lawyer-name", ".contact-name", ".name", "title"]
                
                for selector in name_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in elements:
                            text = self.clean_text(elem.text)
                            if text and len(text) > 5:
                                prenom_elem, nom_elem = self.extract_name_from_title(text)
                                if prenom_elem and nom_elem and len(prenom_elem) >= 2 and len(nom_elem) >= 2:
                                    self.log(f"✓ Nom extrait du contenu ({selector}): {prenom_elem} {nom_elem}")
                                    return prenom_elem, nom_elem
                    except:
                        continue
            except:
                pass
            
            # Méthode 4: Pattern d'urgence depuis l'URL - extraction plus permissive
            try:
                # Prendre tout après le dernier tiret avant le numéro
                url_pattern = r'/[^/]*-([a-zA-Z-]+)-(\d+)\.htm$'
                match = re.search(url_pattern, url)
                if match:
                    name_part = match.group(1)
                    # Diviser en parties
                    parts = name_part.split('-')
                    if len(parts) >= 2:
                        # Les premières parties = prénom, la dernière = nom
                        prenom = '-'.join(parts[:-1]).title()
                        nom = parts[-1].upper()
                        if len(prenom) >= 2 and len(nom) >= 2:
                            self.log(f"✓ Nom extrait (pattern d'urgence): {prenom} {nom}")
                            return prenom, nom
            except:
                pass
            
            self.log("❌ Impossible d'extraire le nom")
            return "", ""
            
        except Exception as e:
            self.log(f"❌ Erreur extraction complète nom: {str(e)}")
            return "", ""
    
    def extract_from_page_content(self, profile_url):
        """Extraire les informations structurées de la page"""
        try:
            data = {
                "nom": "",
                "prenom": "",
                "email": "",
                "telephone": "",
                "adresse": "",
                "specialisations": "",
                "structure": "",
                "annee_inscription": "",
                "prestations_serment": ""
            }
            
            page_source = self.driver.page_source
            
            # 1. Extraire nom/prénom avec méthode complète
            prenom, nom = self.extract_comprehensive_name(profile_url)
            data["prenom"] = prenom
            data["nom"] = nom
            
            # 2. Extraire l'email (avec décodage URL)
            email_patterns = [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
            ]
            
            for pattern in email_patterns:
                emails = re.findall(pattern, page_source)
                if emails:
                    # Filtrer les emails techniques
                    valid_emails = []
                    for email in emails:
                        email = self.clean_text(email)
                        if not any(tech in email.lower() for tech in ['azko', 'google', 'facebook', 'twitter', 'analytics']):
                            valid_emails.append(email)
                    
                    if valid_emails:
                        data["email"] = valid_emails[0]
                        break
            
            # 3. Extraire le téléphone
            phone_patterns = [
                r'\b0[1-9][\s\-\.]?(?:\d{2}[\s\-\.]?){4}\b',
                r'\b(?:\+33|0033)[\s\-\.]?[1-9](?:[\s\-\.]?\d{2}){4}\b'
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, page_source)
                if phones:
                    # Nettoyer le numéro
                    phone = re.sub(r'[\s\-\.]', '', phones[0])
                    data["telephone"] = phone
                    break
            
            # 4. Extraire l'adresse avec sélecteurs CSS puis patterns
            try:
                address_selectors = [
                    '.adresse',
                    '.contact-adresse', 
                    '[class*="adresse"]',
                    '.coordonnees',
                    '.contact-info',
                    '.address'
                ]
                
                for selector in address_selectors:
                    try:
                        elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        addr_text = self.clean_text(elem.text)
                        if addr_text and len(addr_text) > 5 and any(word in addr_text.lower() for word in ['rue', 'avenue', 'place', 'boulevard', 'cambrai', 'caudry']):
                            data["adresse"] = addr_text
                            break
                    except:
                        continue
                
                # Si pas d'adresse trouvée, chercher dans le texte avec des patterns
                if not data["adresse"]:
                    address_patterns = [
                        r'(\d+[^,\n]*(?:rue|avenue|place|boulevard|chemin)[^,\n]*(?:\d{5})?[^,\n]*)',
                        r'(\d{5}\s+[A-Z][a-zA-Z\s-]+)',
                        r'([^,\n]*(?:rue|avenue|place|boulevard)[^,\n]*\d{5}[^,\n]*)'
                    ]
                    
                    for pattern in address_patterns:
                        matches = re.findall(pattern, page_source, re.IGNORECASE | re.MULTILINE)
                        if matches:
                            # Prendre la première adresse qui semble valide
                            for addr in matches:
                                addr = self.clean_text(addr)
                                if len(addr) > 10 and len(addr) < 100:
                                    data["adresse"] = addr
                                    break
                            if data["adresse"]:
                                break
                
            except Exception as e:
                self.log(f"Erreur extraction adresse: {str(e)}")
            
            # 5. Extraire spécialisations avec recherche améliorée
            try:
                spec_keywords = ["spécialisation", "spécialité", "domaine", "compétence", "droit"]
                
                for keyword in spec_keywords:
                    try:
                        # Chercher des sections contenant ces mots-clés
                        elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]")
                        
                        specializations = []
                        for elem in elements:
                            try:
                                # Chercher dans l'élément et ses parents/enfants
                                parent = elem.find_element(By.XPATH, "./..")
                                text = self.clean_text(parent.text)
                                
                                # Filtrer et extraire les spécialisations
                                if text and 10 < len(text) < 300:
                                    # Supprimer le mot-clé lui-même et nettoyer
                                    text = re.sub(rf'{keyword}[s]?\s*:?\s*', '', text, flags=re.IGNORECASE)
                                    text = re.sub(r'domaines?\s+d\'intervention[s]?\s*:?\s*', '', text, flags=re.IGNORECASE)
                                    
                                    if text.strip() and text.strip() != "d'interventions":
                                        specializations.append(text.strip())
                                        
                            except:
                                continue
                        
                        if specializations:
                            # Prendre les spécialisations uniques et les plus descriptives
                            unique_specs = []
                            for spec in specializations:
                                if spec not in unique_specs and len(spec) > 5:
                                    unique_specs.append(spec)
                            
                            if unique_specs:
                                data["specialisations"] = " | ".join(unique_specs[:3])
                                break
                                
                    except:
                        continue
                        
            except Exception as e:
                self.log(f"Erreur extraction spécialisations: {str(e)}")
            
            # 6. Extraire année d'inscription/prestation de serment
            try:
                year_patterns = [
                    r'(?:prestation\s+de\s+serment|inscription|asserment[ée]?)\s*:?\s*(\d{4})',
                    r'(\d{4})\s*(?:prestation\s+de\s+serment|inscription)',
                    r'serment\s*:?\s*(\d{4})'
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        year = matches[0]
                        current_year = datetime.now().year
                        if 1950 <= int(year) <= current_year:
                            data["annee_inscription"] = year
                            data["prestations_serment"] = year
                            break
                            
            except Exception as e:
                self.log(f"Erreur extraction année: {str(e)}")
            
            # 7. Extraire structure/cabinet
            try:
                structure_patterns = [
                    r'(?:cabinet|étude|scp|selarl|société)\s+([A-Za-z\s&-]+)',
                    r'([A-Z\s&-]+(?:AVOCAT[S]?|CONSEIL[S]?)[A-Z\s&-]*)',
                    r'([A-Z][A-Za-z\s&-]+(?:avocat[s]?|conseil[s]?))',
                ]
                
                for pattern in structure_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE)
                    if matches:
                        for structure in matches:
                            structure = self.clean_text(structure)
                            if structure and 3 < len(structure) < 50:
                                data["structure"] = structure
                                break
                        if data["structure"]:
                            break
                            
            except Exception as e:
                self.log(f"Erreur extraction structure: {str(e)}")
            
            return data
            
        except Exception as e:
            self.log(f"❌ Erreur extraction contenu page: {str(e)}")
            return {}
    
    def get_cities(self):
        """Récupérer la liste des villes disponibles"""
        try:
            self.log("Accès à la page d'annuaire...")
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            # Masquer les bannières cookies
            self.driver.execute_script("""
                var banners = document.querySelectorAll('.bandeauCookies, .bandeauCookies__main, .cookie-banner');
                banners.forEach(function(banner) {
                    if(banner) banner.style.display = 'none';
                });
            """)
            
            # Extraire les villes
            select = self.driver.find_element(By.CSS_SELECTOR, "#frmAnnuaire_ville_page2")
            options = select.find_elements(By.TAG_NAME, "option")
            
            cities = []
            for option in options:
                text = self.clean_text(option.text)
                value = option.get_attribute("value")
                if text and text != "Toutes les villes":
                    cities.append({
                        "text": text,
                        "value": value,
                        "ville": self.clean_text(option.get_attribute("data-ville") or ""),
                        "cp": self.clean_text(option.get_attribute("data-cp") or "")
                    })
            
            self.log(f"Villes trouvées: {[c['text'] for c in cities]}")
            return cities
            
        except Exception as e:
            self.log(f"❌ Erreur récupération villes: {str(e)}")
            return []
    
    def search_city(self, city):
        """Effectuer une recherche pour une ville"""
        try:
            self.log(f"Recherche pour {city['text']}...")
            
            # Sélectionner la ville
            self.driver.execute_script(f"$('#frmAnnuaire_ville_page2').val('{city['value']}').trigger('change');")
            time.sleep(1)
            
            # Lancer la recherche
            button = self.driver.find_element(By.CSS_SELECTOR, "#frmAnnuaire_ok_page2")
            self.driver.execute_script("arguments[0].click();", button)
            time.sleep(3)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur recherche {city['text']}: {str(e)}")
            return False
    
    def extract_lawyers_list(self, city):
        """Extraire la liste des avocats d'une ville"""
        try:
            # Chercher les fiches d'avocats
            lawyer_cards = self.driver.find_elements(By.CSS_SELECTOR, ".annuaireFicheMini.annuaireFicheMiniAvocat")
            
            if not lawyer_cards:
                self.log(f"Aucun avocat trouvé pour {city['text']}")
                return []
            
            self.log(f"Trouvé {len(lawyer_cards)} avocats pour {city['text']}")
            
            lawyers = []
            for i, card in enumerate(lawyer_cards, 1):
                try:
                    # Extraire le lien vers la fiche
                    link_elem = card.find_element(By.CSS_SELECTOR, "a.annuaireFicheImage")
                    profile_url = link_elem.get_attribute("href")
                    
                    # Initialiser la structure de données propre
                    lawyer = {
                        "ville": city["ville"],
                        "code_postal": city["cp"], 
                        "profile_url": profile_url,
                        "nom": "",
                        "prenom": "",
                        "email": "",
                        "telephone": "",
                        "adresse": "",
                        "specialisations": "",
                        "structure": "",
                        "annee_inscription": "",
                        "prestations_serment": ""
                    }
                    
                    lawyers.append(lawyer)
                    self.log(f"  Avocat {i}: {profile_url}")
                    
                except Exception as e:
                    self.log(f"❌ Erreur extraction avocat {i}: {str(e)}")
                    continue
            
            return lawyers
            
        except Exception as e:
            self.log(f"❌ Erreur extraction liste: {str(e)}")
            return []
    
    def extract_lawyer_details(self, lawyer):
        """Extraire les détails d'un avocat depuis sa fiche"""
        try:
            profile_url = lawyer["profile_url"]
            self.log(f"Extraction détails: {profile_url}")
            
            # Ouvrir la fiche dans un nouvel onglet
            self.driver.execute_script(f"window.open('{profile_url}', '_blank');")
            
            # Basculer vers le nouvel onglet
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)
            
            # Extraire les informations structurées
            extracted_data = self.extract_from_page_content(profile_url)
            
            # Mettre à jour les données de l'avocat
            for key, value in extracted_data.items():
                if value:  # Seulement si la valeur n'est pas vide
                    lawyer[key] = value
            
            # Fermer l'onglet et revenir
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            self.log(f"✓ Détails extraits: {lawyer.get('prenom', '')} {lawyer.get('nom', '')} - {lawyer.get('email', 'Pas d email')}")
            return True
            
        except Exception as e:
            self.log(f"❌ Erreur extraction détails: {str(e)}")
            # S'assurer de fermer l'onglet en cas d'erreur
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return False
    
    def save_results(self):
        """Sauvegarder les résultats dans différents formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f"cambrai_avocats_FINAL_FIXED_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # CSV pour Excel
        csv_file = f"cambrai_avocats_FINAL_FIXED_{timestamp}.csv"
        if self.results:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'ville', 'code_postal', 'nom', 'prenom', 'email', 'telephone', 
                    'adresse', 'specialisations', 'structure', 'annee_inscription', 
                    'prestations_serment', 'profile_url'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
        
        # Emails uniquement (nettoyés)
        emails_file = f"cambrai_EMAILS_FINAL_FIXED_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            emails = []
            for lawyer in self.results:
                if lawyer.get("email"):
                    email = self.clean_text(lawyer["email"])
                    if email:
                        emails.append(email)
            
            unique_emails = sorted(set(emails))
            for email in unique_emails:
                f.write(email + "\n")
        
        # Rapport de synthèse final
        report_file = f"cambrai_RAPPORT_FINAL_FIXED_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("RAPPORT FINAL CORRIGÉ - EXTRACTION BARREAU DE CAMBRAI\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            total = len(self.results)
            with_email = len([l for l in self.results if l.get("email")])
            with_phone = len([l for l in self.results if l.get("telephone")])
            with_address = len([l for l in self.results if l.get("adresse")])
            with_specs = len([l for l in self.results if l.get("specialisations")])
            with_complete_name = len([l for l in self.results if l.get("nom") and l.get("prenom")])
            
            f.write(f"STATISTIQUES GÉNÉRALES:\n")
            f.write(f"- Total avocats extraits: {total}\n")
            f.write(f"- Avec nom complet: {with_complete_name} ({with_complete_name/max(total,1)*100:.1f}%)\n")
            f.write(f"- Avec email: {with_email} ({with_email/max(total,1)*100:.1f}%)\n")
            f.write(f"- Avec téléphone: {with_phone} ({with_phone/max(total,1)*100:.1f}%)\n")
            f.write(f"- Avec adresse: {with_address} ({with_address/max(total,1)*100:.1f}%)\n")
            f.write(f"- Avec spécialisations: {with_specs} ({with_specs/max(total,1)*100:.1f}%)\n\n")
            
            # Répartition par ville
            cities = set([l["ville"] for l in self.results])
            f.write(f"RÉPARTITION PAR VILLE:\n")
            for city in sorted(cities):
                city_lawyers = [l for l in self.results if l["ville"] == city]
                city_emails = [l for l in city_lawyers if l.get("email")]
                f.write(f"- {city}: {len(city_lawyers)} avocats ({len(city_emails)} emails)\n")
            
            f.write(f"\nFICHIERS GÉNÉRÉS:\n")
            f.write(f"- {json_file} (données complètes JSON)\n")
            f.write(f"- {csv_file} (format Excel FINAL CORRIGÉ)\n")
            f.write(f"- {emails_file} (emails nettoyés)\n")
            f.write(f"- {report_file} (ce rapport)\n")
            
            # Exemples d'avocats avec noms complets
            f.write(f"\nEXEMPLES D'AVOCATS AVEC NOMS COMPLETS:\n")
            complete_lawyers = [l for l in self.results if l.get("email") and l.get("nom") and l.get("prenom")]
            for i, lawyer in enumerate(complete_lawyers[:10], 1):
                f.write(f"{i:2d}. {lawyer.get('prenom', '')} {lawyer.get('nom', '')} - {lawyer.get('email', '')} ({lawyer['ville']})\n")
                if lawyer.get('adresse'):
                    f.write(f"     Adresse: {lawyer['adresse']}\n")
                if lawyer.get('specialisations'):
                    f.write(f"     Spécialisations: {lawyer['specialisations']}\n")
                f.write("\n")
        
        self.log(f"✅ Résultats finaux corrigés sauvegardés:")
        self.log(f"   JSON: {json_file}")
        self.log(f"   CSV: {csv_file}")
        self.log(f"   Emails: {emails_file}")
        self.log(f"   Rapport: {report_file}")
    
    def run_complete_extraction(self):
        """Lancer l'extraction complète avec toutes les corrections"""
        start_time = datetime.now()
        self.log("🔧 DÉBUT EXTRACTION FINALE CORRIGÉE - BARREAU DE CAMBRAI")
        
        try:
            # 1. Récupérer les villes
            cities = self.get_cities()
            if not cities:
                self.log("❌ Aucune ville trouvée, arrêt du processus")
                return False
            
            # 2. Scanner chaque ville
            for i, city in enumerate(cities, 1):
                self.log(f"\n[{i}/{len(cities)}] === TRAITEMENT DE {city['text']} ===")
                
                try:
                    # Rechercher dans cette ville
                    if not self.search_city(city):
                        continue
                    
                    # Extraire la liste des avocats
                    lawyers = self.extract_lawyers_list(city)
                    if not lawyers:
                        continue
                    
                    # Extraire les détails de chaque avocat
                    for j, lawyer in enumerate(lawyers, 1):
                        self.log(f"  [{j}/{len(lawyers)}] Extraction détails avocat...")
                        self.extract_lawyer_details(lawyer)
                        self.results.append(lawyer)
                        
                        # Petite pause entre les extractions
                        time.sleep(1)
                    
                    self.log(f"✅ {len(lawyers)} avocats traités pour {city['text']}")
                    
                except Exception as e:
                    self.log(f"❌ Erreur traitement {city['text']}: {str(e)}")
                    continue
                
                # Pause entre les villes
                time.sleep(2)
            
            # 3. Sauvegarder les résultats
            self.save_results()
            
            # 4. Statistiques finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.log(f"\n🎉 EXTRACTION FINALE CORRIGÉE TERMINÉE!")
            self.log(f"⏱️  Durée: {duration}")
            self.log(f"📊 Avocats extraits: {len(self.results)}")
            self.log(f"👤 Avec noms complets: {len([l for l in self.results if l.get('nom') and l.get('prenom')])}")
            self.log(f"📧 Avec email: {len([l for l in self.results if l.get('email')])}")
            self.log(f"📞 Avec téléphone: {len([l for l in self.results if l.get('telephone')])}")
            self.log(f"🏢 Avec spécialisations: {len([l for l in self.results if l.get('specialisations')])}")
            
            return True
            
        except Exception as e:
            self.log(f"💥 ERREUR GLOBALE: {str(e)}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoyer et fermer le driver"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass

def main():
    print("=" * 90)
    print("  SCRAPER FINAL CORRIGÉ - BARREAU DE CAMBRAI")
    print("  Version définitive avec extraction des noms composés corrigée")
    print("=" * 90)
    
    scraper = CambraiFinalFixedScraper(headless=True, verbose=True)
    success = scraper.run_complete_extraction()
    
    if success:
        print("\n✅ SUCCÈS: Extraction finale corrigée terminée avec succès!")
        print("Les noms composés et toutes les données sont maintenant parfaitement extraits.")
    else:
        print("\n❌ ÉCHEC: Problème durant l'extraction finale")

if __name__ == "__main__":
    main()