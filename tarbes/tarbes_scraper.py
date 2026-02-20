#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau de Tarbes
Site web: https://www.avocats-tarbes.fr/annuaire/liste/tous/toutes/1

Ce script extrait toutes les informations des avocats du Barreau de Tarbes :
- Nom complet et séparé (prénom/nom)
- Année d'inscription et date de serment
- Spécialisations juridiques
- Structures d'exercice
- Coordonnées complètes
- URLs de vérification

Développé pour extraction complète avec gestion des structures d'exercice.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
import csv
import time
import re
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tarbes_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class TarbesScraper:
    def __init__(self, headless=True):
        self.base_url = "https://www.avocats-tarbes.fr/annuaire/liste/tous/toutes/"
        self.headless = headless
        self.driver = None
        self.lawyers = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def setup_driver(self):
        """Configuration du driver Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        logging.info("Driver Chrome configuré")

    def accept_cookies(self):
        """Accepter les cookies si nécessaire"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize"))
            )
            cookie_button.click()
            logging.info("Cookies personnalisés acceptés")
            time.sleep(2)
        except TimeoutException:
            try:
                cookie_accept = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "tarteaucitronAllDenied2"))
                )
                cookie_accept.click()
                logging.info("Tous les cookies refusés")
            except TimeoutException:
                logging.info("Pas de bannière de cookies trouvée")

    def parse_name(self, full_name):
        """Parse le nom complet pour séparer prénom et nom"""
        if not full_name:
            return "", "", full_name
            
        full_name = full_name.strip()
        parts = full_name.split()
        
        if len(parts) == 1:
            return "", parts[0], full_name
        elif len(parts) == 2:
            return parts[0], parts[1], full_name
        else:
            # Pour les noms composés, on prend le dernier mot comme nom
            # et tout le reste comme prénom
            first_name = " ".join(parts[:-1])
            last_name = parts[-1]
            return first_name, last_name, full_name

    def extract_specializations(self, soup):
        """Extrait les spécialisations juridiques"""
        specializations = []
        
        # Recherche des spécialisations après l'image macaron.png
        spans = soup.find_all('span', class_='label')
        for span in spans:
            img = span.find('img')
            if img and img.get('src') and 'macaron.png' in img.get('src'):
                # Texte après le span
                current = span.next_sibling
                while current:
                    if hasattr(current, 'strip'):
                        text = current.strip()
                        if text and text != "Spécialité":
                            specializations.append(text)
                            break
                    current = current.next_sibling
                    
        return specializations if specializations else ["Généraliste"]

    def extract_structure_exercice(self, soup):
        """Extrait les informations sur la structure d'exercice"""
        # Recherche des structures après l'image struc.png
        spans_with_img = soup.find_all('span', class_='label')
        
        for span in spans_with_img:
            img = span.find('img')
            if img and img.get('src') and 'struc.png' in img.get('src'):
                # Le contenu de la structure est dans les nœuds suivants
                current = span.next_sibling
                structure_content = []
                
                while current and len(structure_content) < 3:
                    if hasattr(current, 'strip'):
                        text = current.strip()
                        if text and text != "Structure d'exercice":
                            structure_content.append(text)
                    elif hasattr(current, 'get_text'):
                        text = current.get_text().strip()
                        if text and text != "Structure d'exercice":
                            structure_content.append(text)
                    current = current.next_sibling
                
                if structure_content:
                    return " ".join(structure_content)
        
        return "Exercice individuel"

    def extract_lawyer_info(self, lawyer_element, source_url):
        """Extrait toutes les informations d'un avocat"""
        try:
            soup = BeautifulSoup(lawyer_element.get_attribute('outerHTML'), 'html.parser')
            
            # Nom complet
            name_element = soup.find('h2')
            full_name = name_element.get_text().strip() if name_element else "Non spécifié"
            first_name, last_name, _ = self.parse_name(full_name)
            
            # Année d'inscription et serment
            inscription_year = None
            oath_date = None
            
            date_pattern = r'(\d{4})'
            date_text = soup.get_text()
            dates = re.findall(date_pattern, date_text)
            if dates:
                inscription_year = dates[0]
                oath_date = inscription_year
            
            # Spécialisations
            specializations = self.extract_specializations(soup)
            
            # Structure d'exercice
            structure = self.extract_structure_exercice(soup)
            
            # Coordonnées
            address_parts = []
            phone = "Non spécifié"
            email = "Non spécifié"
            
            # Extraction des coordonnées depuis le texte
            text_content = soup.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            # Recherche du téléphone
            for line in lines:
                if re.match(r'0[1-9][\s\d]{8,}', line.replace(' ', '')):
                    phone = line.strip()
                    break
            
            # Recherche de l'email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_content)
            if email_match:
                email = email_match.group()
            
            # Adresse (dernières lignes après le nom)
            for i, line in enumerate(lines):
                if full_name in line:
                    # Prendre les lignes suivantes pour l'adresse
                    potential_address = []
                    for addr_line in lines[i+1:]:
                        if not re.match(r'0[1-9][\s\d]{8,}', addr_line.replace(' ', '')) and '@' not in addr_line:
                            if not any(word in addr_line.lower() for word in ['spécialité', 'structure', 'inscription']):
                                potential_address.append(addr_line)
                        if len(potential_address) >= 3:
                            break
                    
                    if potential_address:
                        address_parts = potential_address[:2]  # Prendre les 2 premières lignes
                    break
            
            address = " ".join(address_parts) if address_parts else "Non spécifiée"
            
            lawyer_data = {
                'nom_complet': full_name,
                'prenom': first_name,
                'nom': last_name,
                'annee_inscription': inscription_year,
                'date_serment': oath_date,
                'specialisations': ', '.join(specializations),
                'structure_exercice': structure,
                'adresse': address,
                'telephone': phone,
                'email': email,
                'url_source': source_url
            }
            
            return lawyer_data
            
        except Exception as e:
            logging.error(f"Erreur extraction avocat: {e}")
            return None

    def scrape_page(self, page_num):
        """Scrape une page spécifique"""
        url = f"{self.base_url}{page_num}"
        logging.info(f"Scraping page {page_num}: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            if page_num == 1:
                self.accept_cookies()
            
            # Attendre que les avocats se chargent
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lawyer"))
            )
            
            lawyers_on_page = self.driver.find_elements(By.CLASS_NAME, "lawyer")
            logging.info(f"Trouvé {len(lawyers_on_page)} avocats sur la page {page_num}")
            
            page_lawyers = []
            for i, lawyer_element in enumerate(lawyers_on_page):
                try:
                    lawyer_data = self.extract_lawyer_info(lawyer_element, url)
                    if lawyer_data:
                        page_lawyers.append(lawyer_data)
                        logging.info(f"Page {page_num} - Avocat {i+1}: {lawyer_data['nom_complet']}")
                except Exception as e:
                    logging.error(f"Erreur avocat {i+1} page {page_num}: {e}")
            
            return page_lawyers
            
        except Exception as e:
            logging.error(f"Erreur scraping page {page_num}: {e}")
            return []

    def scrape_all(self, max_pages=10):
        """Scrape toutes les pages"""
        logging.info("Début du scraping complet Tarbes")
        
        self.setup_driver()
        all_lawyers = []
        
        try:
            for page in range(1, max_pages + 1):
                page_lawyers = self.scrape_page(page)
                if not page_lawyers:
                    logging.info(f"Pas d'avocats trouvés page {page}, arrêt")
                    break
                
                all_lawyers.extend(page_lawyers)
                
                # Backup intermédiaire
                if page % 3 == 0:
                    self.save_backup(all_lawyers, page)
                
                time.sleep(2)
            
            self.lawyers = all_lawyers
            logging.info(f"Scraping terminé: {len(self.lawyers)} avocats extraits")
            
        except Exception as e:
            logging.error(f"Erreur scraping général: {e}")
            self.lawyers = all_lawyers
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return self.lawyers

    def save_backup(self, lawyers, page_num):
        """Sauvegarde intermédiaire"""
        backup_file = f"TARBES_BACKUP_{len(lawyers)}_page{page_num}_{self.timestamp}.json"
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(lawyers, f, ensure_ascii=False, indent=2)
            logging.info(f"Backup sauvegardé: {backup_file}")
        except Exception as e:
            logging.error(f"Erreur backup: {e}")

    def save_results(self):
        """Sauvegarde les résultats finaux"""
        if not self.lawyers:
            logging.warning("Aucun avocat à sauvegarder")
            return
        
        timestamp = self.timestamp
        base_name = f"TARBES_COMPLET_{len(self.lawyers)}_avocats_{timestamp}"
        
        # CSV
        csv_file = f"{base_name}.csv"
        fieldnames = ['nom_complet', 'prenom', 'nom', 'annee_inscription', 'date_serment', 
                     'specialisations', 'structure_exercice', 'adresse', 'telephone', 'email', 'url_source']
        
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.lawyers)
            logging.info(f"CSV sauvegardé: {csv_file}")
        except Exception as e:
            logging.error(f"Erreur sauvegarde CSV: {e}")
        
        # JSON
        json_file = f"{base_name}.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
            logging.info(f"JSON sauvegardé: {json_file}")
        except Exception as e:
            logging.error(f"Erreur sauvegarde JSON: {e}")
        
        # Rapport
        self.generate_report(base_name)

    def generate_report(self, base_name):
        """Génère un rapport détaillé"""
        report_file = f"{base_name}_RAPPORT.txt"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("=== RAPPORT TARBES AVEC STRUCTURES D'EXERCICE ===\n")
                f.write(f"Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Site source: https://www.avocats-tarbes.fr/annuaire/\n")
                f.write(f"Total avocats extraits: {len(self.lawyers)}\n\n")
                
                # Statistiques qualité
                f.write("=== STATISTIQUES QUALITÉ DES DONNÉES ===\n")
                stats = self.calculate_stats()
                for stat, value in stats.items():
                    f.write(f"{stat}: {value}\n")
                f.write("\n")
                
                # Analyse des spécialisations
                self.write_specialization_analysis(f)
                
                # Analyse des structures
                self.write_structure_analysis(f)
                
                # Échantillon
                f.write("=== ÉCHANTILLON DES DONNÉES EXTRAITES ===\n")
                for i, lawyer in enumerate(self.lawyers[:10], 1):
                    f.write(f" {i}. {lawyer['nom_complet']}\n")
                    f.write(f"    Prénom: {lawyer['prenom']}\n")
                    f.write(f"    Nom: {lawyer['nom']}\n")
                    f.write(f"    Inscription: {lawyer['annee_inscription']}\n")
                    f.write(f"    Spécialisations: {lawyer['specialisations']}\n")
                    f.write(f"    ✨ Structure: {lawyer['structure_exercice']}\n")
                    f.write(f"    Téléphone: {lawyer['telephone']}\n")
                    f.write(f"    Adresse: {lawyer['adresse']}\n\n")
            
            logging.info(f"Rapport généré: {report_file}")
        except Exception as e:
            logging.error(f"Erreur génération rapport: {e}")

    def calculate_stats(self):
        """Calcule les statistiques de qualité"""
        total = len(self.lawyers)
        if total == 0:
            return {}
        
        stats = {
            "Avocats avec nom complet": total,
            "Avocats avec prénom/nom séparés": sum(1 for l in self.lawyers if l['prenom'] and l['nom']),
            f"Avocats avec année d'inscription": f"{sum(1 for l in self.lawyers if l['annee_inscription'])} ({sum(1 for l in self.lawyers if l['annee_inscription'])*100/total:.1f}%)",
            "Avocats avec date de serment": sum(1 for l in self.lawyers if l['date_serment']),
            f"Avocats avec adresse": f"{sum(1 for l in self.lawyers if l['adresse'] != 'Non spécifiée')} ({sum(1 for l in self.lawyers if l['adresse'] != 'Non spécifiée')*100/total:.1f}%)",
            f"Avocats avec téléphone": f"{sum(1 for l in self.lawyers if l['telephone'] != 'Non spécifié')} ({sum(1 for l in self.lawyers if l['telephone'] != 'Non spécifié')*100/total:.1f}%)",
            f"Avocats avec email": f"{sum(1 for l in self.lawyers if l['email'] != 'Non spécifié')} ({sum(1 for l in self.lawyers if l['email'] != 'Non spécifié')*100/total:.1f}%)",
            f"Avocats avec spécialisations": f"{sum(1 for l in self.lawyers if l['specialisations'] != 'Généraliste')} ({sum(1 for l in self.lawyers if l['specialisations'] != 'Généraliste')*100/total:.1f}%)",
            f"✨ Avocats avec structures": f"{sum(1 for l in self.lawyers if l['structure_exercice'] != 'Exercice individuel')} ({sum(1 for l in self.lawyers if l['structure_exercice'] != 'Exercice individuel')*100/total:.1f}%)"
        }
        return stats

    def write_specialization_analysis(self, f):
        """Analyse des spécialisations"""
        specializations = {}
        specialized_lawyers = []
        
        for lawyer in self.lawyers:
            specs = lawyer['specialisations']
            if specs != 'Généraliste':
                specialized_lawyers.append(lawyer)
                for spec in specs.split(', '):
                    specializations[spec] = specializations.get(spec, 0) + 1
        
        if specializations:
            f.write("=== ANALYSE DES SPÉCIALISATIONS JURIDIQUES ===\n")
            total_specs = sum(specializations.values())
            f.write(f"Nombre total de spécialisations trouvées: {total_specs}\n")
            f.write(f"Domaines juridiques distincts: {len(specializations)}\n\n")
            
            f.write("Répartition par domaine:\n")
            for spec, count in sorted(specializations.items(), key=lambda x: x[1], reverse=True):
                f.write(f"• {spec}: {count} avocat(s)\n")
            
            f.write("\n=== LISTE DES AVOCATS SPÉCIALISÉS ===\n")
            for lawyer in specialized_lawyers:
                f.write(f"• {lawyer['nom_complet']} ({lawyer['annee_inscription']}) - {lawyer['specialisations']}\n")
            f.write("\n")

    def write_structure_analysis(self, f):
        """Analyse des structures d'exercice"""
        structures = {}
        structure_types = {'SCP': 0, 'SELARL': 0, 'SARL': 0, 'Cabinet': 0}
        lawyers_with_structure = []
        
        for lawyer in self.lawyers:
            structure = lawyer['structure_exercice']
            if structure != 'Exercice individuel':
                lawyers_with_structure.append(lawyer)
                structures[structure] = structures.get(structure, 0) + 1
                
                # Catégorisation par type
                if 'SCP' in structure:
                    structure_types['SCP'] += 1
                elif 'SELARL' in structure:
                    structure_types['SELARL'] += 1
                elif 'SARL' in structure:
                    structure_types['SARL'] += 1
                elif 'Cabinet' in structure:
                    structure_types['Cabinet'] += 1
        
        if lawyers_with_structure:
            f.write("=== ANALYSE DES STRUCTURES D'EXERCICE ===\n")
            f.write(f"Nombre d'avocats avec structure: {len(lawyers_with_structure)}\n")
            f.write(f"Structures d'exercice distinctes: {len(structures)}\n\n")
            
            f.write("Types de structures:\n")
            for struct_type, count in structure_types.items():
                f.write(f"• {struct_type} (Société Civile Professionnelle): {count}\n" if struct_type == 'SCP' else
                       f"• {struct_type} (Société d'Exercice Libéral): {count}\n" if struct_type == 'SELARL' else
                       f"• {struct_type}: {count}\n")
            
            f.write("\n=== LISTE DES STRUCTURES D'EXERCICE ===\n")
            for lawyer in lawyers_with_structure:
                f.write(f"• {lawyer['nom_complet']} - {lawyer['structure_exercice']}\n")
            f.write("\n")

def main():
    """Fonction principale"""
    logging.info("Début du scraping Tarbes")
    
    scraper = TarbesScraper(headless=True)
    lawyers = scraper.scrape_all(max_pages=15)
    
    if lawyers:
        scraper.save_results()
        logging.info(f"Extraction terminée avec succès: {len(lawyers)} avocats")
    else:
        logging.error("Aucun avocat extrait")

if __name__ == "__main__":
    main()