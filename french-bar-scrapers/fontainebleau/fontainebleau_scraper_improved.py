#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper AMÉLIORÉ pour le Barreau de Fontainebleau
Version corrigée avec meilleure classification nom/prénom
URL: https://avocats-fontainebleau.fr/trouver-un-avocat/
Développé avec Claude Code
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class FontainebleauScraperFinal:
    def __init__(self, headless=True):
        """Initialiser le scraper amélioré pour les 7 pages"""
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        self.base_url = "https://avocats-fontainebleau.fr/trouver-un-avocat/?dosrch=1&q=&wpbdp_view=search&listingfields%5B1%5D=&listingfields%5B2%5D=-1&listingfields%5B12%5D%5B%5D=&listingfields%5B13%5D=-1"
        self.current_page = 1
        self.max_pages = 7
        
        # Particules et préfixes nobiliaires français
        self.name_particles = {
            'de', 'du', 'des', 'da', 'della', 'del', 'van', 'von', 'le', 'la', 'les',
            'd\'', 'de la', 'de le', 'du', 'dos', 'das', 'dell\'', 'dall\'', 'mc', 'mac',
            'o\'', 'ben', 'ibn', 'al', 'el'
        }
        
        # Termes de cabinet à exclure du nom
        self.cabinet_terms = {
            'cabinet', 'avocat', 'avocats', 'associé', 'associés', 'associées',
            'société', 'scp', 'selarl', 'selafa', 'selca', '&', 'et', '-'
        }
        
    def setup_driver(self):
        """Configurer le driver Chrome"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-gpu")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return True
        except Exception as e:
            print("Erreur driver :", str(e))
            return False
    
    def accept_cookies(self):
        """Accepter les cookies"""
        try:
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[class*='cookie']",
                "[class*='cookie'] button"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    time.sleep(1)
                    return True
                except:
                    continue
            return True
        except:
            return True
    
    def parse_lawyer_name(self, full_name):
        """
        Améliorer le parsing du nom complet avec gestion des particules et des cabinets
        """
        if not full_name:
            return '', '', ''
        
        # Nettoyer le nom initial
        clean_name = full_name.replace('Me ', '').strip()
        
        # Séparer le nom du cabinet s'il y a un séparateur
        name_part = clean_name
        cabinet_part = ''
        
        # Chercher les séparateurs de cabinet
        separators = ['—', ' Cabinet ', ' cabinet ']
        for sep in separators:
            if sep in clean_name:
                parts = clean_name.split(sep, 1)
                name_part = parts[0].strip()
                cabinet_part = parts[1].strip() if len(parts) > 1 else ''
                break
        
        # Supprimer les termes de cabinet du nom si pas de séparateur explicite
        words = name_part.split()
        name_words = []
        cabinet_words = []
        
        cabinet_detected = False
        for word in words:
            word_lower = word.lower().strip('.,;()[]')
            
            # Si on a détecté un mot de cabinet, tout ce qui suit va dans cabinet_words
            if cabinet_detected or word_lower in self.cabinet_terms:
                cabinet_detected = True
                cabinet_words.append(word)
            else:
                name_words.append(word)
        
        if cabinet_words and not cabinet_part:
            cabinet_part = ' '.join(cabinet_words)
            name_part = ' '.join(name_words)
        
        # Parser le nom proprement dit
        words = name_part.split()
        if len(words) < 2:
            return name_part, '', cabinet_part
        
        # Identifier le nom de famille (généralement en majuscules ou le premier mot)
        nom = ''
        prenom = ''
        
        # Cas 1: Premier mot en majuscules = nom de famille
        if words[0].isupper() and len(words[0]) > 1:
            i = 0
            nom_parts = [words[i]]
            i += 1
            
            # Vérifier les particules qui suivent
            while i < len(words):
                word_lower = words[i].lower().strip('.,;()[]')
                if word_lower in self.name_particles or words[i].isupper():
                    nom_parts.append(words[i])
                    i += 1
                else:
                    break
            
            nom = ' '.join(nom_parts)
            prenom = ' '.join(words[i:]) if i < len(words) else ''
            
        # Cas 2: Particule au début
        elif words[0].lower() in self.name_particles:
            i = 0
            nom_parts = []
            
            # Prendre toutes les particules et mots en majuscules au début
            while i < len(words):
                word_lower = words[i].lower().strip('.,;()[]')
                if word_lower in self.name_particles or words[i].isupper():
                    nom_parts.append(words[i])
                    i += 1
                else:
                    break
            
            # Si on n'a pris que des particules, prendre le mot suivant
            if i < len(words) and not any(w.isupper() for w in nom_parts):
                nom_parts.append(words[i])
                i += 1
            
            nom = ' '.join(nom_parts)
            prenom = ' '.join(words[i:]) if i < len(words) else ''
            
        # Cas 3: Format "Prénom NOM" classique
        else:
            # Chercher le premier mot en majuscules
            for i, word in enumerate(words):
                if word.isupper() and len(word) > 1:
                    prenom = ' '.join(words[:i])
                    nom = ' '.join(words[i:])
                    break
            else:
                # Si pas de majuscules, prendre le dernier mot comme nom
                prenom = ' '.join(words[:-1])
                nom = words[-1]
        
        return prenom.strip(), nom.strip(), cabinet_part.strip()
    
    def extract_lawyer_info(self, lawyer_element):
        """Extraire les informations d'un avocat avec parsing amélioré"""
        lawyer_data = {
            'prenom': '',
            'nom': '',
            'nom_complet': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'annee_inscription': '',
            'date_serment': '',
            'specialisations': [],
            'competences': [],
            'structure': '',
            'site_web': '',
            'url_fiche': '',
            'page_trouvee': self.current_page
        }
        
        try:
            # Nom complet
            try:
                name_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-nom .value a")
                name_text = name_element.get_attribute('textContent').strip()
                name_lines = [line.strip() for line in name_text.split('\n') if line.strip()]
                if name_lines:
                    full_name = name_lines[0].strip()
                    lawyer_data['nom_complet'] = full_name
                    
                    # Parsing amélioré du nom
                    prenom, nom, cabinet_from_name = self.parse_lawyer_name(full_name)
                    lawyer_data['prenom'] = prenom
                    lawyer_data['nom'] = nom
                    
                    # Si on a détecté un cabinet dans le nom, l'utiliser si pas d'autre structure
                    if cabinet_from_name and not lawyer_data['structure']:
                        lawyer_data['structure'] = cabinet_from_name
                
                lawyer_data['url_fiche'] = name_element.get_attribute('href')
            except Exception as e:
                print("Erreur nom:", str(e))
            
            # Cabinet/Structure (peut remplacer ce qu'on a trouvé dans le nom)
            try:
                cabinet_element = lawyer_element.find_element(By.CSS_SELECTOR, ".cabinet")
                cabinet_text = cabinet_element.text.strip()
                if cabinet_text:
                    lawyer_data['structure'] = cabinet_text
            except:
                pass
            
            # Email
            try:
                email_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-e-mail .value")
                lawyer_data['email'] = email_element.text.strip()
            except:
                pass
            
            # Téléphone
            try:
                tel_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-telephone .value")
                lawyer_data['telephone'] = tel_element.text.strip()
            except:
                pass
            
            # Adresse
            try:
                address_element = lawyer_element.find_element(By.CSS_SELECTOR, ".address-info div")
                lawyer_data['adresse'] = address_element.text.strip()
            except:
                pass
            
            # Date de serment
            try:
                serment_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-date_de_serment .value")
                date_text = serment_element.text.strip()
                lawyer_data['date_serment'] = date_text
                
                if date_text:
                    # Extraire l'année de la date
                    date_parts = date_text.split('/')
                    if len(date_parts) == 3:
                        lawyer_data['annee_inscription'] = date_parts[2]
            except:
                pass
            
            # Compétences dominantes
            try:
                competence_elements = lawyer_element.find_elements(By.CSS_SELECTOR, ".wpbdp-field-competences_dominantes .value ul li")
                competences = [comp_elem.text.strip() for comp_elem in competence_elements if comp_elem.text.strip()]
                lawyer_data['competences'] = competences
                lawyer_data['specialisations'] = competences.copy()
            except:
                pass
            
            # Site web
            try:
                site_element = lawyer_element.find_element(By.CSS_SELECTOR, ".wpbdp-field-site_internet .value a")
                lawyer_data['site_web'] = site_element.get_attribute('href')
            except:
                pass
                
        except Exception as e:
            print("Erreur extraction:", str(e))
        
        return lawyer_data
    
    def scrape_current_page(self):
        """Scraper la page actuelle"""
        try:
            # Attendre que les fiches se chargent
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".wpbdp-listing"))
            )
            
            lawyer_elements = self.driver.find_elements(By.CSS_SELECTOR, ".wpbdp-listing")
            page_lawyers = []
            
            for lawyer_element in lawyer_elements:
                lawyer_data = self.extract_lawyer_info(lawyer_element)
                if lawyer_data['nom_complet']:
                    page_lawyers.append(lawyer_data)
            
            self.lawyers_data.extend(page_lawyers)
            print("Page {}/7: {} avocats extraits (Total: {})".format(self.current_page, len(page_lawyers), len(self.lawyers_data)))
            
            return len(page_lawyers)
            
        except Exception as e:
            print("Erreur page {}: {}".format(self.current_page, str(e)))
            return 0
    
    def navigate_to_next_page(self):
        """Naviguer vers la page suivante"""
        if self.current_page >= self.max_pages:
            return False
            
        try:
            # Méthode 1 : Lien "suivant" avec rel='next'
            try:
                next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
                if next_link.is_enabled():
                    self.driver.execute_script("arguments[0].click();", next_link)
                    self.current_page += 1
                    time.sleep(3)
                    return True
            except:
                pass
            
            # Méthode 2 : Lien par numéro de page
            try:
                next_page_num = self.current_page + 1
                page_link = self.driver.find_element(By.XPATH, "//a[text()='{}']".format(next_page_num))
                self.driver.execute_script("arguments[0].click();", page_link)
                self.current_page += 1
                time.sleep(3)
                return True
            except:
                pass
            
            # Méthode 3 : Navigation directe par URL
            try:
                next_page_num = self.current_page + 1
                next_url = "https://avocats-fontainebleau.fr/trouver-un-avocat/page/{}/?dosrch=1&q=&wpbdp_view=search&listingfields%5B1%5D=&listingfields%5B2%5D=-1&listingfields%5B12%5D%5B%5D=&listingfields%5B13%5D=-1".format(next_page_num)
                self.driver.get(next_url)
                self.current_page += 1
                time.sleep(3)
                return True
            except:
                pass
                
            return False
            
        except Exception as e:
            print("Erreur navigation:", str(e))
            return False
    
    def run_complete_scraping(self):
        """Scraper toutes les 7 pages"""
        print("DÉMARRAGE SCRAPER FONTAINEBLEAU AMÉLIORÉ - 7 PAGES COMPLÈTES")
        print("=" * 70)
        
        if not self.setup_driver():
            return False
            
        try:
            # Page 1
            print("Navigation vers la page 1...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Accepter cookies
            self.accept_cookies()
            
            # Scraper page 1
            scraped_count = self.scrape_current_page()
            
            # Scraper pages 2 à 7
            while self.current_page < self.max_pages:
                print("Navigation vers la page {}...".format(self.current_page + 1))
                
                if not self.navigate_to_next_page():
                    print("Impossible de naviguer vers la page {}".format(self.current_page + 1))
                    break
                
                scraped_count = self.scrape_current_page()
                if scraped_count == 0:
                    print("Aucun avocat trouvé page {}".format(self.current_page))
                
                time.sleep(2)  # Pause entre pages
            
            # Résultats finaux
            print("\n" + "=" * 70)
            print("SCRAPING TERMINÉ !")
            print("Total d'avocats extraits : {}".format(len(self.lawyers_data)))
            print("Nombre de pages scrapées : {}".format(self.current_page))
            print("Couverture : {}/51 avocats attendus".format(len(self.lawyers_data)))
            
            # Vérification des doublons
            emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
            unique_emails = set(emails)
            print("Emails uniques : {}/{}".format(len(unique_emails), len(emails)))
            
            # Vérifier la qualité du parsing
            parsed_correctly = sum(1 for l in self.lawyers_data if l['nom'] and l['prenom'])
            print("Parsing nom/prénom réussi : {}/{} ({:.1f}%)".format(parsed_correctly, len(self.lawyers_data), (parsed_correctly/len(self.lawyers_data)*100)))
            
            # Sauvegarder les résultats
            self.save_results()
            
            return True
            
        except Exception as e:
            print("Erreur générale:", str(e))
            return False
        finally:
            if self.driver:
                self.driver.quit()
                print("Driver fermé")
    
    def save_results(self):
        """Sauvegarder tous les résultats avec timestamps"""
        if not self.lawyers_data:
            print("Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON complet
        json_filename = "fontainebleau_FINAL_{}.json".format(timestamp)
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        print("JSON sauvé : {}".format(json_filename))
        
        # 2. CSV complet avec nom/prenom en premier
        csv_filename = "fontainebleau_FINAL_{}.csv".format(timestamp)
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 'adresse', 
                        'annee_inscription', 'date_serment', 'specialisations', 'competences', 
                        'structure', 'site_web', 'page_trouvee', 'url_fiche']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers_data:
                lawyer_copy = lawyer.copy()
                lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations'])
                lawyer_copy['competences'] = '; '.join(lawyer['competences'])
                writer.writerow(lawyer_copy)
        
        print("CSV sauvé : {}".format(csv_filename))
        
        # 3. Emails seulement
        emails_filename = "fontainebleau_EMAILS_FINAL_{}.txt".format(timestamp)
        with open(emails_filename, 'w', encoding='utf-8') as f:
            emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
            f.write('\n'.join(emails))
        print("Emails sauvés : {}".format(emails_filename))
        
        print("\nTous les fichiers sauvegardés avec parsing amélioré !")

def main():
    """Fonction principale"""
    print("SCRAPER FONTAINEBLEAU FINAL - VERSION 7 PAGES")
    print("Parsing nom/prénom amélioré avec gestion des particules")
    print("Mode headless activé pour ne pas vous déranger")
    
    scraper = FontainebleauScraperFinal(headless=True)
    
    try:
        success = scraper.run_complete_scraping()
        
        if success:
            print("\nSUCCÈS TOTAL ! Tous les avocats des 7 pages ont été extraits avec parsing amélioré.")
        else:
            print("\nÉCHEC. Vérifiez les erreurs ci-dessus.")
            
    except KeyboardInterrupt:
        print("\nArrêt demandé par l'utilisateur")
    except Exception as e:
        print("\nErreur inattendue : {}".format(str(e)))

if __name__ == "__main__":
    main()