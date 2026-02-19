#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau de Saint-Nazaire
https://www.barreau-saintnazaire.fr/

Ce script extrait la totalité des avocats du barreau de Saint-Nazaire avec toutes leurs informations :
- Prénom et nom (correctement séparés)
- Année d'inscription au barreau
- Email (depuis les liens mailto)
- Téléphone et adresse
- Spécialisations quand disponibles
- Structure/cabinet

Auteur: Claude Code
Date: Février 2026
"""

import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class SaintNazaireScraper:
    def __init__(self, headless=True):
        """
        Initialise le scraper Saint-Nazaire
        
        Args:
            headless (bool): True pour mode sans interface, False pour mode visible
        """
        self.setup_driver(headless)
        self.base_url = "https://www.barreau-saintnazaire.fr/les-avocats/lannuaire-des-avocats/page/{}"
        self.lawyers_data = []
        self.processed_lawyers = set()  # Pour éviter les doublons
        
    def setup_driver(self, headless=True):
        """Configure le driver Chrome avec les bonnes options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
    def accept_cookies(self):
        """Accepter les cookies du site"""
        try:
            print("🍪 Recherche du bouton d'acceptation des cookies...")
            
            # Attendre que la page soit chargée
            time.sleep(3)
            
            # Chercher le bouton d'acceptation via XPath
            buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accepter')]")
            if buttons:
                buttons[0].click()
                print("✅ Cookies acceptés")
                time.sleep(2)
                return True
                    
            print("⚠️  Aucun bouton de cookies trouvé, on continue...")
            return False
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'acceptation des cookies: {e}")
            return False
            
    def get_total_pages(self):
        """Déterminer le nombre total de pages de l'annuaire"""
        try:
            # Chercher les liens de pagination
            links = self.driver.find_elements(By.CSS_SELECTOR, '.pagination a, .page-numbers')
            max_page = 1
            
            for link in links:
                text = link.text.strip()
                if text.isdigit():
                    page_num = int(text)
                    max_page = max(max_page, page_num)
            
            print(f"📄 Nombre total de pages détecté: {max_page}")
            return max_page
            
        except Exception as e:
            print(f"⚠️  Erreur détection pagination: {e}")
            return 1
            
    def extract_lawyer_links(self):
        """Extraire les liens vers les fiches d'avocats de la page courante"""
        try:
            lawyer_links = []
            
            # Attendre que la page soit chargée
            time.sleep(2)
            
            # Chercher tous les liens contenant /avocat/
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/avocat/' in href and href not in self.processed_lawyers:
                    lawyer_links.append(href)
                    self.processed_lawyers.add(href)
            
            return list(set(lawyer_links))  # Supprimer doublons
            
        except Exception as e:
            print(f"❌ Erreur extraction liens: {e}")
            return []
            
    def parse_name(self, full_name):
        """Séparer prénom et nom, gestion des noms composés"""
        if not full_name:
            return "", ""
            
        # Nettoyer le nom
        full_name = full_name.strip()
        
        # Retirer les titres
        prefixes_to_remove = ['Me', 'Maître', 'M.', 'Mme', 'Docteur', 'Dr']
        for prefix in prefixes_to_remove:
            if full_name.startswith(prefix + ' '):
                full_name = full_name[len(prefix):].strip()
        
        parts = full_name.split()
        if len(parts) == 1:
            return "", parts[0]  # Un seul mot = nom seulement
        elif len(parts) == 2:
            part1, part2 = parts
            
            # Si les deux mots sont en MAJUSCULES
            if part1.isupper() and part2.isupper():
                if '-' in part1 or '-' in part2:
                    return "", " ".join(parts)  # Noms composés
                else:
                    # Analyser les patterns courants
                    common_short_names = ['Jean', 'Paul', 'Marie', 'Anne', 'Marc', 'Eric', 'Luc']
                    if len(part2) <= 4 or part2.title() in common_short_names:
                        return part2.title(), part1  # Prénom Nom
                    else:
                        return part1.title(), part2  # Prénom Nom
            else:
                # Cas normal avec casse mixte
                if part1.isupper() and not part2.isupper():
                    return part2, part1  # NOM Prénom
                else:
                    return part1, part2  # Prénom NOM
        else:
            # Plus de 2 mots - analyser la structure
            upper_words = [word for word in parts if word.isupper()]
            mixed_words = [word for word in parts if not word.isupper()]
            
            if len(upper_words) == len(parts):
                return "", " ".join(parts)  # Tous en majuscules = noms de famille
            elif len(mixed_words) == 1:
                prenom = mixed_words[0]
                nom_parts = [word for word in parts if word != prenom]
                return prenom, " ".join(nom_parts)
            else:
                # Cas mixte complexe
                if parts[0].isupper():
                    return " ".join(parts[1:]), parts[0]
                else:
                    return parts[0], " ".join(parts[1:])
            
    def extract_lawyer_details(self, lawyer_url):
        """Extraire les détails d'un avocat depuis sa page"""
        try:
            self.driver.get(lawyer_url)
            time.sleep(3)
            
            lawyer_info = {
                'prenom': '',
                'nom': '',
                'annee_inscription': '',
                'specialisations': '',
                'competences': '',
                'activites_dominantes': '',
                'structure': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'source': lawyer_url
            }
            
            # Extraction du nom depuis h2
            try:
                name_element = self.driver.find_element(By.CSS_SELECTOR, 'h2')
                full_name = name_element.text.strip()
                if full_name.startswith('Me'):
                    full_name = full_name[2:].strip()
                if full_name:
                    prenom, nom = self.parse_name(full_name)
                    lawyer_info['prenom'] = prenom
                    lawyer_info['nom'] = nom
            except:
                # Fallback sur h1
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, 'h1')
                    full_name = name_element.text.strip()
                    if full_name.startswith('Me'):
                        full_name = full_name[2:].strip()
                    if full_name:
                        prenom, nom = self.parse_name(full_name)
                        lawyer_info['prenom'] = prenom
                        lawyer_info['nom'] = nom
                except:
                    pass
            
            # Récupérer tout le texte de la page
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            # Recherche année d'inscription (date de serment)
            year_patterns = [
                r'Date\s+de\s+prestation\s+de\s+serment\s*:?\s*(\d{2}/\d{2}/\d{4})',
                r'prestation\s+de\s+serment\s*:?\s*(\d{2}/\d{2}/\d{4})',
                r'serment\s*:?\s*(\d{2}/\d{2}/\d{4})'
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    lawyer_info['annee_inscription'] = date_str.split('/')[-1]
                    break
            
            # Recherche email depuis les liens mailto
            try:
                mailto_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                for link in mailto_links:
                    href = link.get_attribute('href')
                    if href and href.startswith('mailto:'):
                        email = href.replace('mailto:', '').strip()
                        if '@' in email:
                            lawyer_info['email'] = email
                            break
            except:
                pass
            
            # Fallback: recherche email dans le texte
            if not lawyer_info['email']:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                email_matches = re.findall(email_pattern, page_text)
                if email_matches:
                    lawyer_info['email'] = email_matches[0]
            
            # Recherche téléphone
            phone_patterns = [
                r'(\d{2}\.?\d{2}\.?\d{2}\.?\d{2}\.?\d{2})',
                r'(\+33\s?\d\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})',
                r'(0\d\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, page_text)
                if match:
                    lawyer_info['telephone'] = match.group(1)
                    break
            
            # Recherche adresse
            address_patterns = [
                r'(\d+.*?44\d{3}.*?[A-Za-z-]+)',
                r'(.*?44600.*?Saint-Nazaire)',
                r'(\d+.*?Avenue.*?44\d{3}.*?)',
                r'(\d+.*?rue.*?44\d{3}.*?)'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    lawyer_info['adresse'] = match.group(1).strip()
                    break
            
            # Recherche spécialisations - méthode ciblée
            specialization_keywords = [
                'droit du travail', 'droit des affaires', 'droit commercial', 'droit civil',
                'droit pénal', 'droit de la famille', 'droit immobilier', 'droit fiscal',
                'droit social', 'droit bancaire', 'droit des assurances', 'droit public',
                'droit administratif', 'droit de la construction', 'droit médical',
                'droit du dommage corporel', 'droit de la sécurité sociale', 
                'droit de la concurrence', 'droit des sociétés'
            ]
            
            lines = page_text.split('\n')
            found_specializations = []
            
            for line in lines:
                line = line.strip().lower()
                if not line:
                    continue
                
                # Vérifier si la ligne contient une spécialisation valide
                for spec in specialization_keywords:
                    if spec in line and line.startswith(spec):
                        clean_spec = line.replace(spec, spec.title()).strip()
                        if clean_spec and len(clean_spec) < 100:
                            # Vérifier qu'il n'y a pas d'informations parasites
                            unwanted = ['contacter', 'mail', 'cabinet', 'avenue', 'rue', 'téléphone', '@', 'http']
                            if not any(unwanted_word in clean_spec.lower() for unwanted_word in unwanted):
                                found_specializations.append(clean_spec)
                        break
            
            # Assigner les spécialisations trouvées
            if found_specializations:
                unique_specs = list(set(found_specializations))[:3]  # Max 3 spécialisations
                lawyer_info['competences'] = ', '.join(unique_specs)
            
            # Recherche structure/cabinet
            structure_patterns = [
                r'cabinet\s+([^\n]+)',
                r'structure\s*:([^\n]+)',
                r'SCP\s+([^\n]+)',
                r'SELARL\s+([^\n]+)'
            ]
            
            for pattern in structure_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    lawyer_info['structure'] = match.group(1).strip()
                    break
            
            # Nettoyer toutes les données pour éviter les problèmes de CSV
            for key, value in lawyer_info.items():
                if isinstance(value, str):
                    # Supprimer les retours à la ligne et caractères de contrôle
                    value = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    # Supprimer les espaces multiples
                    value = ' '.join(value.split())
                    # Limiter la longueur
                    if len(value) > 200:
                        value = value[:200] + "..."
                    lawyer_info[key] = value.strip()
            
            return lawyer_info
            
        except Exception as e:
            print(f"❌ Erreur extraction détails {lawyer_url}: {e}")
            return None
            
    def run_scraping(self):
        """Lancer le scraping complet de tous les avocats"""
        try:
            print("🚀 Démarrage du scraping Saint-Nazaire")
            
            # Aller à la première page
            self.driver.get(self.base_url.format(1))
            time.sleep(3)
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Déterminer le nombre total de pages
            total_pages = self.get_total_pages()
            print(f"📚 Pages à traiter: {total_pages}")
            
            all_lawyer_links = []
            
            # Parcourir toutes les pages pour collecter les liens
            for page in range(1, total_pages + 1):
                try:
                    print(f"\n🔍 Page {page}/{total_pages}")
                    self.driver.get(self.base_url.format(page))
                    time.sleep(2)
                    
                    # Extraire les liens d'avocats de cette page
                    page_links = self.extract_lawyer_links()
                    all_lawyer_links.extend(page_links)
                    
                    print(f"   📋 {len(page_links)} avocats trouvés sur cette page")
                    
                except Exception as e:
                    print(f"   ❌ Erreur page {page}: {e}")
                    continue
            
            # Supprimer les doublons finaux
            all_lawyer_links = list(set(all_lawyer_links))
            print(f"\n🎯 Total: {len(all_lawyer_links)} avocats uniques à traiter")
            
            # Créer des sauvegardes régulières
            backup_frequency = 20
            
            # Extraire les détails de chaque avocat
            for i, lawyer_url in enumerate(all_lawyer_links, 1):
                try:
                    print(f"\n--- Avocat {i}/{len(all_lawyer_links)} ---")
                    lawyer_info = self.extract_lawyer_details(lawyer_url)
                    
                    if lawyer_info:
                        self.lawyers_data.append(lawyer_info)
                        print(f"✅ {lawyer_info['prenom']} {lawyer_info['nom']}")
                        
                        if lawyer_info['email']:
                            print(f"   📧 {lawyer_info['email']}")
                    else:
                        print("❌ Erreur extraction")
                    
                    # Sauvegarde régulière
                    if i % backup_frequency == 0:
                        self.save_backup(i)
                    
                    # Pause entre les requêtes
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Erreur avocat {i}: {e}")
                    continue
            
            print(f"\n🎉 Scraping terminé! {len(self.lawyers_data)} avocats extraits")
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return False
        finally:
            self.driver.quit()
            
    def save_backup(self, current_index):
        """Créer une sauvegarde intermédiaire"""
        if not self.lawyers_data:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"SAINTNAZAIRE_BACKUP_{len(self.lawyers_data)}sur{current_index}_{timestamp}.json"
        
        try:
            with open(backup_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
            print(f"   💾 Sauvegarde: {backup_filename}")
        except Exception as e:
            print(f"   ⚠️  Erreur sauvegarde: {e}")
            
    def save_results(self):
        """Sauvegarder les résultats finaux"""
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder en CSV
        csv_filename = f"SAINTNAZAIRE_FINAL_{len(self.lawyers_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if self.lawyers_data:
                writer = csv.DictWriter(csvfile, fieldnames=self.lawyers_data[0].keys())
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # Sauvegarder en JSON
        json_filename = f"SAINTNAZAIRE_FINAL_{len(self.lawyers_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Créer un fichier de emails uniquement
        emails_filename = f"SAINTNAZAIRE_FINAL_EMAILS_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            emails = set()
            for lawyer in self.lawyers_data:
                if lawyer.get('email'):
                    emails.add(lawyer['email'])
            
            for email in sorted(emails):
                emailfile.write(email + '\n')
        
        # Rapport final
        report_filename = f"SAINTNAZAIRE_FINAL_RAPPORT_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"=== RAPPORT FINAL SAINT-NAZAIRE ===\n")
            reportfile.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"Nombre d'avocats extraits: {len(self.lawyers_data)}\n\n")
            
            reportfile.write("=== STATISTIQUES FINALES ===\n")
            complete_profiles = sum(1 for lawyer in self.lawyers_data if lawyer['prenom'] and lawyer['nom'])
            reportfile.write(f"Profils avec prénom/nom: {complete_profiles}\n")
            
            with_year = sum(1 for lawyer in self.lawyers_data if lawyer['annee_inscription'])
            reportfile.write(f"Profils avec année d'inscription: {with_year}\n")
            
            with_email = sum(1 for lawyer in self.lawyers_data if lawyer['email'])
            reportfile.write(f"Profils avec email: {with_email}\n")
            
            with_phone = sum(1 for lawyer in self.lawyers_data if lawyer['telephone'])
            reportfile.write(f"Profils avec téléphone: {with_phone}\n")
            
            with_address = sum(1 for lawyer in self.lawyers_data if lawyer['adresse'])
            reportfile.write(f"Profils avec adresse: {with_address}\n")
            
            emails = set(lawyer['email'] for lawyer in self.lawyers_data if lawyer['email'])
            reportfile.write(f"Emails uniques: {len(emails)}\n")
            
            reportfile.write("\n=== ÉCHANTILLON FINAL ===\n")
            for i, lawyer in enumerate(self.lawyers_data[:10], 1):
                reportfile.write(f"\n{i}. {lawyer['prenom']} {lawyer['nom']}\n")
                reportfile.write(f"   Année: {lawyer['annee_inscription']}\n")
                reportfile.write(f"   Email: {lawyer['email']}\n")
                reportfile.write(f"   Téléphone: {lawyer['telephone']}\n")
        
        print(f"\n✅ Résultats finaux sauvegardés:")
        print(f"   📊 CSV: {csv_filename}")
        print(f"   📋 JSON: {json_filename}")
        print(f"   📧 Emails: {emails_filename}")
        print(f"   📄 Rapport: {report_filename}")

def main():
    """Fonction principale"""
    # Script en mode headless par défaut (pas d'interface visuelle)
    scraper = SaintNazaireScraper(headless=True)
    
    try:
        success = scraper.run_scraping()
        if success:
            scraper.save_results()
        else:
            print("❌ Échec du scraping")
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrompu par l'utilisateur")
        scraper.save_results()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        scraper.save_results()
    finally:
        try:
            scraper.driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()