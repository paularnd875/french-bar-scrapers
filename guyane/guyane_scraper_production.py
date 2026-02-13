#!/usr/bin/env python3
"""
Scraper de production pour le Barreau de Guyane
Version complète avec extraction avancée et navigation multi-pages
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class GuyaneBarScraperProduction:
    def __init__(self, headless=True, max_pages=None):
        """
        Initialise le scraper de production
        :param headless: Mode headless (sans fenêtre) par défaut
        :param max_pages: Limite du nombre de pages à traiter (None = toutes)
        """
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
            print("🔇 Mode headless activé (sans fenêtre)")
        
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ WebDriver Chrome initialisé")
        except Exception as e:
            print(f"❌ Erreur WebDriver: {e}")
            raise
        
        self.base_url = "https://www.avocats-barreau-guyane.com/annuaire-des-avocats.htm"
        self.lawyers_data = []
        self.current_page = 1
        self.max_pages_limit = max_pages
        self.total_lawyers_found = 0
        
    def accept_cookies(self):
        """Gestion des cookies"""
        try:
            time.sleep(3)
            cookie_selectors = [
                "//button[contains(text(), 'ACCEPTER')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(@id, 'accept')]"
            ]
            
            for selector in cookie_selectors:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    button.click()
                    print("✅ Cookies acceptés")
                    return True
                except TimeoutException:
                    continue
            
            return True
            
        except Exception as e:
            print(f"⚠️ Cookies: {e}")
            return True
    
    def detect_pagination_info(self):
        """Détecte les informations de pagination"""
        try:
            # Chercher les informations de pagination
            pagination_selectors = [
                ".pagination",
                ".pager", 
                ".page-nav",
                "[class*='pagination']",
                "[class*='pager']"
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination = self.driver.find_element(By.CSS_SELECTOR, selector)
                    pagination_text = pagination.text
                    
                    # Extraire les numéros de pages
                    page_numbers = re.findall(r'\\b(\\d+)\\b', pagination_text)
                    if page_numbers:
                        max_page = max(int(p) for p in page_numbers)
                        print(f"📄 Pagination détectée: {max_page} pages")
                        return max_page
                except:
                    continue
                    
            # Si pas de pagination claire, chercher les liens numériques
            page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'page=') or matches(text(), '^\\\\d+$')]")
            if page_links:
                pages = []
                for link in page_links:
                    try:
                        page_num = int(link.text.strip())
                        pages.append(page_num)
                    except:
                        continue
                
                if pages:
                    max_page = max(pages)
                    print(f"📄 {max_page} pages détectées via liens")
                    return max_page
            
            print("📄 Pagination non détectée, traitement page par page")
            return None
            
        except Exception as e:
            print(f"⚠️ Erreur pagination: {e}")
            return None
    
    def get_all_lawyers_from_page(self):
        """Extrait TOUS les avocats de la page courante"""
        lawyers = []
        
        try:
            print(f"📋 Traitement page {self.current_page}...")
            
            # Attendre le chargement
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "annuaireFicheMini")))
            
            # Récupérer toutes les fiches
            lawyer_cards = self.driver.find_elements(By.CLASS_NAME, "annuaireFicheMini")
            print(f"👥 {len(lawyer_cards)} avocats sur cette page")
            
            for i, card in enumerate(lawyer_cards):
                try:
                    lawyer_data = {}
                    
                    # Nom complet et URL
                    name_link = card.find_element(By.XPATH, ".//h4/a")
                    lawyer_data['nom_complet'] = name_link.text.strip()
                    lawyer_data['detail_url'] = name_link.get_attribute('href')
                    
                    # Détails séparés
                    try:
                        lawyer_data['civilite'] = card.find_element(By.CLASS_NAME, "anfiche_civ").text.strip()
                        lawyer_data['prenom'] = card.find_element(By.CLASS_NAME, "anfiche_prenom").text.strip()
                        lawyer_data['nom'] = card.find_element(By.CLASS_NAME, "anfiche_nom").text.strip()
                    except:
                        pass
                    
                    # Structure
                    try:
                        structure_elem = card.find_element(By.CLASS_NAME, "structure")
                        lawyer_data['structure'] = structure_elem.text.strip()
                    except:
                        lawyer_data['structure'] = "INDIVIDUEL"
                    
                    lawyer_data['page_origine'] = self.current_page
                    lawyers.append(lawyer_data)
                    
                except Exception as e:
                    print(f"❌ Erreur avocat {i+1}: {e}")
                    continue
            
            print(f"✅ {len(lawyers)} avocats extraits de la page {self.current_page}")
            return lawyers
            
        except Exception as e:
            print(f"❌ Erreur page {self.current_page}: {e}")
            return []
    
    def extract_enhanced_details(self, lawyer_data):
        """EXTRACTION CORRIGÉE avec les vrais sélecteurs HTML identifiés"""
        if not lawyer_data.get('detail_url'):
            return lawyer_data
        
        try:
            # Navigation vers la fiche
            self.driver.get(lawyer_data['detail_url'])
            time.sleep(3)
            
            # ========================
            # STRUCTURE/CABINET - VRAIS SÉLECTEURS
            # ========================
            try:
                # Le nom du cabinet est dans h4 sous .annuaireFicheHead
                cabinet_elem = self.driver.find_element(By.CSS_SELECTOR, ".annuaireFicheHead h4")
                if cabinet_elem:
                    cabinet_name = cabinet_elem.text.strip()
                    # Vérifier que ce n'est pas le nom de l'avocat lui-même
                    if cabinet_name and cabinet_name != lawyer_data.get('nom_complet', '').replace('Maître ', ''):
                        lawyer_data['structure'] = cabinet_name
                    else:
                        lawyer_data['structure'] = "INDIVIDUEL"
                else:
                    lawyer_data['structure'] = "INDIVIDUEL"
                    
            except NoSuchElementException:
                lawyer_data['structure'] = "INDIVIDUEL"
            
            # ========================
            # SPÉCIALISATIONS - VRAIS SÉLECTEURS
            # ========================
            try:
                # Les spécialisations sont dans .annuaireListeDomCmp li
                spec_elements = self.driver.find_elements(By.CSS_SELECTOR, ".annuaireListeDomCmp li")
                if spec_elements:
                    specs = []
                    for elem in spec_elements:
                        spec_text = elem.text.strip()
                        if spec_text:
                            specs.append(spec_text)
                    
                    if specs:
                        lawyer_data['specialisations'] = ' | '.join(specs)
                    else:
                        lawyer_data['specialisations'] = ""
                else:
                    lawyer_data['specialisations'] = ""
                        
            except NoSuchElementException:
                lawyer_data['specialisations'] = ""
            
            # ========================
            # CONTACT - VRAIS SÉLECTEURS  
            # ========================
            # Téléphone depuis .btnTel .valeur
            try:
                phone_elem = self.driver.find_element(By.CSS_SELECTOR, ".btnTel .valeur")
                if phone_elem:
                    lawyer_data['telephone'] = phone_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Fax depuis .btnFax .valeur  
            try:
                fax_elem = self.driver.find_element(By.CSS_SELECTOR, ".btnFax .valeur")
                if fax_elem:
                    lawyer_data['fax'] = fax_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Email depuis .annuaireFicheSite a[href^="mailto:"]
            try:
                email_elem = self.driver.find_element(By.CSS_SELECTOR, ".annuaireFicheSite a[href^='mailto:']")
                if email_elem:
                    lawyer_data['email'] = email_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Adresse depuis .annuaireBlocAdresse
            try:
                address_block = self.driver.find_element(By.CSS_SELECTOR, ".annuaireBlocAdresse")
                if address_block:
                    # Extraire l'adresse en analysant le texte du bloc
                    address_text = address_block.text
                    lines = [line.strip() for line in address_text.split('\n') if line.strip()]
                    
                    address_parts = []
                    for line in lines:
                        # Ignorer les lignes avec téléphone/fax/barreau
                        if not any(word in line.lower() for word in ['tél', 'fax', 'barreau']):
                            if line and len(line) > 3:  # Éviter les lignes très courtes
                                address_parts.append(line)
                    
                    if address_parts:
                        lawyer_data['adresse'] = ', '.join(address_parts[:2])  # Prendre les 2 premières parties
                        
            except NoSuchElementException:
                pass
            
            # ========================
            # INFORMATIONS COMPLÉMENTAIRES
            # ========================
            # Extraction nom/prénom CORRIGÉE pour noms composés multiples
            if lawyer_data.get('nom_complet'):
                nom_complet_clean = lawyer_data['nom_complet'].replace('Maître', '').strip()
                
                # Stratégie améliorée pour noms/prénoms composés
                if len(nom_complet_clean.split()) >= 2:
                    parts = nom_complet_clean.split()
                    
                    # Trouver le PREMIER mot en majuscules (début du nom de famille)
                    # Car les noms peuvent être composés (CHOW CHINE, EL ALLAOUI, etc.)
                    nom_start_index = -1
                    for i in range(len(parts)):
                        if parts[i].isupper() and len(parts[i]) > 1:
                            nom_start_index = i
                            break
                    
                    if nom_start_index > 0:
                        # Prénom = tout avant le premier mot en majuscules
                        lawyer_data['prenom'] = ' '.join(parts[:nom_start_index])
                        # Nom = tous les mots en majuscules qui suivent
                        lawyer_data['nom'] = ' '.join(parts[nom_start_index:])
                    else:
                        # Fallback: utiliser une heuristique basée sur les patterns courants
                        # Si contient des tirets ou des mots courts, c'est souvent un prénom composé
                        if any('-' in part or len(part) <= 3 for part in parts[:-1]):
                            # Prendre les 2 derniers mots comme nom si possible
                            if len(parts) >= 3:
                                lawyer_data['prenom'] = ' '.join(parts[:-2])
                                lawyer_data['nom'] = ' '.join(parts[-2:])
                            else:
                                lawyer_data['prenom'] = parts[0]
                                lawyer_data['nom'] = ' '.join(parts[1:])
                        else:
                            # Cas standard: dernier mot = nom
                            lawyer_data['prenom'] = ' '.join(parts[:-1])
                            lawyer_data['nom'] = parts[-1]
                    
                    lawyer_data['civilite'] = 'Maître'
            
            return lawyer_data
            
        except Exception as e:
            print(f"⚠️ Erreur détails {lawyer_data.get('nom_complet', 'Inconnu')}: {e}")
            return lawyer_data
    
    def extract_contact_info(self, lawyer_data, text):
        """Extraction des informations de contact"""
        try:
            # Email - pattern très permissif
            email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b'
            emails = re.findall(email_pattern, text, re.IGNORECASE)
            if emails:
                lawyer_data['email'] = emails[0]
            
            # Téléphone Guyane (594) - plusieurs formats
            phone_patterns = [
                r'\\b(?:0?594[.\\s]?)?(?:[0-9]{2}[.\\s]?){4}[0-9]\\b',  # Format 594.XX.XX.XX ou XX.XX.XX.XX
                r'\\b(?:\\+594|0594)[.\\s]?(?:[0-9]{2}[.\\s]?){3}[0-9]{2}\\b',  # +594.XX.XX.XX.XX
                r'\\b[0-9]{2}[.\\s][0-9]{2}[.\\s][0-9]{2}[.\\s][0-9]{2}\\b'  # XX.XX.XX.XX
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, text)
                if phones:
                    # Nettoyer le numéro
                    phone = phones[0].replace(' ', '.').replace('-', '.')
                    lawyer_data['telephone'] = phone
                    break
            
            # Fax
            fax_pattern = r'(?:fax|télécopie)[:\\s]*([0-9.\\s]+)'
            fax_match = re.search(fax_pattern, text, re.IGNORECASE)
            if fax_match:
                lawyer_data['fax'] = fax_match.group(1).strip()
            
            # Adresse - Guyane (codes postaux 973xx)
            lines = text.split('\\n')
            address_parts = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                # Chercher ligne avec code postal Guyane
                if re.search(r'\\b973[0-9]{2}\\b', line):
                    # Prendre aussi la ligne précédente si elle contient des infos d'adresse
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if any(word in prev_line.lower() for word in ['route', 'rue', 'avenue', 'bd', 'boulevard', 'place', 'chemin']):
                            address_parts.append(prev_line)
                    
                    address_parts.append(line)
                    break
                
                # Ligne avec mots-clés d'adresse
                if any(word in line.lower() for word in ['route', 'rue', 'avenue', 'bd', 'boulevard', 'place', 'chemin']):
                    address_parts.append(line)
                    # Vérifier si la ligne suivante a le code postal
                    if i + 1 < len(lines) and re.search(r'\\b973[0-9]{2}\\b', lines[i+1]):
                        address_parts.append(lines[i+1].strip())
                        break
            
            if address_parts:
                lawyer_data['adresse'] = ', '.join(address_parts)
                
        except Exception as e:
            print(f"⚠️ Erreur extraction contact: {e}")
    
    def extract_professional_info(self, lawyer_data, text):
        """Extraction des informations professionnelles"""
        try:
            text_lower = text.lower()
            lines = [line.strip() for line in text.split('\\n') if line.strip()]
            
            # Année d'inscription - patterns multiples
            inscription_patterns = [
                r'inscrit[e]?.*?(?:en|depuis)\\s*(\\d{4})',
                r'barreau.*?(?:en|depuis)\\s*(\\d{4})',
                r'inscription.*?:?\\s*(\\d{4})',
                r'admis[e]?.*?(?:en|depuis)\\s*(\\d{4})'
            ]
            
            for pattern in inscription_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    year = match.group(1)
                    if 1980 <= int(year) <= 2025:
                        lawyer_data['annee_inscription'] = year
                        break
            
            # Barreau de rattachement
            if 'barreau' in text_lower:
                for line in lines:
                    if 'barreau' in line.lower() and 'guyane' in line.lower():
                        lawyer_data['barreau'] = line
                        break
            
            # Spécialisations - recherche plus large
            specialisation_keywords = ['spécialisation', 'spécialise', 'spécialisé', 'compétence', 'domaine', 'expertise', 'pratique']
            
            for keyword in specialisation_keywords:
                if keyword in text_lower:
                    for i, line in enumerate(lines):
                        if keyword in line.lower():
                            # Prendre les lignes suivantes qui semblent être des spécialisations
                            specialisations = []
                            
                            for j in range(i+1, min(i+5, len(lines))):
                                next_line = lines[j]
                                # Arrêter si on trouve des mots de fin
                                if any(stop_word in next_line.lower() 
                                      for stop_word in ['contact', 'adresse', 'téléphone', 'email', 'cabinet', 'structure']):
                                    break
                                    
                                # Si la ligne semble être une spécialisation
                                if next_line and len(next_line) > 5:
                                    specialisations.append(next_line)
                            
                            if specialisations:
                                lawyer_data['specialisations'] = ' | '.join(specialisations)
                                break
                    
                    if lawyer_data.get('specialisations'):
                        break
            
            # Langues parlées
            if any(lang_word in text_lower for lang_word in ['langue', 'anglais', 'espagnol', 'portugais', 'créole']):
                for line in lines:
                    if any(lang_word in line.lower() for lang_word in ['langue', 'anglais', 'espagnol', 'portugais', 'créole']):
                        lawyer_data['langues'] = line
                        break
                        
        except Exception as e:
            print(f"⚠️ Erreur extraction professionnelle: {e}")
    
    def navigate_to_next_page(self):
        """Navigation vers la page suivante"""
        try:
            # Stratégies multiples pour la pagination
            next_selectors = [
                f"//a[text()='{self.current_page + 1}']",
                "//a[contains(@class, 'next')]",
                "//a[contains(text(), 'Suivant')]",
                "//a[contains(text(), '>')]"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if next_button.is_displayed():
                        # Scroll vers le bouton
                        self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                        time.sleep(1)
                        
                        next_button.click()
                        self.current_page += 1
                        time.sleep(3)
                        
                        print(f"📄 Navigation réussie vers page {self.current_page}")
                        return True
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    print(f"⚠️ Erreur navigation {selector}: {e}")
                    continue
            
            print(f"📄 Fin de pagination (pas de page {self.current_page + 1})")
            return False
            
        except Exception as e:
            print(f"❌ Erreur navigation générale: {e}")
            return False
    
    def run_full_extraction(self):
        """Lance l'extraction complète de tous les avocats"""
        try:
            print("🚀 SCRAPER GUYANE - MODE PRODUCTION")
            print("="*60)
            print(f"📍 URL de base: {self.base_url}")
            print(f"🔄 Limite pages: {self.max_pages_limit or 'Toutes'}")
            
            start_time = datetime.now()
            
            # Page initiale
            self.driver.get(self.base_url)
            time.sleep(5)
            
            # Cookies
            self.accept_cookies()
            
            # Détecter pagination
            max_pages_detected = self.detect_pagination_info()
            
            # Boucle principale de traitement
            while True:
                # Vérifier limite
                if self.max_pages_limit and self.current_page > self.max_pages_limit:
                    print(f"🛑 Limite de {self.max_pages_limit} pages atteinte")
                    break
                
                # Extraire tous les avocats de la page
                page_lawyers = self.get_all_lawyers_from_page()
                
                if not page_lawyers:
                    print("❌ Aucun avocat trouvé, arrêt")
                    break
                
                self.total_lawyers_found += len(page_lawyers)
                
                # Traitement des détails
                print(f"🔍 Extraction détails de {len(page_lawyers)} avocats...")
                for i, lawyer in enumerate(page_lawyers):
                    if i % 10 == 0 and i > 0:
                        print(f"  📊 Progression: {i}/{len(page_lawyers)} avocats traités")
                    
                    detailed_lawyer = self.extract_enhanced_details(lawyer)
                    self.lawyers_data.append(detailed_lawyer)
                    
                    # Pause courte entre extractions
                    time.sleep(1)
                
                print(f"✅ Page {self.current_page} terminée: {len(page_lawyers)} avocats")
                
                # Navigation vers page suivante
                if not self.navigate_to_next_page():
                    break
                
                # Retour à la page d'accueil pour navigation propre
                self.driver.get(self.base_url)
                time.sleep(2)
            
            # Fin du traitement
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\\n" + "="*60)
            print(f"✅ EXTRACTION TERMINÉE")
            print(f"📊 Total avocats: {len(self.lawyers_data)}")
            print(f"📄 Pages traitées: {self.current_page}")
            print(f"⏱️  Durée: {duration}")
            
            # Sauvegarde
            self.save_production_results()
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
        finally:
            try:
                self.driver.quit()
            except:
                pass
    
    def save_production_results(self):
        """Sauvegarde les résultats de production"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f"GUYANE_COMPLET_{len(self.lawyers_data)}_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV avec toutes les colonnes
        csv_file = f"GUYANE_COMPLET_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
        if self.lawyers_data:
            all_fields = set()
            for lawyer in self.lawyers_data:
                all_fields.update(lawyer.keys())
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # Fichier emails uniquement
        emails_file = f"GUYANE_EMAILS_SEULEMENT_{timestamp}.txt"
        emails = [lawyer.get('email') for lawyer in self.lawyers_data if lawyer.get('email')]
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write(f"EMAILS AVOCATS BARREAU DE GUYANE\\n")
            f.write(f"Extraction du {datetime.now().strftime('%d/%m/%Y %H:%M')}\\n")
            f.write(f"Total: {len(emails)} emails sur {len(self.lawyers_data)} avocats\\n")
            f.write("="*50 + "\\n\\n")
            for email in emails:
                f.write(f"{email}\\n")
        
        # Rapport détaillé
        report_file = f"GUYANE_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            self.write_detailed_report(f)
        
        print(f"\\n📁 Fichiers générés:")
        print(f"   📄 {json_file} (données complètes)")
        print(f"   📊 {csv_file} (format tableur)")
        print(f"   📧 {emails_file} ({len(emails)} emails)")
        print(f"   📋 {report_file} (rapport détaillé)")
    
    def write_detailed_report(self, file_handle):
        """Écrit un rapport détaillé"""
        f = file_handle
        
        f.write("RAPPORT COMPLET - EXTRACTION BARREAU DE GUYANE\\n")
        f.write("="*70 + "\\n\\n")
        
        f.write(f"Date extraction: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\\n")
        f.write(f"URL source: {self.base_url}\\n")
        f.write(f"Pages traitées: {self.current_page}\\n")
        f.write(f"Total avocats: {len(self.lawyers_data)}\\n\\n")
        
        # Statistiques
        emails_count = len([l for l in self.lawyers_data if l.get('email')])
        phones_count = len([l for l in self.lawyers_data if l.get('telephone')])
        addresses_count = len([l for l in self.lawyers_data if l.get('adresse')])
        specializations_count = len([l for l in self.lawyers_data if l.get('specialisations')])
        
        f.write("STATISTIQUES:\\n")
        f.write("-" * 30 + "\\n")
        f.write(f"Avocats avec email: {emails_count} ({emails_count/len(self.lawyers_data)*100:.1f}%)\\n")
        f.write(f"Avocats avec téléphone: {phones_count} ({phones_count/len(self.lawyers_data)*100:.1f}%)\\n") 
        f.write(f"Avocats avec adresse: {addresses_count} ({addresses_count/len(self.lawyers_data)*100:.1f}%)\\n")
        f.write(f"Avocats avec spécialisations: {specializations_count} ({specializations_count/len(self.lawyers_data)*100:.1f}%)\\n\\n")
        
        # Liste des emails
        f.write("EMAILS EXTRAITS:\\n")
        f.write("-" * 30 + "\\n")
        emails = [l.get('email') for l in self.lawyers_data if l.get('email')]
        for email in sorted(emails):
            f.write(f"  • {email}\\n")
        f.write("\\n")
        
        # Aperçu par avocat (50 premiers)
        f.write("APERÇU AVOCATS (50 premiers):\\n") 
        f.write("-" * 30 + "\\n")
        for i, lawyer in enumerate(self.lawyers_data[:50], 1):
            f.write(f"\\n[{i}] {lawyer.get('nom_complet', 'N/A')}\\n")
            f.write(f"    Structure: {lawyer.get('structure', 'N/A')}\\n")
            f.write(f"    Email: {lawyer.get('email', 'Non trouvé')}\\n")
            f.write(f"    Téléphone: {lawyer.get('telephone', 'Non trouvé')}\\n")
            f.write(f"    Page: {lawyer.get('page_origine', 'N/A')}\\n")
        
        if len(self.lawyers_data) > 50:
            f.write(f"\\n... et {len(self.lawyers_data) - 50} autres avocats\\n")

if __name__ == "__main__":
    print("SCRAPER BARREAU DE GUYANE - VERSION PRODUCTION")
    print("="*50)
    
    # Configuration
    mode_headless = input("Mode sans fenêtre (headless) ? [O/n]: ").strip().lower()
    headless = mode_headless != 'n'
    
    max_pages_input = input("Limiter le nombre de pages ? (laissez vide pour toutes): ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else None
    
    # Lancement
    scraper = GuyaneBarScraperProduction(headless=headless, max_pages=max_pages)
    scraper.run_full_extraction()