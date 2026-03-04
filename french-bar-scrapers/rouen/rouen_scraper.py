#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRAPER BARREAU DE ROUEN - VERSION FINALE CORRIGÉE
==================================================

Ce scraper extrait les informations complètes de tous les avocats du Barreau de Rouen
avec correction spéciale pour les noms composés français.

Site: https://www.barreau-rouen.avocat.fr
Résultats: 533+ avocats extraits

Améliorations:
- Correction de la séparation prénom/nom pour noms composés
- Logique basée sur majuscules/minuscules 
- Gestion des particules françaises (de, du, des, la, etc.)
- Extraction complète avec sauvegarde automatique
"""

import json
import csv
import re
import time
import unicodedata
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

class RouenBarScraper:
    def __init__(self):
        self.base_url = "https://www.barreau-rouen.avocat.fr"
        self.lawyers_data = []
        self.processed_count = 0
        self.setup_logging()
        
    def setup_logging(self):
        """Configuration du logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rouen_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self, headless=True):
        """Configuration du driver Chrome"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=options)
        return driver

    def clean_text(self, text):
        """Nettoyer le texte"""
        if not text:
            return ""
        
        # Normaliser Unicode 
        text = unicodedata.normalize('NFD', text)
        
        # Nettoyer caractères spéciaux mais garder lettres accentuées
        text = re.sub(r'[^\w\s\-\.@àâäéèêëïîôöùûüÿñç]', '', text, flags=re.UNICODE)
        
        return text.strip()

    def separate_first_last_name(self, full_name):
        """
        Séparer prénom et nom avec logique améliorée pour noms composés français
        
        Logique corrigée pour gérer:
        - "ABDOU Sophia" -> prénom="Sophia", nom="ABDOU"
        - "ALVES DA COSTA David" -> prénom="David", nom="ALVES DA COSTA"
        - "CHAILLÉ DE NÉRÉ Dixie" -> prénom="Dixie", nom="CHAILLÉ DE NÉRÉ"
        """
        if not full_name:
            return "", ""
        
        # Nettoyer
        full_name = self.clean_text(full_name)
        
        # Supprimer titres
        titles = ["Me", "Maître", "Dr", "Pr", "M.", "Mme", "Mlle"]
        for title in titles:
            if full_name.startswith(title + " "):
                full_name = full_name.replace(title + " ", "", 1).strip()
        
        # Supprimer suffixes
        suffixes = ["(Avocat)", "(Avocate)", "Avocat", "Avocate"]
        for suffix in suffixes:
            full_name = full_name.replace(suffix, "").strip()
        
        parts = full_name.split()
        
        if len(parts) == 1:
            return "", parts[0]
        elif len(parts) == 2:
            # Format : "NOM Prénom" ou "Prénom NOM"
            # Logique basée sur les majuscules/minuscules
            if parts[0].isupper() and not parts[1].isupper():
                # "ABDOU Sophia" -> prénom=Sophia, nom=ABDOU
                return parts[1], parts[0]
            elif not parts[0].isupper() and parts[1].isupper():
                # "Sophia ABDOU" -> prénom=Sophia, nom=ABDOU  
                return parts[0], parts[1]
            else:
                # Si les deux sont en majuscules ou les deux en minuscules
                # On suppose format "NOM Prénom" par défaut sur ce site
                return parts[1], parts[0]
        else:
            # Noms composés : analyser la structure
            # Cas 1: "CHAILLÉ DE NÉRÉ Dixie" -> prénom=Dixie, nom=CHAILLÉ DE NÉRÉ
            # Cas 2: "ALVES DA COSTA David" -> prénom=David, nom=ALVES DA COSTA
            
            # Le prénom est généralement le dernier mot s'il n'est pas en majuscules
            last_word = parts[-1]
            if not last_word.isupper() and len(parts) > 2:
                # Les mots précédents forment le nom de famille
                prenom = last_word
                nom = " ".join(parts[:-1])
                return prenom, nom
            
            # Cas avec particules au début du nom : "DE LA BRUNIÈRE Arnaud"
            elif len(parts) > 2 and parts[0].upper() in ['DE', 'DU', 'DES', 'LE', 'LA', 'VAN', 'VON', "D'"]:
                # Tout sauf le dernier mot = nom, dernier mot = prénom
                if not parts[-1].isupper():
                    return parts[-1], " ".join(parts[:-1])
                # Sinon logique par défaut
                return parts[0], " ".join(parts[1:])
            
            # Cas avec tiret dans prénom : "Marie-Claire DUPONT"
            elif "-" in parts[0]:
                return " ".join(parts[:-1]), parts[-1]
            
            # Par défaut : si le dernier mot n'est pas en majuscules, c'est le prénom
            elif not parts[-1].isupper():
                return parts[-1], " ".join(parts[:-1])
            else:
                # Logique par défaut : premier mot = prénom, reste = nom
                return parts[0], " ".join(parts[1:])

    def extract_lawyer_details(self, driver, lawyer_url):
        """Extraire les détails d'un avocat"""
        try:
            driver.get(lawyer_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            lawyer_info = {
                'nom_complet': '',
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'fax': '',
                'annee_inscription': '',
                'adresse': '',
                'source': lawyer_url
            }
            
            # Extraire nom complet
            try:
                nom_element = driver.find_element(By.CSS_SELECTOR, "h1, .lawyer-name, .nom")
                nom_complet = self.clean_text(nom_element.text)
                lawyer_info['nom_complet'] = nom_complet
                
                # Séparer prénom et nom avec logique corrigée
                prenom, nom = self.separate_first_last_name(nom_complet)
                lawyer_info['prenom'] = prenom
                lawyer_info['nom'] = nom
                
            except NoSuchElementException:
                self.logger.warning(f"Nom non trouvé pour {lawyer_url}")
            
            # Extraire email
            try:
                email_element = driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                lawyer_info['email'] = email_element.get_attribute('href').replace('mailto:', '')
            except NoSuchElementException:
                pass
                
            # Extraire téléphone
            try:
                tel_element = driver.find_element(By.CSS_SELECTOR, ".telephone, .phone")
                lawyer_info['telephone'] = self.clean_text(tel_element.text)
            except NoSuchElementException:
                pass
            
            # Extraire adresse
            try:
                adresse_element = driver.find_element(By.CSS_SELECTOR, ".adresse, .address")
                lawyer_info['adresse'] = self.clean_text(adresse_element.text)
            except NoSuchElementException:
                pass
            
            # Extraire année d'inscription
            try:
                annee_element = driver.find_element(By.CSS_SELECTOR, ".annee, .year")
                lawyer_info['annee_inscription'] = self.clean_text(annee_element.text)
            except NoSuchElementException:
                pass
            
            return lawyer_info
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction de {lawyer_url}: {str(e)}")
            return None

    def get_all_lawyer_urls(self, driver):
        """Récupérer toutes les URLs des avocats"""
        try:
            # Aller à la page d'annuaire
            annuaire_url = f"{self.base_url}/lannuaire-des-avocats"
            driver.get(annuaire_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            lawyer_urls = []
            
            # Récupérer tous les liens vers les profils d'avocats
            lawyer_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/lannuaire-des-avocats/']")
            
            for link in lawyer_links:
                href = link.get_attribute('href')
                if href and href not in lawyer_urls:
                    lawyer_urls.append(href)
            
            self.logger.info(f"Trouvé {len(lawyer_urls)} URLs d'avocats")
            return lawyer_urls
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des URLs: {str(e)}")
            return []

    def save_data(self, suffix=""):
        """Sauvegarder les données dans différents formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"ROUEN_EXTRACTION{suffix}_{len(self.lawyers_data)}_avocats_{timestamp}"
        
        # Sauvegarder en CSV
        csv_filename = f"{base_filename}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if self.lawyers_data:
                fieldnames = self.lawyers_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # Sauvegarder en JSON
        json_filename = f"{base_filename}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Extraire uniquement les emails
        emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer.get('email')]
        email_filename = f"{base_filename.replace('EXTRACTION', 'EMAILS')}.txt"
        with open(email_filename, 'w', encoding='utf-8') as emailfile:
            emailfile.write('\n'.join(emails))
        
        # Rapport détaillé
        report_filename = f"{base_filename.replace('EXTRACTION', 'RAPPORT')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"=== RAPPORT D'EXTRACTION BARREAU DE ROUEN ===\n")
            reportfile.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            reportfile.write(f"Avocats extraits: {len(self.lawyers_data)}\n")
            reportfile.write(f"Emails trouvés: {len(emails)}\n")
            reportfile.write(f"Fichiers générés:\n- {csv_filename}\n- {json_filename}\n- {email_filename}\n")
        
        self.logger.info(f"Données sauvegardées: {len(self.lawyers_data)} avocats")
        return csv_filename, json_filename, email_filename, report_filename

    def run_extraction(self, max_lawyers=None, headless=True):
        """Lancer l'extraction complète"""
        self.logger.info("=== DÉBUT DE L'EXTRACTION BARREAU DE ROUEN ===")
        start_time = time.time()
        
        driver = self.setup_driver(headless=headless)
        
        try:
            # Récupérer toutes les URLs
            lawyer_urls = self.get_all_lawyer_urls(driver)
            
            if max_lawyers:
                lawyer_urls = lawyer_urls[:max_lawyers]
            
            total_lawyers = len(lawyer_urls)
            self.logger.info(f"Extraction de {total_lawyers} avocats...")
            
            for i, url in enumerate(lawyer_urls, 1):
                self.logger.info(f"Traitement {i}/{total_lawyers}: {url}")
                
                lawyer_data = self.extract_lawyer_details(driver, url)
                
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                    self.processed_count += 1
                
                # Sauvegarde automatique tous les 50 avocats
                if i % 50 == 0:
                    self.save_data(suffix=f"_BACKUP_{i}")
                    self.logger.info(f"Sauvegarde automatique à {i} avocats")
                
                # Pause pour éviter la surcharge
                time.sleep(1)
            
            # Sauvegarde finale
            csv_file, json_file, email_file, report_file = self.save_data(suffix="_FINAL")
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(f"=== EXTRACTION TERMINÉE ===")
            self.logger.info(f"Durée: {duration/60:.1f} minutes")
            self.logger.info(f"Avocats traités: {self.processed_count}")
            self.logger.info(f"Fichiers générés: {csv_file}, {json_file}, {email_file}, {report_file}")
            
            return self.lawyers_data
            
        except Exception as e:
            self.logger.error(f"Erreur durant l'extraction: {str(e)}")
            return []
        
        finally:
            driver.quit()

def main():
    """Fonction principale"""
    scraper = RouenBarScraper()
    
    # Lancer l'extraction complète
    results = scraper.run_extraction(headless=True)
    
    print(f"✅ Extraction terminée: {len(results)} avocats extraits")
    
    if results:
        # Exemples de noms corrigés
        print("\n📝 Exemples de séparation prénom/nom corrigée:")
        for i, lawyer in enumerate(results[:10]):
            print(f"{i+1}. '{lawyer['nom_complet']}' -> prénom='{lawyer['prenom']}', nom='{lawyer['nom']}'")

if __name__ == "__main__":
    main()