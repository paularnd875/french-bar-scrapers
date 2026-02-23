#!/usr/bin/env python3
"""
SCRAPER OFFICIEL - BARREAU DE VANNES
====================================

Version finale et optimisée pour l'extraction complète des avocats du Barreau de Vannes
avec spécialisations juridiques correctement séparées des langues parlées.

Caractéristiques:
- Extraction de 152 avocats sur 19 pages
- Spécialisations juridiques individuelles correctement détectées
- Langues parlées séparées des spécialisations
- Sauvegarde automatique tous les 25 avocats
- Robuste avec gestion d'erreurs

Utilisation:
    python3 vannes_scraper_final.py

Fichiers générés:
- VANNES_FINAL_SPECIALISATIONS_VRAIMENT_CORRECTES_152_avocats_[timestamp].csv
- VANNES_FINAL_SPECIALISATIONS_VRAIMENT_CORRECTES_152_avocats_[timestamp].json
- VANNES_RAPPORT_SPECIALISATIONS_VRAIMENT_FINAL_[timestamp].txt

Auteur: Claude Code
Date: 2026-02-23
"""

import json
import csv
import re
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class VannesBarAssociationScraper:
    def __init__(self):
        self.setup_logging()
        self.setup_driver()
        self.lawyers_data = []
        self.lawyers_links = []
        self.processed_urls = set()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.logger.info("✅ Driver initialisé")
        
    def extract_specializations_and_languages(self, url):
        """
        Extraction correcte des spécialisations individuelles et des langues parlées
        
        Logique:
        1. Ignore les lignes 16-34 (formulaire de recherche générique)
        2. Cherche APRÈS ligne 60 pour les informations individuelles de l'avocat
        3. Détecte "Specialisation de l'avocat" pour les vraies spécialisations
        4. Détecte "Langues parlées" pour les langues
        5. Sépare complètement les deux types d'informations
        """
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = page_text.split('\n')
            
            # Trouver l'index où commencent les informations de l'avocat (après ligne 60)
            lawyer_start_index = -1
            for i, line in enumerate(lines):
                line_clean = line.strip()
                # Chercher le nom de l'avocat (format : "NOM Prénom" en majuscules)
                if re.match(r'^[A-Z][A-Z\s\-\']+\s+[A-Z][a-z]+.*$', line_clean) and len(line_clean) > 5:
                    # Vérifier que ce n'est pas dans la section navigation (lignes 0-60)
                    if i > 60:
                        lawyer_start_index = i
                        break
            
            specializations = []
            languages = []
            
            if lawyer_start_index > 0:
                # Chercher les spécialisations seulement APRÈS les informations de l'avocat
                post_lawyer_lines = lines[lawyer_start_index:]
                
                # Chercher le pattern "Specialisation de l'avocat" (avec ou sans 's')
                specialization_section = False
                languages_section = False
                
                for i, line in enumerate(post_lawyer_lines):
                    line_clean = line.strip()
                    
                    # Détecter la section spécialisations
                    if re.match(r'Specialis.*de l.avocat', line_clean, re.IGNORECASE):
                        specialization_section = True
                        languages_section = False
                        self.logger.info(f"  🎯 Section spé trouvée: {line_clean}")
                        continue
                        
                    # Détecter la section langues
                    if "Langues parlées" in line_clean:
                        languages_section = True
                        specialization_section = False
                        continue
                    
                    # Extraire les spécialisations
                    if specialization_section and line_clean:
                        # Vérifier que c'est une vraie spécialisation (pas un élément de navigation)
                        legal_specializations = [
                            'Droit immobilier', 'Droit pénal', 'Droit de la famille', 
                            'Droit commercial', 'Droit du travail', 'Droit civil',
                            'Droit des sociétés', 'Droit fiscal', 'Droit public',
                            'Droit de l\'environnement', 'Droit bancaire', 'Droit rural',
                            'Droit de la consommation', 'Droit international',
                            'Contentieux', 'Médiation'
                        ]
                        
                        # Vérifier si c'est une vraie spécialisation
                        if any(spec.lower() in line_clean.lower() for spec in legal_specializations):
                            if line_clean not in specializations:
                                specializations.append(line_clean)
                                self.logger.info(f"    ✅ Spé trouvée: {line_clean}")
                        
                        # Arrêter si on trouve autre chose que des spécialisations
                        elif line_clean in ['ORDRE DES L\'AVOCATS', 'RETOUR', 'LE BARREAU']:
                            specialization_section = False
                    
                    # Extraire les langues
                    if languages_section and line_clean:
                        language_candidates = [
                            'Anglais', 'Français', 'Allemand', 'Italien', 'Espagnol', 
                            'Portugais', 'Arabe', 'Chinois', 'Japonais', 'Russe', 
                            'Néerlandais', 'Roumain', 'Polonais'
                        ]
                        
                        if line_clean in language_candidates:
                            languages.append(line_clean)
                        elif line_clean and line_clean not in ['Cabinet', 'Plan', 'Satellite']:
                            # Arrêter si on trouve autre chose que des langues
                            languages_section = False
            
            # Retourner les résultats séparés
            specializations_str = ' | '.join(specializations) if specializations else ''
            languages_str = ' | '.join(languages) if languages else ''
            
            return specializations_str, languages_str
            
        except Exception as e:
            self.logger.error(f"Erreur extraction spécialisations: {e}")
            return '', ''
    
    def extract_lawyer_details(self, url, name):
        """Extraction des détails d'un avocat avec spécialisations correctement séparées"""
        try:
            self.logger.info(f"🔍 Extraction: {name}")
            
            self.driver.get(url)
            time.sleep(2)
            
            # Accepter cookies si nécessaire
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2"))
                )
                cookie_button.click()
                time.sleep(1)
            except:
                pass
                
            # Données de base
            lawyer_data = {
                'nom_complet': name,
                'prenom': '',
                'nom': '',
                'annee_inscription': '',
                'specialisations': '',
                'langues_parlees': '',
                'structure': '',
                'adresse': '',
                'telephone': '',
                'email': '',
                'site_web': '',
                'source': url
            }
            
            # Parsing du nom avec particules françaises
            name_parts = name.strip().split()
            particules = ['DE', 'DU', 'DES', 'LE', 'LA', 'LES', 'VON', 'VAN', "D'", "L'"]
            
            if len(name_parts) >= 2:
                if len(name_parts) >= 3 and name_parts[0].upper() in particules:
                    lawyer_data['nom'] = ' '.join(name_parts[:-1])
                    lawyer_data['prenom'] = name_parts[-1]
                else:
                    lawyer_data['nom'] = name_parts[0]
                    lawyer_data['prenom'] = ' '.join(name_parts[1:])
            else:
                lawyer_data['nom'] = name
                lawyer_data['prenom'] = ''
            
            # **EXTRACTION CORRECTE DES SPÉCIALISATIONS ET LANGUES**
            specs, langs = self.extract_specializations_and_languages(url)
            lawyer_data['specialisations'] = specs
            lawyer_data['langues_parlees'] = langs
            
            # Log du résultat pour suivi
            if specs and langs:
                self.logger.info(f"  ✅ Spé: {specs} | Langues: {langs}")
            elif specs:
                self.logger.info(f"  ✅ Spé: {specs} | Pas de langues")
            elif langs:
                self.logger.info(f"  ✅ Pas de spé | Langues: {langs}")
            else:
                self.logger.info(f"  ✅ Pas de spé | Pas de langues")
            
            # Extraction des autres données (email, téléphone, etc.)
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Email
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_text)
            if email_match:
                lawyer_data['email'] = email_match.group()
            
            # Téléphone français
            phone_patterns = [
                r'(\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2})',
                r'(\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2})',
                r'(0[1-9](?:[\s\.]?\d{2}){4})',
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, page_text)
                if phone_match:
                    lawyer_data['telephone'] = phone_match.group()
                    break
            
            # Année d'inscription au barreau
            year_match = re.search(r'(?:serment|inscription).*?([12]\d{3})', page_text, re.IGNORECASE)
            if year_match:
                year = int(year_match.group(1))
                if 1950 <= year <= 2030:
                    lawyer_data['annee_inscription'] = str(year)
            
            # Structure/Cabinet juridique
            lines = page_text.split('\n')
            for line in lines:
                line = line.strip()
                structure_keywords = ['selarl', 'scp', 'cabinet', 'selas', 'société', 'libéral', 'avocat']
                if (any(word in line.lower() for word in structure_keywords) and 
                    len(line) > 10 and len(line) < 100 and 
                    'cabinet' in line.lower()):
                    lawyer_data['structure'] = line
                    break
            
            # Adresse
            address_lines = []
            for line in lines:
                line = line.strip()
                if (re.match(r'.*\d{5}.*', line) or 
                    re.match(r'.*[Rr]ue.*\d+.*', line) or
                    re.match(r'.*[Aa]venue.*\d+.*', line) or
                    re.match(r'.*[Bb]oulevard.*\d+.*', line)):
                    if len(line) > 10 and len(line) < 100:
                        address_lines.append(line)
            
            if address_lines:
                lawyer_data['adresse'] = address_lines[0]
            
            self.lawyers_data.append(lawyer_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur extraction {name}: {e}")
            return False
    
    def collect_all_lawyer_links(self):
        """Collecter tous les liens d'avocats depuis toutes les pages (19→1)"""
        self.logger.info("🔍 PHASE 1: COLLECTE DE TOUS LES LIENS D'AVOCATS")
        self.logger.info("--" * 25)
        
        all_links = []
        
        # Parcourir les pages de 19 à 1 (pagination inverse pour optimisation)
        for page_num in range(19, 0, -1):
            if page_num == 1:
                url = "https://www.avocats-vannes.com/le-barreau-de-vannes/annuaire-des-avocats/tous-les-avocats/"
            else:
                url = f"https://www.avocats-vannes.com/le-barreau-de-vannes/annuaire-des-avocats/rech-page-{page_num}.html"
            
            self.logger.info(f"📖 COLLECTE LIENS PAGE {page_num}: {url}")
            
            try:
                self.driver.get(url)
                time.sleep(2)
                
                # Gérer les cookies si présents
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.ID, "tarteaucitronPersonalize2"))
                    )
                    cookie_button.click()
                    self.logger.info("🍪 Cookies acceptés")
                    time.sleep(1)
                except:
                    self.logger.info("🍪 Pas de cookies")
                
                # Trouver tous les liens d'avocats sur la page
                lawyer_elements = self.driver.find_elements(By.CSS_SELECTOR, ".short_product")
                self.logger.info(f"🔍 {len(lawyer_elements)} éléments .short_product trouvés")
                
                page_links = []
                for i, element in enumerate(lawyer_elements):
                    try:
                        # Extraire le lien et le nom
                        link_element = element.find_element(By.TAG_NAME, "a")
                        link_url = link_element.get_attribute("href")
                        
                        name_element = element.find_element(By.CSS_SELECTOR, ".short_product h3")
                        lawyer_name = name_element.text.strip()
                        
                        if link_url and lawyer_name:
                            page_links.append((link_url, lawyer_name))
                            all_links.append((link_url, lawyer_name))
                            self.logger.info(f"   {i+1}. 📝 {lawyer_name} -> {link_url}")
                        
                    except Exception as e:
                        self.logger.error(f"Erreur élément {i}: {e}")
                        continue
                
                self.logger.info(f"✅ PAGE {page_num}: {len(page_links)} liens collectés")
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Erreur page {page_num}: {e}")
                continue
        
        self.lawyers_links = all_links
        self.logger.info(f"📊 TOTAL LIENS COLLECTÉS: {len(all_links)}")
        return all_links
    
    def process_all_lawyers(self):
        """Traiter tous les avocats avec extraction détaillée"""
        self.logger.info("🔍 PHASE 2: EXTRACTION DÉTAILLÉE DE TOUS LES AVOCATS")
        self.logger.info("--" * 30)
        
        total = len(self.lawyers_links)
        
        for i, (url, name) in enumerate(self.lawyers_links):
            self.logger.info(f"📋 {i+1}/{total}: {name}")
            
            success = self.extract_lawyer_details(url, name)
            if not success:
                self.logger.error(f"  ❌ {name} - Échec")
            
            # Sauvegarde intermédiaire automatique tous les 25 avocats
            if (i + 1) % 25 == 0:
                self.save_intermediate_backup(i + 1)
            
            time.sleep(1)  # Respecter le serveur
    
    def save_intermediate_backup(self, count):
        """Sauvegarder un backup intermédiaire pour sécurité"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"VANNES_BACKUP_{count}_avocats_{timestamp}.csv"
        
        with open(backup_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'annee_inscription', 'specialisations', 
                         'langues_parlees', 'structure', 'adresse', 'telephone', 'email', 'site_web', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        self.logger.info(f"💾 Sauvegarde intermédiaire: {backup_filename}")
    
    def save_final_results(self):
        """Sauvegarder les résultats finaux avec statistiques complètes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV final
        csv_filename = f"VANNES_FINAL_SPECIALISATIONS_CORRECTES_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'annee_inscription', 'specialisations', 
                         'langues_parlees', 'structure', 'adresse', 'telephone', 'email', 'site_web', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.lawyers_data)
        
        self.logger.info(f"✅ Fichier CSV final: {csv_filename}")
        
        # JSON final
        json_filename = f"VANNES_FINAL_SPECIALISATIONS_CORRECTES_{len(self.lawyers_data)}_avocats_{timestamp}.json"
        
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ Fichier JSON final: {json_filename}")
        
        # Rapport statistique détaillé
        report_filename = f"VANNES_RAPPORT_SPECIALISATIONS_FINAL_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as report:
            report.write("RAPPORT EXTRACTION SPÉCIALISATIONS - BARREAU DE VANNES\n")
            report.write("=" * 60 + "\n\n")
            report.write(f"Date: {datetime.now()}\n")
            report.write(f"Total avocats: {len(self.lawyers_data)}\n\n")
            
            # Statistiques détaillées
            with_specs = sum(1 for lawyer in self.lawyers_data if lawyer['specialisations'])
            with_langs = sum(1 for lawyer in self.lawyers_data if lawyer['langues_parlees'])
            
            report.write(f"STATISTIQUES SPÉCIALISATIONS:\n")
            report.write(f"- Avec spécialisations: {with_specs} ({with_specs/len(self.lawyers_data)*100:.1f}%)\n")
            report.write(f"- Sans spécialisations: {len(self.lawyers_data)-with_specs} ({(len(self.lawyers_data)-with_specs)/len(self.lawyers_data)*100:.1f}%)\n")
            report.write(f"- Avec langues: {with_langs} ({with_langs/len(self.lawyers_data)*100:.1f}%)\n")
            report.write(f"- Sans langues: {len(self.lawyers_data)-with_langs} ({(len(self.lawyers_data)-with_langs)/len(self.lawyers_data)*100:.1f}%)\n\n")
            
            # Exemples de spécialisations trouvées
            report.write("EXEMPLES DE SPÉCIALISATIONS TROUVÉES:\n")
            report.write("-" * 40 + "\n")
            specs_found = 0
            for lawyer in self.lawyers_data:
                if lawyer['specialisations'] and specs_found < 20:
                    report.write(f"• {lawyer['nom_complet']}: {lawyer['specialisations']}\n")
                    specs_found += 1
            
            if specs_found == 0:
                report.write("Aucune spécialisation trouvée !\n")
        
        self.logger.info(f"✅ Rapport final: {report_filename}")
        self.logger.info(f"📊 TOTAL: {len(self.lawyers_data)} avocats extraits")
    
    def run(self):
        """
        Exécuter l'extraction complète du Barreau de Vannes
        
        Process:
        1. Collecte tous les liens d'avocats (152 liens sur 19 pages)
        2. Extraction détaillée de chaque avocat avec spécialisations
        3. Sauvegarde automatique et rapport final
        """
        try:
            self.logger.info("🚀 VANNES SCRAPER - VERSION FINALE")
            self.logger.info("=" * 50)
            
            # Phase 1: Collecter tous les liens
            all_links = self.collect_all_lawyer_links()
            
            if not all_links:
                self.logger.error("❌ Aucun lien collecté")
                return
            
            # Phase 2: Extraire les détails de tous les avocats
            self.process_all_lawyers()
            
            # Sauvegarder les résultats finaux
            if self.lawyers_data:
                self.save_final_results()
                self.logger.info(f"✅ Extraction terminée: {len(self.lawyers_data)} avocats traités")
                
                # Statistiques finales
                with_specs = sum(1 for lawyer in self.lawyers_data if lawyer['specialisations'])
                self.logger.info(f"📈 Spécialisations trouvées: {with_specs} avocats ({with_specs/len(self.lawyers_data)*100:.1f}%)")
            else:
                self.logger.error("❌ Aucune donnée collectée")
                
        except Exception as e:
            self.logger.error(f"Erreur générale: {e}")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    scraper = VannesBarAssociationScraper()
    scraper.run()