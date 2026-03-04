#!/usr/bin/env python3
"""
Scraper COMPLET pour le Barreau de Libourne
Version finale avec liste exacte des 77 avocats
Gestion optimisée des cookies et anti-détection
"""

import time
import json
import csv
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import urllib.parse

class LibourneCompletScraper:
    def __init__(self, headless=True, test_mode=False):
        self.lawyers_list = self.get_lawyers_list()
        self.results = []
        self.headless = headless
        self.test_mode = test_mode
        self.setup_driver()
        
    def get_lawyers_list(self):
        """Liste complète des 77 avocats fournie"""
        lawyers = [
            ("ABDOUL Paméla", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/abdoul-pam%C3%A9la/"),
            ("AKPO Ghislain", "https://www.barreaulibourne.fr/annuaire-1/akpo-ghislain/"),
            ("BAULIMON Arnaud", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/baulimon-arnaud/"),
            ("BEAUVILAIN Natacha", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/beauvilain-natacha/"),
            ("BECAM Florian", "https://www.barreaulibourne.fr/annuaire-1/becam-florian/"),
            ("BERARD Luc", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/berard-luc/"),
            ("BERGER-SOULET Marie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/berger-marie/"),
            ("BONNAN David", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/bonnan-davis/"),
            ("BONNER-BRISSAUD Anne Claire", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/bonner-anne-claire/"),
            ("BOUGUIER Donatien", "https://www.barreaulibourne.fr/annuaire-1/bouguier-donatien/"),
            ("BOUKOULOU Pharès", "https://www.barreaulibourne.fr/annuaire-1/boukoulou-phar%C3%A8s/"),
            ("BOYE-PONSAN Florence", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/boye-florence/"),
            ("BREDIN - KUILAGI Hélène", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/bredin-h%C3%A9l%C3%A8ne/"),
            ("BRUN Anne Laure", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/brun-anne-laure/"),
            ("CARBONNIER Antoine", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/carbonnier-antoine/"),
            ("CHIGNAGUE Christine", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/chignague-christine/"),
            ("CHUDZIAK Raymond", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/chudziak-raymond/"),
            ("CHUDZIAK-BIOULOU Delphine", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/chudziak-bioulou-delphine/"),
            ("CILIENTO François", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/ciliento-fran%C3%A7ois/"),
            ("CLAVEL Sophie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/clavel-sophie/"),
            ("CLERGET Caroline", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/clerget-caroline/"),
            ("COULEUVRE Jean-Luc", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/couleuvre-jean-luc/"),
            ("DEBENAT Marion", "https://www.barreaulibourne.fr/annuaire-1/debenat-marion/"),
            ("DE LUNARDO Thomas", "https://www.barreaulibourne.fr/annuaire-1/de-lunardo-thomas/"),
            ("DE VASSELOT Briac", "https://www.barreaulibourne.fr/annuaire-1/de-vasselot-briac-1/"),
            ("DECOUX Anne-Sophie", "https://www.barreaulibourne.fr/annuaire-1/decoux-anne-sophie-1/"),
            ("DJE Séverin", "https://www.barreaulibourne.fr/annuaire-1/dje-s%C3%A9verin/"),
            ("DOLEAC Christophe", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/doleac-christophe/"),
            ("DROUAULT Nicolas", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/drouault-nicolas/"),
            ("DUFFAU-LAGARROSSE Paule", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/duffau-lagarrosse-paule/"),
            ("DUVAL-VERON Constance", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/duval-veron-constance/"),
            ("DYKMAN Julie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/dykman-julie/"),
            ("EBISSAYI Marius", "https://www.barreaulibourne.fr/annuaire-1/ebissayi-marius/"),
            ("FOURMON Elodie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/fourmon-leclercq-elodie/"),
            ("FOUSSARD-LAFON Céline", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/foussard-lafon-c%C3%A9line/"),
            ("GAUCHER-PIOLA Alexis", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/gaucher-piola-alexis/"),
            ("GODIN Coralie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/guiter-marion/"),
            ("GUITER Marion", "https://www.barreaulibourne.fr/annuaire-1/guiter-marion/"),
            ("HASSINE Nadia", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/hassine-nadia/"),
            ("HELIAS Yannick", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/helias-yannick/"),
            ("JANOUEIX Hélène", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/janoueix-h%C3%A9l%C3%A8ne/"),
            ("JARRIOT Julien", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/kuznik-val%C3%A9rie/"),
            ("JUSSIAUME Quentin", "https://www.barreaulibourne.fr/annuaire-1/jussiaume-quentin/"),
            ("KUZNIK Valérie", "https://www.barreaulibourne.fr/annuaire-1/kuznik-val%C3%A9rie-1/"),
            ("LABARRIERE Laure", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/labarriere-laure/"),
            ("LATAILLADE Arnaud", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/lataillade-arnaud/"),
            ("LECOQ Isabelle", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/lecoq-isabelle/"),
            ("LEMELLE Elise", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/magret-jean-philippe/"),
            ("LLAMMAS Henri", "https://www.barreaulibourne.fr/annuaire-1/llammas-henri/"),
            ("LUDIG Héloîse", "https://www.barreaulibourne.fr/annuaire-1/ludig-h%C3%A9lo%C3%AEse/"),
            ("MAGRET Jean-Philippe", "https://www.barreaulibourne.fr/annuaire-1/magret-jean-philippe/"),
            ("MASSIAS Mélina", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/massias-m%C3%A9lina/"),
            ("MAU Vireak", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/mau-vireak/"),
            ("MILLAS-CONTESTIN Dominique", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/millas-contestin-dominique/"),
            ("MOLTENI Félix", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/molteni-f%C3%A9lix/"),
            ("MONROUX Raphael", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/monroux-raphael/"),
            ("NAUD-CARON Carole", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/naud-caron-carole/"),
            ("NEBOLSINE Ariadna", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/nebolsine-ariadna/"),
            ("NORMAND Justine", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/normand-justine/"),
            ("PAIS Isabelle", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/pais-isabelle/"),
            ("PERROGON Marie-Andrée", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/perrogon-marie-andr%C3%A9e/"),
            ("POPA Elena", "https://www.barreaulibourne.fr/annuaire-1/popa-elena/"),
            ("PROVOST Loïc", "https://www.barreaulibourne.fr/annuaire-1/provost-lo%C3%AFc/"),
            ("REGES Caroline", "https://www.barreaulibourne.fr/annuaire-1/reges-caroline/"),
            ("REYNET ADRIEN", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/rodriguez-marjorie/"),
            ("RODRIGUEZ Marjorie", "https://www.barreaulibourne.fr/annuaire-1/rodriguez-marjorie/"),
            ("ROHOU Alice", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/rudler-am%C3%A9lie/"),
            ("RUDLER Amélie", "https://www.barreaulibourne.fr/annuaire-1/rudler-am%C3%A9lie/"),
            ("RUFFIE François", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/ruffie-fran%C3%A7ois/"),
            ("SINATRA Romain", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/sinatra-romain/"),
            ("STAROSSE Sophie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/starosse-sophie/"),
            ("TAINTENIER-MARTIN Hélène", "https://www.barreaulibourne.fr/annuaire-1/taintenier-martin-h%C3%A9l%C3%A8ne/"),
            ("TAMBO Stéphanie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/tambo-st%C3%A9phanie/"),
            ("TOSTAIN Emilie", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/tostain-emilie/"),
            ("TRESTARD Emmanuel", "https://www.barreaulibourne.fr/annuaire/liste-des-avocats/trestard-emmanuel/"),
            ("VIGNAUD Morgane", "https://www.barreaulibourne.fr/annuaire-1/vignaud-morgane/"),
            ("WURTZ Claire", "https://www.barreaulibourne.fr/annuaire-1/wurtz-claire/")
        ]
        return lawyers
        
    def setup_driver(self):
        """Configuration optimisée du driver Chrome avec anti-détection"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
            
        # Options anti-détection avancées
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent réaliste
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Options performance
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Accélère le chargement
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Masquer l'automation
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.wait = WebDriverWait(self.driver, 15)
        
    def random_delay(self, min_sec=1, max_sec=3):
        """Délai aléatoire pour éviter la détection"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        
    def accept_cookies(self):
        """Gestion intelligente des cookies"""
        try:
            print("🍪 Vérification des cookies...")
            self.random_delay(2, 4)
            
            # Liste exhaustive de sélecteurs possibles
            cookie_selectors = [
                "button[id*='cookie' i]",
                "button[class*='cookie' i]",
                "button[id*='accept' i]",
                "button[class*='accept' i]",
                "[data-cookie='accept']",
                ".cookie-accept",
                "#cookie-accept",
                ".tarteaucitronAllow",
                "#tarteaucitronPersonalize2",
                ".tarteaucitron-button",
                "button:contains('Accepter')",
                "button:contains('Accept')",
                "button:contains('OK')",
                "button:contains('J\\'accepte')"
            ]
            
            for selector in cookie_selectors:
                try:
                    if ":contains(" in selector:
                        text = selector.split("'")[1]
                        xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            print(f"✅ Cookie button trouvé: {selector}")
                            self.driver.execute_script("arguments[0].click();", element)
                            self.random_delay(1, 2)
                            return True
                except Exception:
                    continue
                    
            print("ℹ️ Aucun banner de cookies détecté")
            return True
            
        except Exception as e:
            print(f"⚠️ Erreur cookies: {str(e)}")
            return True
            
    def extract_lawyer_data(self, name, url, index):
        """Extraire toutes les données d'un avocat"""
        try:
            print(f"📋 [{index+1}/77] Extraction: {name}")
            
            # Navigation vers la page
            self.driver.get(url)
            self.random_delay(2, 4)
            
            # Structure des données
            lawyer_data = {
                "index": index + 1,
                "nom_complet": name,
                "prenom": "",
                "nom": "",
                "email": "",
                "telephone": "",
                "adresse": "",
                "code_postal": "",
                "ville": "",
                "annee_inscription": "",
                "specialisations": [],
                "competences": [],
                "structure": "",
                "url": url,
                "extraction_reussie": False
            }
            
            # Séparer prénom et nom
            self.split_name(lawyer_data)
            
            # Extraire email
            email = self.find_email()
            if email:
                lawyer_data["email"] = email
                
            # Extraire téléphone
            phone = self.find_phone()
            if phone:
                lawyer_data["telephone"] = phone
                
            # Extraire adresse
            address_data = self.find_address()
            if address_data:
                lawyer_data.update(address_data)
                
            # Extraire année d'inscription
            year = self.find_inscription_year()
            if year:
                lawyer_data["annee_inscription"] = year
                
            # Extraire spécialisations
            specs = self.find_specializations()
            if specs:
                lawyer_data["specialisations"] = specs
                
            # Extraire compétences
            comps = self.find_competences()
            if comps:
                lawyer_data["competences"] = comps
                
            # Extraire structure
            structure = self.find_structure()
            if structure:
                lawyer_data["structure"] = structure
                
            # Marquer comme réussie si au moins email ou téléphone
            if lawyer_data["email"] or lawyer_data["telephone"]:
                lawyer_data["extraction_reussie"] = True
                
            print(f"✅ {name}: Email={bool(lawyer_data['email'])}, Tel={bool(lawyer_data['telephone'])}")
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur {name}: {str(e)}")
            lawyer_data = {
                "index": index + 1,
                "nom_complet": name,
                "url": url,
                "extraction_reussie": False,
                "erreur": str(e)
            }
            self.split_name(lawyer_data)
            return lawyer_data
            
    def split_name(self, lawyer_data):
        """Séparation intelligente prénom/nom avec gestion des noms composés"""
        full_name = lawyer_data["nom_complet"].strip()
        
        # Nettoyer le nom
        clean_name = re.sub(r'^(Me|Maître|M\.|Mme|Mlle)\.?\s*', '', full_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'\s*\(.*?\)\s*', '', clean_name)
        
        # Gestion des noms avec particules (DE, DU, VAN, etc.)
        if re.match(r'^(DE|DU|VAN|VON|LA|LE|LES)\s+', clean_name, re.IGNORECASE):
            parts = clean_name.split()
            if len(parts) >= 3:
                # Particule + nom + prénom(s)
                lawyer_data["nom"] = " ".join(parts[:2])  # Particule + nom
                lawyer_data["prenom"] = " ".join(parts[2:])  # Prénom(s)
            elif len(parts) == 2:
                lawyer_data["nom"] = " ".join(parts)
                lawyer_data["prenom"] = ""
        else:
            # Cas standard : prénom(s) + nom
            parts = clean_name.split()
            if len(parts) >= 2:
                # Dernier mot = nom, le reste = prénom(s)
                lawyer_data["nom"] = parts[-1]
                lawyer_data["prenom"] = " ".join(parts[:-1])
            elif len(parts) == 1:
                lawyer_data["nom"] = parts[0]
                lawyer_data["prenom"] = ""
            else:
                lawyer_data["nom"] = full_name
                lawyer_data["prenom"] = ""
                
    def find_email(self):
        """Recherche intelligente d'email"""
        try:
            # Recherche dans le texte de la page
            page_source = self.driver.page_source
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, page_source)
            
            # Filtrer les emails valides
            valid_emails = []
            for email in emails:
                email_lower = email.lower()
                if not any(ext in email_lower for ext in ['.jpg', '.png', '.gif', '.svg', '.css', '.js']):
                    if '@' in email and '.' in email.split('@')[1]:
                        valid_emails.append(email)
                        
            # Recherche dans les liens mailto
            try:
                mailto_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                for link in mailto_links:
                    href = link.get_attribute("href")
                    if href:
                        email = href.replace("mailto:", "").split("?")[0]
                        if email not in valid_emails:
                            valid_emails.append(email)
            except:
                pass
                
            return valid_emails[0] if valid_emails else None
            
        except Exception as e:
            print(f"⚠️ Erreur email: {str(e)}")
            return None
            
    def find_phone(self):
        """Recherche de numéro de téléphone"""
        try:
            page_text = self.driver.page_source
            
            # Patterns pour téléphone français
            phone_patterns = [
                r'(?:(?:\+33|0)[1-9])(?:[.\s-]?\d{2}){4}',
                r'0[1-9](?:[.\s-]?\d{2}){4}',
                r'\+33[1-9](?:[.\s-]?\d{2}){4}'
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, page_text)
                if phones:
                    # Nettoyer et formater
                    phone = phones[0]
                    phone = re.sub(r'[.\s-]', ' ', phone)
                    phone = re.sub(r'\s+', ' ', phone).strip()
                    return phone
                    
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur téléphone: {str(e)}")
            return None
            
    def find_address(self):
        """Recherche d'adresse complète améliorée"""
        try:
            address_data = {
                "adresse": "",
                "code_postal": "",
                "ville": ""
            }
            
            # Récupérer le texte visible uniquement
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Pattern pour adresse française standard
            address_patterns = [
                r'(\d+[\w\s,.-]+?)\s*(\d{5})\s*([A-Za-zÀ-ÿ\s-]{3,50})',
                r'(\d+[^0-9\n]*?)\s*(\d{5})\s*([A-Za-zÀ-ÿ\s-]+)',
                r'((?:\d+|rue|avenue|boulevard|place)[^0-9\n]*?)\s*(\d{5})\s*(\w+(?:\s+\w+)*)'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    addr, postal, city = match
                    
                    # Nettoyer les données
                    addr = re.sub(r'[^\w\s,.-]', '', addr).strip()
                    postal = postal.strip()
                    city = re.sub(r'[^\w\s-]', '', city).strip()
                    
                    # Vérifier que c'est valide
                    if (len(addr) > 3 and len(addr) < 100 and 
                        postal.isdigit() and len(postal) == 5 and
                        len(city) > 2 and len(city) < 50):
                        
                        address_data["adresse"] = addr
                        address_data["code_postal"] = postal
                        address_data["ville"] = city
                        return address_data
                
            # Si pas d'adresse complète, chercher au moins la ville
            city_pattern = r'(\d{5})\s*([A-Za-zÀ-ÿ\s-]{3,30})'
            city_matches = re.findall(city_pattern, page_text)
            for postal, city in city_matches:
                if postal.isdigit() and len(city) > 2:
                    address_data["code_postal"] = postal
                    address_data["ville"] = re.sub(r'[^\w\s-]', '', city).strip()
                    break
                
            return address_data
            
        except Exception as e:
            print(f"⚠️ Erreur adresse: {str(e)}")
            return {}
            
    def find_inscription_year(self):
        """Recherche année d'inscription"""
        try:
            page_text = self.driver.page_source.lower()
            
            year_patterns = [
                r'inscri[tp].*?(\d{4})',
                r'barreau.*?(\d{4})',
                r'admission.*?(\d{4})',
                r'serment.*?(\d{4})'
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    year = int(match)
                    if 1950 <= year <= 2024:
                        return year
                        
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur année: {str(e)}")
            return None
            
    def find_specializations(self):
        """Recherche spécialisations"""
        try:
            specializations = []
            page_text = self.driver.page_source
            
            # Patterns de recherche
            spec_patterns = [
                r'spécialisations?[:\s]*([^<\n]{10,200})',
                r'compétences?[:\s]*([^<\n]{10,200})',
                r'domaines?[:\s]*([^<\n]{10,200})'
            ]
            
            for pattern in spec_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text and len(clean_text) > 5:
                        specializations.append(clean_text)
                        
            return specializations[:5]  # Max 5 spécialisations
            
        except Exception as e:
            print(f"⚠️ Erreur spécialisations: {str(e)}")
            return []
            
    def find_competences(self):
        """Recherche compétences distinctes des spécialisations"""
        try:
            competences = []
            
            # Recherche dans des éléments spécifiques
            comp_selectors = [
                ".competences", ".skills", ".expertise",
                ".practice-areas", ".domaines"
            ]
            
            for selector in comp_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 5:
                            competences.append(text)
                except:
                    continue
                    
            return competences[:3]  # Max 3 compétences
            
        except Exception as e:
            print(f"⚠️ Erreur compétences: {str(e)}")
            return []
            
    def find_structure(self):
        """Recherche structure/cabinet"""
        try:
            page_text = self.driver.page_source
            
            struct_patterns = [
                r'cabinet[:\s]*([^<\n]{5,100})',
                r'structure[:\s]*([^<\n]{5,100})',
                r'société[:\s]*([^<\n]{5,100})',
                r'scpa?[:\s]*([^<\n]{5,100})'
            ]
            
            for pattern in struct_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    clean_text = re.sub(r'<[^>]+>', '', match).strip()
                    if clean_text and len(clean_text) > 3:
                        return clean_text
                        
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur structure: {str(e)}")
            return None
            
    def save_results(self, lawyers, mode="COMPLET"):
        """Sauvegarde des résultats avec statistiques"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Statistiques
        total = len(lawyers)
        successful = len([l for l in lawyers if l.get("extraction_reussie", False)])
        with_email = len([l for l in lawyers if l.get("email")])
        with_phone = len([l for l in lawyers if l.get("telephone")])
        
        prefix = f"LIBOURNE_{mode}_{total}avocats"
        
        # Sauvegarde JSON
        json_file = f"{prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, ensure_ascii=False, indent=2)
            
        # Sauvegarde CSV
        csv_file = f"{prefix}_{timestamp}.csv"
        if lawyers:
            fieldnames = ['prenom', 'nom', 'nom_complet', 'email', 'telephone', 
                         'adresse', 'code_postal', 'ville', 'annee_inscription',
                         'specialisations', 'competences', 'structure', 'url', 'extraction_reussie']
                         
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in lawyers:
                    row = {}
                    for field in fieldnames:
                        value = lawyer.get(field, '')
                        if isinstance(value, list):
                            value = '; '.join(str(v) for v in value)
                        row[field] = str(value)
                    writer.writerow(row)
                    
        # Fichier emails uniquement
        emails_file = f"{prefix}_EMAILS_{timestamp}.txt"
        unique_emails = set()
        for lawyer in lawyers:
            email = lawyer.get("email", "")
            if email and "@" in email:
                unique_emails.add(email)
                
        with open(emails_file, 'w', encoding='utf-8') as f:
            for email in sorted(unique_emails):
                f.write(f"{email}\n")
                
        # Rapport détaillé
        report_file = f"{prefix}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT FINAL - SCRAPING BARREAU LIBOURNE\n")
            f.write(f"=" * 50 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Mode: {mode}\n")
            f.write(f"Liste fournie: 77 avocats\n\n")
            f.write(f"RÉSULTATS:\n")
            f.write(f"- Total traités: {total}\n")
            f.write(f"- Extractions réussies: {successful} ({successful/total*100:.1f}%)\n")
            f.write(f"- Avec email: {with_email} ({with_email/total*100:.1f}%)\n")
            f.write(f"- Avec téléphone: {with_phone} ({with_phone/total*100:.1f}%)\n")
            f.write(f"- Emails uniques: {len(unique_emails)}\n\n")
            
            f.write(f"FICHIERS GÉNÉRÉS:\n")
            f.write(f"- JSON: {json_file}\n")
            f.write(f"- CSV: {csv_file}\n")
            f.write(f"- Emails: {emails_file}\n")
            f.write(f"- Rapport: {report_file}\n\n")
            
            if successful > 0:
                f.write(f"DÉTAIL DES EXTRACTIONS RÉUSSIES:\n")
                f.write(f"-" * 40 + "\n")
                for i, lawyer in enumerate([l for l in lawyers if l.get("extraction_reussie", False)], 1):
                    f.write(f"{i}. {lawyer.get('nom_complet', 'N/A')}\n")
                    f.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                    f.write(f"   Tél: {lawyer.get('telephone', 'N/A')}\n\n")
                    
        print(f"\n💾 SAUVEGARDE TERMINÉE:")
        print(f"   📊 CSV: {csv_file}")
        print(f"   📧 Emails: {emails_file}")
        print(f"   📋 Rapport: {report_file}")
        print(f"   📈 Taux de réussite: {successful/total*100:.1f}%")
        
        return csv_file, emails_file, report_file
        
    def run_extraction(self):
        """Lancer l'extraction complète"""
        try:
            total_lawyers = len(self.lawyers_list)
            limit = 10 if self.test_mode else total_lawyers
            
            print(f"🚀 DÉBUT EXTRACTION LIBOURNE")
            print(f"Mode: {'TEST (10 premiers)' if self.test_mode else 'COMPLET'}")
            print(f"Total: {limit}/{total_lawyers} avocats")
            print("=" * 60)
            
            # Traiter chaque avocat
            for i, (name, url) in enumerate(self.lawyers_list[:limit]):
                lawyer_data = self.extract_lawyer_data(name, url, i)
                self.results.append(lawyer_data)
                
                # Sauvegarde intermédiaire tous les 20
                if (i + 1) % 20 == 0:
                    print(f"💾 Sauvegarde intermédiaire après {i + 1} avocats...")
                    self.save_results(self.results, mode="PARTIEL")
                    
                # Délai anti-détection
                self.random_delay(1, 2)
                
            # Sauvegarde finale
            mode = "TEST" if self.test_mode else "FINAL"
            self.save_results(self.results, mode=mode)
            
            # Statistiques finales
            successful = len([r for r in self.results if r.get("extraction_reussie", False)])
            print(f"\n🎉 EXTRACTION TERMINÉE!")
            print(f"✅ {successful}/{limit} avocats extraits avec succès")
            print(f"📧 {len(set([r.get('email') for r in self.results if r.get('email')]))} emails uniques")
            
            return self.results
            
        except Exception as e:
            print(f"❌ Erreur générale: {str(e)}")
            # Sauvegarder ce qui a été fait
            if self.results:
                self.save_results(self.results, mode="ERREUR")
            return None
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

if __name__ == "__main__":
    print("🏛️ SCRAPER BARREAU LIBOURNE - VERSION FINALE")
    print("=" * 60)
    
    # Mode test ou complet
    import sys
    test_mode = "--test" in sys.argv
    headless_mode = "--headless" in sys.argv or not test_mode
    
    if test_mode:
        print("🧪 MODE TEST: Extraction des 10 premiers avocats")
    else:
        print("🚀 MODE COMPLET: Extraction des 77 avocats")
        
    scraper = LibourneCompletScraper(headless=headless_mode, test_mode=test_mode)
    results = scraper.run_extraction()
    
    if results:
        successful = len([r for r in results if r.get("extraction_reussie", False)])
        print(f"\n🏆 MISSION ACCOMPLIE!")
        print(f"📊 {successful} extractions réussies sur {len(results)}")
    else:
        print("\n❌ Échec de l'extraction - vérifiez les logs")