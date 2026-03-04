#!/usr/bin/env python3
"""
Scraper COMPLET pour le Barreau de Blois
Extrait TOUTES les informations disponibles pour TOUS les avocats
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BloisScraperCompletToutesInfos:
    def __init__(self, headless=True):
        self.base_url = "https://avocats-blois.com/trouver-un-avocat/"
        self.lawyers_data = []
        
        # Configuration Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def accept_cookies(self):
        """Accepte les cookies"""
        try:
            logger.info("Recherche du bandeau de cookies...")
            time.sleep(3)
            cookie_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepter')]")))
            cookie_button.click()
            logger.info("Cookies acceptés")
            time.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Pas de cookies: {e}")
            return True
    
    def get_all_lawyer_links(self):
        """Récupère tous les liens vers les fiches d'avocats"""
        try:
            logger.info("Récupération de TOUS les liens d'avocats...")
            
            # Aller sur la page principale
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Scroll pour charger tout
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Méthode 1: liens "lire plus"
            lire_plus_links = []
            try:
                lire_plus_elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'lire plus')]")
                for element in lire_plus_elements:
                    href = element.get_attribute('href')
                    if href:
                        lire_plus_links.append(href)
                logger.info(f"Liens 'lire plus' trouvés: {len(lire_plus_links)}")
            except:
                pass
            
            # Méthode 2: noms d'avocats dans les H2
            h2_name_links = []
            try:
                h2_elements = self.driver.find_elements(By.XPATH, "//h2//a")
                for element in h2_elements:
                    href = element.get_attribute('href')
                    text = element.text.strip()
                    if (href and 
                        'category' not in href and 
                        'droit-' not in href and
                        len(text.split()) >= 2 and
                        not any(skip in href for skip in ['contact', 'mentions', 'politique'])):
                        h2_name_links.append(href)
                logger.info(f"Liens dans H2 trouvés: {len(h2_name_links)}")
            except:
                pass
            
            # Combiner tous les liens
            all_lawyer_links = set(lire_plus_links + h2_name_links)
            
            # Filtrer pour garder seulement les vrais avocats
            final_links = []
            for link in all_lawyer_links:
                # Vérifier que c'est bien une fiche d'avocat
                if (link and
                    'avocats-blois.com/' in link and
                    not any(exclude in link for exclude in [
                        'category/', 'droit-', 'domaine-intervention', 
                        'contact', 'mentions', 'politique', 'accueil',
                        'palais-de-justice', 'honoraires', 'adresses-utiles',
                        'followers', 'trouver-un-avocat'
                    ]) and
                    len(link.split('/')[-2]) > 3):  # Nom pas trop court
                    
                    final_links.append(link)
            
            final_links = sorted(list(set(final_links)))
            
            logger.info(f"=== RECENSEMENT FINAL ===")
            logger.info(f"Total fiches d'avocats trouvées: {len(final_links)}")
            
            return final_links
            
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return []
    
    def extract_lawyer_complete_details(self, lawyer_url):
        """Extrait TOUTES les informations disponibles d'un avocat"""
        try:
            logger.info(f"Extraction complète: {lawyer_url.split('/')[-2]}")
            self.driver.get(lawyer_url)
            time.sleep(4)
            
            lawyer_data = {
                'url': lawyer_url,
                'nom': '',
                'prenom': '',
                'nom_complet': '',
                'civilite': '',  # M. / Mme
                'titre': '',     # Maître, etc.
                'email': '',
                'telephone': '',
                'fax': '',
                'adresse_complete': '',
                'adresse_ligne1': '',
                'adresse_ligne2': '',
                'code_postal': '',
                'ville': '',
                'site_web': '',
                'date_serment': '',
                'annee_inscription': '',
                'date_naissance': '',
                'barreau_origine': '',
                'specialisations': '',
                'domaines_competences': '',
                'langues': '',
                'structure': '',
                'cabinet': '',
                'associes': '',
                'diplomes': '',
                'formations': '',
                'publications': '',
                'distinctions': '',
                'description_complete': '',
                'biographie': '',
                'activites_extra_prof': '',
                'coordonnees_completes': '',
                'horaires': '',
                'consultations': '',
                'tarifs': '',
                'notes_diverses': ''
            }
            
            # Contenu de la page
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source
            
            # 1. NOM COMPLET ET CIVILITÉ
            name_selectors = [
                "//h1[@class='entry-title']",
                "//h1",
                "//h2",
                "//title"
            ]
            
            for selector in name_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        name_text = element.text.strip()
                        if (len(name_text.split()) >= 2 and 
                            not any(word in name_text.lower() for word in ['domaine', 'compétence', 'contact', 'retour']) and
                            len(name_text) < 50):
                            
                            # Détecter civilité/titre
                            if name_text.startswith('M.'):
                                lawyer_data['civilite'] = 'M.'
                                name_text = name_text[2:].strip()
                            elif name_text.startswith('Mme'):
                                lawyer_data['civilite'] = 'Mme'
                                name_text = name_text[3:].strip()
                            elif name_text.startswith('Maître'):
                                lawyer_data['titre'] = 'Maître'
                                name_text = name_text[6:].strip()
                            elif name_text.startswith('Me'):
                                lawyer_data['titre'] = 'Me'
                                name_text = name_text[2:].strip()
                            
                            lawyer_data['nom_complet'] = name_text.upper()
                            name_parts = name_text.upper().split()
                            if len(name_parts) >= 2:
                                lawyer_data['nom'] = name_parts[0]
                                lawyer_data['prenom'] = ' '.join(name_parts[1:])
                            break
                    if lawyer_data['nom_complet']:
                        break
                except:
                    continue
            
            # Fallback nom depuis URL
            if not lawyer_data['nom_complet']:
                url_name = lawyer_url.split('/')[-2].replace('-', ' ').upper()
                if len(url_name.split()) >= 2:
                    lawyer_data['nom_complet'] = url_name
                    name_parts = url_name.split()
                    lawyer_data['nom'] = name_parts[0]
                    lawyer_data['prenom'] = ' '.join(name_parts[1:])
            
            # 2. EMAIL - Recherche exhaustive
            # Liens mailto
            try:
                email_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'mailto:')]")
                for link in email_links:
                    href = link.get_attribute('href')
                    if href and 'mailto:' in href:
                        email = href.replace('mailto:', '').strip()
                        # Nettoyer l'email
                        email = re.sub(r'^.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*$', r'\1', email)
                        if '@' in email and '.' in email:
                            lawyer_data['email'] = email
                            break
            except:
                pass
            
            # Regex email dans le texte
            if not lawyer_data['email']:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, page_text)
                if emails:
                    lawyer_data['email'] = emails[0]
                else:
                    emails = re.findall(email_pattern, page_source)
                    if emails:
                        lawyer_data['email'] = emails[0]
            
            # 3. TÉLÉPHONE ET FAX
            # Téléphone
            phone_patterns = [
                r'Tél\.?\s*:?\s*([0-9\s\.-]{10,})',
                r'Téléphone\s*:?\s*([0-9\s\.-]{10,})',
                r'Tel\s*:?\s*([0-9\s\.-]{10,})',
                r'\b(?:0[1-9])(?:[\s.-]?\d{2}){4}\b'
            ]
            
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    phone = match.strip() if isinstance(match, str) else match[0].strip()
                    if len(phone) >= 10 and not lawyer_data['telephone']:
                        lawyer_data['telephone'] = phone
                        break
                if lawyer_data['telephone']:
                    break
            
            # Fax
            fax_patterns = [
                r'Fax\s*:?\s*([0-9\s\.-]{10,})',
                r'Télécopie\s*:?\s*([0-9\s\.-]{10,})'
            ]
            
            for pattern in fax_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    fax = match.strip() if isinstance(match, str) else match[0].strip()
                    if len(fax) >= 10:
                        lawyer_data['fax'] = fax
                        break
                if lawyer_data['fax']:
                    break
            
            # 4. ADRESSE COMPLÈTE
            address_patterns = [
                r'([^.\n]*(?:41000|BLOIS)[^.\n]*)',
                r'([^.\n]*(?:rue|avenue|place|boulevard)[^.\n]*(?:41000|BLOIS)[^.\n]*)',
                r'([^.\n]*\d+[^.\n]*(?:rue|avenue|place|boulevard)[^.\n]*)',
                r'Adresse\s*:?\s*([^.\n]+(?:\n[^.\n]+)*?)(?=\n[A-Z]|\n$|Tél|Email)'
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    address = match.strip()
                    if 10 < len(address) < 300 and not lawyer_data['adresse_complete']:
                        lawyer_data['adresse_complete'] = address
                        
                        # Extraire code postal et ville
                        cp_match = re.search(r'(41\d{3})', address)
                        if cp_match:
                            lawyer_data['code_postal'] = cp_match.group(1)
                        
                        if 'BLOIS' in address.upper():
                            lawyer_data['ville'] = 'BLOIS'
                        elif 'blois' in address.lower():
                            lawyer_data['ville'] = 'Blois'
                        
                        # Diviser l'adresse en lignes
                        address_lines = [line.strip() for line in address.split('\n') if line.strip()]
                        if len(address_lines) >= 1:
                            lawyer_data['adresse_ligne1'] = address_lines[0]
                        if len(address_lines) >= 2:
                            lawyer_data['adresse_ligne2'] = address_lines[1]
                        
                        break
                if lawyer_data['adresse_complete']:
                    break
            
            # 5. SITE WEB
            web_patterns = [
                r'Site\s*:?\s*(www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
                r'Web\s*:?\s*(www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
                r'(www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
                r'https?://(www\.[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
                r'https?://([A-Za-z0-9.-]+\.[A-Za-z]{2,})'
            ]
            
            for pattern in web_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    lawyer_data['site_web'] = matches[0]
                    break
            
            # 6. DATE DE SERMENT ET INSCRIPTION
            serment_patterns = [
                r'(?:Serment|Date de serment|Prestation de serment)\s*:?\s*([0-9/.-]+)',
                r'Inscrit(?:e)?\s*(?:au barreau)?\s*(?:depuis|en|le)?\s*([0-9/.-]+)',
                r'([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
                r'(\d{4})'  # Année seule
            ]
            
            for pattern in serment_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    date_serment = match.strip()
                    if len(date_serment) >= 4:
                        if '/' in date_serment and len(date_serment) >= 8:
                            lawyer_data['date_serment'] = date_serment
                        
                        # Extraire l'année
                        year_match = re.search(r'([12]\d{3})', date_serment)
                        if year_match:
                            year = int(year_match.group(1))
                            if 1950 <= year <= 2024 and not lawyer_data['annee_inscription']:
                                lawyer_data['annee_inscription'] = str(year)
                        break
                if lawyer_data['date_serment'] or lawyer_data['annee_inscription']:
                    break
            
            # 7. BARREAU D'ORIGINE
            barreau_patterns = [
                r'Barreau\s*(?:d\'origine|de)\s*:?\s*([^.\n]+)',
                r'Inscrit(?:e)?\s*au\s*(?:barreau\s*(?:de|du))?\s*([A-Z][^.\n]+)'
            ]
            
            for pattern in barreau_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    barreau = match.strip()
                    if len(barreau) > 3 and len(barreau) < 50:
                        lawyer_data['barreau_origine'] = barreau
                        break
                if lawyer_data['barreau_origine']:
                    break
            
            # 8. SPÉCIALISATIONS ET DOMAINES DE COMPÉTENCES
            specializations = []
            
            # Chercher section "Domaines de compétences"
            competence_patterns = [
                r'Domaines?\s*de\s*compétences?\s*:?\s*\n([^A-Z\n]*(?:\n[^A-Z\n]*)*)',
                r'Spécialisations?\s*:?\s*\n([^A-Z\n]*(?:\n[^A-Z\n]*)*)',
                r'Domaines?\s*d\'intervention\s*:?\s*\n([^A-Z\n]*(?:\n[^A-Z\n]*)*)'
            ]
            
            for pattern in competence_patterns:
                matches = re.findall(pattern, page_text, re.MULTILINE)
                for match in matches:
                    competence_text = match.strip()
                    if competence_text and competence_text != "A renseigner" and len(competence_text) > 5:
                        specializations.append(competence_text)
            
            # Domaines de droit spécifiques
            droit_patterns = [
                r'([Dd]roit\s+[^.,:;\n]*?)(?:[.,:;\n]|$)',
                r'([Cc]ommercial[^.,:;\n]*?)(?:[.,:;\n]|$)',
                r'([Ff]amille[^.,:;\n]*?)(?:[.,:;\n]|$)',
                r'([Pp]énal[^.,:;\n]*?)(?:[.,:;\n]|$)',
                r'([Ii]mmobilier[^.,:;\n]*?)(?:[.,:;\n]|$)',
                r'([Tt]ravail[^.,:;\n]*?)(?:[.,:;\n]|$)'
            ]
            
            for pattern in droit_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    clean_match = match.strip()
                    if len(clean_match) > 5 and len(clean_match) < 100 and clean_match not in specializations:
                        specializations.append(clean_match)
            
            if specializations:
                lawyer_data['specialisations'] = '; '.join(specializations)
                lawyer_data['domaines_competences'] = lawyer_data['specialisations']
            
            # 9. LANGUES
            langue_patterns = [
                r'Langues?\s*:?\s*([^.\n]+)',
                r'Parle\s*:?\s*([^.\n]+)',
                r'(?:Anglais|Espagnol|Italien|Allemand|Portugais)[^.\n]*'
            ]
            
            for pattern in langue_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    langue = match.strip()
                    if len(langue) > 3 and len(langue) < 100:
                        lawyer_data['langues'] = langue
                        break
                if lawyer_data['langues']:
                    break
            
            # 10. STRUCTURE ET CABINET
            cabinet_patterns = [
                r'Cabinet\s*:?\s*([^.\n]+)',
                r'Structure\s*:?\s*([^.\n]+)',
                r'Société\s*:?\s*([^.\n]+)',
                r'SELARL\s*([^.\n]+)',
                r'SCP\s*([^.\n]+)'
            ]
            
            for pattern in cabinet_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    cabinet = match.strip()
                    if len(cabinet) > 3 and len(cabinet) < 100:
                        lawyer_data['cabinet'] = cabinet
                        lawyer_data['structure'] = cabinet
                        break
                if lawyer_data['cabinet']:
                    break
            
            # 11. DIPLÔMES ET FORMATIONS
            diplome_patterns = [
                r'Diplômes?\s*:?\s*([^.\n]+(?:\n[^A-Z\n]+)*)',
                r'Formation\s*:?\s*([^.\n]+(?:\n[^A-Z\n]+)*)',
                r'Études\s*:?\s*([^.\n]+(?:\n[^A-Z\n]+)*)',
                r'(?:DEA|DESS|Master|Doctorat)[^.\n]*'
            ]
            
            diplomes = []
            for pattern in diplome_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    diplome = match.strip()
                    if len(diplome) > 10 and diplome not in diplomes:
                        diplomes.append(diplome)
            
            if diplomes:
                lawyer_data['diplomes'] = '; '.join(diplomes)
                lawyer_data['formations'] = lawyer_data['diplomes']
            
            # 12. HORAIRES ET CONSULTATIONS
            horaire_patterns = [
                r'Horaires?\s*:?\s*([^.\n]+(?:\n[^A-Z\n]+)*)',
                r'Ouvert\s*:?\s*([^.\n]+)',
                r'Consultation\s*:?\s*([^.\n]+)',
                r'Rendez-vous\s*:?\s*([^.\n]+)'
            ]
            
            for pattern in horaire_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    horaire = match.strip()
                    if len(horaire) > 5 and len(horaire) < 200:
                        lawyer_data['horaires'] = horaire
                        lawyer_data['consultations'] = horaire
                        break
                if lawyer_data['horaires']:
                    break
            
            # 13. DESCRIPTION COMPLÈTE
            # Extraire tout le contenu pertinent
            content_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            relevant_lines = []
            
            for line in content_lines:
                if (20 < len(line) < 300 and 
                    not any(skip in line.lower() for skip in [
                        'retour', 'domaines de compétences', 'a renseigner',
                        'coordonnées', 'contact', 'mentions légales'
                    ])):
                    relevant_lines.append(line)
            
            if relevant_lines:
                lawyer_data['description_complete'] = ' '.join(relevant_lines[:5])[:500]
                lawyer_data['biographie'] = lawyer_data['description_complete']
            
            # 14. COORDONNÉES COMPLÈTES (pour backup)
            coordonnees_parts = []
            if lawyer_data['adresse_complete']:
                coordonnees_parts.append(f"Adresse: {lawyer_data['adresse_complete']}")
            if lawyer_data['telephone']:
                coordonnees_parts.append(f"Tél: {lawyer_data['telephone']}")
            if lawyer_data['fax']:
                coordonnees_parts.append(f"Fax: {lawyer_data['fax']}")
            if lawyer_data['email']:
                coordonnees_parts.append(f"Email: {lawyer_data['email']}")
            if lawyer_data['site_web']:
                coordonnees_parts.append(f"Site: {lawyer_data['site_web']}")
            
            if coordonnees_parts:
                lawyer_data['coordonnees_completes'] = ' | '.join(coordonnees_parts)
            
            logger.info(f"✅ {lawyer_data['nom_complet']}: email={lawyer_data['email'][:30] if lawyer_data['email'] else 'N/A'}")
            return lawyer_data
            
        except Exception as e:
            logger.error(f"❌ Erreur pour {lawyer_url}: {e}")
            return None
    
    def save_complete_results(self):
        """Sauvegarde tous les résultats avec toutes les informations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON COMPLET
        json_file = f"blois_EXTRACTION_COMPLETE_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV COMPLET
        csv_file = f"blois_EXTRACTION_COMPLETE_{timestamp}.csv"
        if self.lawyers_data:
            # Obtenir tous les champs possibles
            all_fields = set()
            for lawyer in self.lawyers_data:
                all_fields.update(lawyer.keys())
            
            fieldnames = sorted(list(all_fields))
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # CSV RÉSUMÉ (principales infos)
        csv_resume_file = f"blois_RESUME_PRINCIPAL_{timestamp}.csv"
        if self.lawyers_data:
            main_fields = [
                'nom_complet', 'nom', 'prenom', 'civilite', 'titre',
                'email', 'telephone', 'fax', 'adresse_complete', 
                'ville', 'code_postal', 'site_web', 'annee_inscription',
                'specialisations', 'cabinet', 'langues'
            ]
            
            with open(csv_resume_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=main_fields)
                writer.writeheader()
                for lawyer in self.lawyers_data:
                    # Extraire seulement les champs principaux
                    resume_data = {field: lawyer.get(field, '') for field in main_fields}
                    writer.writerow(resume_data)
        
        # EMAILS AVEC NOMS
        emails_file = f"blois_EMAILS_AVEC_NOMS_{timestamp}.csv"
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write("nom_complet,email,telephone,specialisations\n")
            for lawyer in self.lawyers_data:
                if lawyer['email']:
                    f.write(f'"{lawyer["nom_complet"]}","{lawyer["email"]}","{lawyer["telephone"]}","{lawyer["specialisations"][:100]}"\n')
        
        # RAPPORT FINAL DÉTAILLÉ
        report_file = f"blois_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT FINAL EXTRACTION COMPLÈTE BLOIS ===\n\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"URL: {self.base_url}\n\n")
            
            f.write("=== STATISTIQUES GLOBALES ===\n")
            f.write(f"Avocats traités: {len(self.lawyers_data)}\n")
            f.write(f"Emails trouvés: {sum(1 for l in self.lawyers_data if l['email'])}\n")
            f.write(f"Téléphones: {sum(1 for l in self.lawyers_data if l['telephone'])}\n")
            f.write(f"Fax: {sum(1 for l in self.lawyers_data if l['fax'])}\n")
            f.write(f"Adresses: {sum(1 for l in self.lawyers_data if l['adresse_complete'])}\n")
            f.write(f"Sites web: {sum(1 for l in self.lawyers_data if l['site_web'])}\n")
            f.write(f"Années inscription: {sum(1 for l in self.lawyers_data if l['annee_inscription'])}\n")
            f.write(f"Spécialisations: {sum(1 for l in self.lawyers_data if l['specialisations'])}\n")
            f.write(f"Cabinets/Structures: {sum(1 for l in self.lawyers_data if l['cabinet'])}\n")
            f.write(f"Langues: {sum(1 for l in self.lawyers_data if l['langues'])}\n")
            f.write(f"Diplômes: {sum(1 for l in self.lawyers_data if l['diplomes'])}\n")
            
            f.write(f"\n=== FICHIERS GÉNÉRÉS ===\n")
            f.write(f"- {json_file} (JSON complet)\n")
            f.write(f"- {csv_file} (CSV complet toutes colonnes)\n")
            f.write(f"- {csv_resume_file} (CSV résumé principales infos)\n")
            f.write(f"- {emails_file} (Emails avec noms et infos)\n")
            
            f.write(f"\n=== AVOCATS AVEC EMAIL ===\n")
            with_email = [l for l in self.lawyers_data if l['email']]
            for i, lawyer in enumerate(with_email, 1):
                f.write(f"{i:3d}. {lawyer['nom_complet']} - {lawyer['email']}\n")
                if lawyer['specialisations']:
                    f.write(f"     Spécialisations: {lawyer['specialisations'][:80]}...\n")
            
            f.write(f"\n=== AVOCATS SANS EMAIL ===\n")
            no_email = [l for l in self.lawyers_data if not l['email']]
            for lawyer in no_email:
                f.write(f"- {lawyer['nom_complet']}")
                if lawyer['telephone']:
                    f.write(f" (Tél: {lawyer['telephone']})")
                f.write(f"\n")
        
        emails_found = sum(1 for l in self.lawyers_data if l['email'])
        return json_file, csv_file, csv_resume_file, emails_file, report_file, emails_found
    
    def run_complete_extraction(self):
        """Lance l'extraction complète de TOUTES les informations"""
        try:
            logger.info("=== DÉBUT EXTRACTION COMPLÈTE BLOIS - TOUTES INFOS ===")
            
            # Récupérer tous les liens d'avocats
            lawyer_links = self.get_all_lawyer_links()
            
            if len(lawyer_links) < 70:
                logger.warning(f"⚠️  Seulement {len(lawyer_links)} fiches trouvées")
            
            logger.info(f"🎯 DÉBUT EXTRACTION COMPLÈTE de {len(lawyer_links)} fiches")
            
            # Extraire chaque fiche avec TOUTES les infos
            for i, lawyer_url in enumerate(lawyer_links, 1):
                logger.info(f"📋 Fiche {i}/{len(lawyer_links)} - Extraction complète")
                
                lawyer_data = self.extract_lawyer_complete_details(lawyer_url)
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                
                # Sauvegarde partielle tous les 15
                if i % 15 == 0:
                    partial_file = f"blois_complet_partial_{i}_{datetime.now().strftime('%H%M%S')}.json"
                    with open(partial_file, 'w', encoding='utf-8') as f:
                        json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"💾 Sauvegarde partielle: {partial_file}")
                
                time.sleep(1)
            
            # Sauvegarde finale complète
            json_file, csv_file, csv_resume_file, emails_file, report_file, email_count = self.save_complete_results()
            
            logger.info("🎉 === EXTRACTION COMPLÈTE TERMINÉE ===")
            logger.info(f"📊 Avocats: {len(self.lawyers_data)}")
            logger.info(f"📧 Emails: {email_count}")
            
            print(f"\n🎉 EXTRACTION COMPLÈTE TERMINÉE !")
            print(f"📊 {len(self.lawyers_data)} avocats extraits avec TOUTES leurs infos")
            print(f"📧 {email_count} emails récupérés")
            print(f"\n📁 FICHIERS GÉNÉRÉS :")
            print(f"   📋 {csv_resume_file} (CSV principal)")
            print(f"   📧 {emails_file} (Emails avec noms/infos)")
            print(f"   📊 {json_file} (JSON complet)")
            print(f"   📄 {csv_file} (CSV toutes colonnes)")
            print(f"   📝 {report_file} (Rapport détaillé)")
            
            return len(self.lawyers_data), email_count
            
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return 0, 0
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = BloisScraperCompletToutesInfos(headless=True)
    scraper.run_complete_extraction()