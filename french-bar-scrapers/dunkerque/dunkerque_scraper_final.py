#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper final pour le Barreau de Dunkerque
Extraction complète et robuste de tous les avocats avec correction automatique des noms
URL: https://barreau-dunkerque.fr/search-result/?directory_type=general

Fonctionnalités:
- Extraction exhaustive de tous les 79 avocats
- Recherche par défaut + alphabétique pour couverture complète  
- Correction automatique des noms et prénoms
- Gestion robuste des erreurs avec redémarrages automatiques
- Export CSV, JSON et rapports détaillés
"""

import time
import json
import csv
import re
import os
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

class DunkerqueScraperFinal:
    def __init__(self):
        self.base_url = "https://barreau-dunkerque.fr/search-result/?directory_type=general"
        self.driver = None
        self.wait = None
        self.all_lawyers = []
        self.seen_urls = set()
        
    def setup_driver(self):
        """Initialisation du driver avec options optimisées"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 15)
        
    def close_driver(self):
        """Fermeture propre du driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            
    def restart_driver(self):
        """Redémarre le driver en cas de problème"""
        print("🔄 Redémarrage du navigateur...")
        self.close_driver()
        time.sleep(3)
        self.setup_driver()
        
    def get_lawyer_cards(self):
        """Extraction des cartes d'avocats de la page actuelle"""
        try:
            time.sleep(2)
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".lawyer-card, .single-result, .avocat-card, [class*='lawyer'], [class*='avocat']")
            
            if not cards:
                # Essai avec d'autres sélecteurs
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".entry-content .row > div")
                
            return [card for card in cards if card.text.strip()]
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des cartes: {e}")
            return []
            
    def extract_lawyer_details(self, card):
        """Extraction des détails d'un avocat depuis sa carte"""
        try:
            lawyer_data = {
                'nom_complet': '',
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'url_fiche': '',
                'autres_infos': {}
            }
            
            # Nom complet
            name_selectors = [
                "h3", "h4", ".lawyer-name", ".nom-avocat", 
                ".entry-title", "strong", ".title"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if name_elem and name_elem.text.strip():
                        lawyer_data['nom_complet'] = name_elem.text.strip()
                        break
                except:
                    continue
                    
            # Email
            email_selectors = [
                "a[href*='mailto:']", ".email", "[data-email]", 
                "span[style*='color']", ".contact-email"
            ]
            
            for selector in email_selectors:
                try:
                    email_elem = card.find_element(By.CSS_SELECTOR, selector)
                    if email_elem:
                        if 'mailto:' in email_elem.get_attribute('href') or '':
                            lawyer_data['email'] = email_elem.get_attribute('href').replace('mailto:', '').strip()
                        elif '@' in email_elem.text:
                            lawyer_data['email'] = email_elem.text.strip()
                        
                        if lawyer_data['email']:
                            break
                except:
                    continue
                    
            # Téléphone
            phone_pattern = r'(\+33\s?[0-9]\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}|0[0-9]\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2}\s?[0-9]{2})'
            phone_match = re.search(phone_pattern, card.text)
            if phone_match:
                lawyer_data['telephone'] = phone_match.group(1).strip()
                
            # URL de la fiche
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a[href*='/avocat/'], a[href*='/lawyer/'], a")
                if link_elem:
                    href = link_elem.get_attribute('href')
                    if href and ('avocat' in href or 'lawyer' in href):
                        lawyer_data['url_fiche'] = href
            except:
                pass
                
            # Année d'inscription
            year_pattern = r'(19[0-9]{2}|20[0-9]{2})'
            year_match = re.search(year_pattern, card.text)
            if year_match:
                lawyer_data['annee_inscription'] = year_match.group(1)
                
            # Spécialisations (texte contenant des domaines juridiques)
            specialisation_keywords = [
                'droit', 'pénal', 'civil', 'commercial', 'famille', 'travail', 
                'immobilier', 'fiscal', 'public', 'social', 'assurance'
            ]
            
            text_lower = card.text.lower()
            for keyword in specialisation_keywords:
                if keyword in text_lower:
                    # Extraire la phrase contenant le mot-clé
                    sentences = card.text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            lawyer_data['specialisations'].append(sentence.strip())
                            break
                            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur extraction détails: {e}")
            return None
            
    def correct_names_and_surnames(self, lawyer_data):
        """Correction automatique des noms et prénoms"""
        if not lawyer_data['nom_complet']:
            return lawyer_data
            
        full_name = lawyer_data['nom_complet'].replace('Maître ', '').replace('Maitre ', '').strip()
        
        # Corrections manuelles pour tous les 79 avocats
        name_corrections = {
            'Hugues FEBVAY': {'prenom': 'Hugues', 'nom': 'FEBVAY'},
            'Dominique SOMMEVILLE': {'prenom': 'Dominique', 'nom': 'SOMMEVILLE'},
            'Dominique VANBATTEN': {'prenom': 'Dominique', 'nom': 'VANBATTEN'},
            'Jean-Pierre MOUGEL': {'prenom': 'Jean-Pierre', 'nom': 'MOUGEL'},
            'Hugues SENLECQ': {'prenom': 'Hugues', 'nom': 'SENLECQ'},
            'Hervé JOLY': {'prenom': 'Hervé', 'nom': 'JOLY'},
            'Frédéric DUFOUR': {'prenom': 'Frédéric', 'nom': 'DUFOUR'},
            'Isabelle MASAY': {'prenom': 'Isabelle', 'nom': 'MASAY'},
            'Anne-Sophie ODOU – GRASSET': {'prenom': 'Anne-Sophie', 'nom': 'ODOU – GRASSET'},
            'Thierry COURQUIN': {'prenom': 'Thierry', 'nom': 'COURQUIN'},
            'Laurent LESTARQUIT': {'prenom': 'Laurent', 'nom': 'LESTARQUIT'},
            'Marc DEBEUGNY': {'prenom': 'Marc', 'nom': 'DEBEUGNY'},
            'Marianne DEVAUX': {'prenom': 'Marianne', 'nom': 'DEVAUX'},
            'Cécile GOMBERT': {'prenom': 'Cécile', 'nom': 'GOMBERT'},
            'François SHAKESHAFT': {'prenom': 'François', 'nom': 'SHAKESHAFT'},
            'Didier CATTOIR': {'prenom': 'Didier', 'nom': 'CATTOIR'},
            'Jean-Philippe CARLIER': {'prenom': 'Jean-Philippe', 'nom': 'CARLIER'},
            'Nathalie PELLETIER': {'prenom': 'Nathalie', 'nom': 'PELLETIER'},
            'Carine LECUTIER – ROSSEEL': {'prenom': 'Carine', 'nom': 'LECUTIER – ROSSEEL'},
            'Valérie ROBERT': {'prenom': 'Valérie', 'nom': 'ROBERT'},
            'Bertrand WATTEZ': {'prenom': 'Bertrand', 'nom': 'WATTEZ'},
            'Jean-Charles COURTOIS': {'prenom': 'Jean-Charles', 'nom': 'COURTOIS'},
            'Emmanuelle DEBRUYNE': {'prenom': 'Emmanuelle', 'nom': 'DEBRUYNE'},
            'Isabelle DE LYLLE': {'prenom': 'Isabelle', 'nom': 'DE LYLLE'},
            'Véronique PLANCKEEL': {'prenom': 'Véronique', 'nom': 'PLANCKEEL'},
            'Laurence GUEIT': {'prenom': 'Laurence', 'nom': 'GUEIT'},
            'David BROUWER': {'prenom': 'David', 'nom': 'BROUWER'},
            'Loreleï VITSE': {'prenom': 'Loreleï', 'nom': 'VITSE'},
            'Franck GYS': {'prenom': 'Franck', 'nom': 'GYS'},
            'Ilias KARAGHIANNIS': {'prenom': 'Ilias', 'nom': 'KARAGHIANNIS'},
            'Katya BIDET': {'prenom': 'Katya', 'nom': 'BIDET'},
            'Caroline BELVAL': {'prenom': 'Caroline', 'nom': 'BELVAL'},
            'François ROSSEEL': {'prenom': 'François', 'nom': 'ROSSEEL'},
            'Sophie ANDRIES': {'prenom': 'Sophie', 'nom': 'ANDRIES'},
            'Charlotte CATRIX': {'prenom': 'Charlotte', 'nom': 'CATRIX'},
            'Jacques-Louis COLOMBANI': {'prenom': 'Jacques-Louis', 'nom': 'COLOMBANI'},
            'Martin DANEL': {'prenom': 'Martin', 'nom': 'DANEL'},
            'Ingrid SCHOEMAECKER': {'prenom': 'Ingrid', 'nom': 'SCHOEMAECKER'},
            'Pierre CORTIER': {'prenom': 'Pierre', 'nom': 'CORTIER'},
            'Ingrid LERMECHIN': {'prenom': 'Ingrid', 'nom': 'LERMECHIN'},
            'Hélène BEHELLE': {'prenom': 'Hélène', 'nom': 'BEHELLE'},
            'Simon PEROT': {'prenom': 'Simon', 'nom': 'PEROT'},
            'Magalie WADOUX': {'prenom': 'Magalie', 'nom': 'WADOUX'},
            'Faïza ELMOKRETAR': {'prenom': 'Faïza', 'nom': 'ELMOKRETAR'},
            'Fanny FAUQUET': {'prenom': 'Fanny', 'nom': 'FAUQUET'},
            'Guillaume GUILLUY': {'prenom': 'Guillaume', 'nom': 'GUILLUY'},
            'Frédérique MAZUREK': {'prenom': 'Frédérique', 'nom': 'MAZUREK'},
            'Aurélie WATEL': {'prenom': 'Aurélie', 'nom': 'WATEL'},
            'Julien SABOS': {'prenom': 'Julien', 'nom': 'SABOS'},
            'Xavier FERRAND': {'prenom': 'Xavier', 'nom': 'FERRAND'},
            'Léa MAENHAUT': {'prenom': 'Léa', 'nom': 'MAENHAUT'},
            'Julie BROY': {'prenom': 'Julie', 'nom': 'BROY'},
            'Anaïs PASCAL': {'prenom': 'Anaïs', 'nom': 'PASCAL'},
            'Alice MARANT': {'prenom': 'Alice', 'nom': 'MARANT'},
            'Nicolas HAUDIQUET': {'prenom': 'Nicolas', 'nom': 'HAUDIQUET'},
            'Henry-François CATTOIR': {'prenom': 'Henry-François', 'nom': 'CATTOIR'},
            'Antoine VANDICHEL – CHOLET': {'prenom': 'Antoine', 'nom': 'VANDICHEL – CHOLET'},
            'Claire CAUSTIER': {'prenom': 'Claire', 'nom': 'CAUSTIER'},
            'Flavien HERTEL': {'prenom': 'Flavien', 'nom': 'HERTEL'},
            'Lauriane TIMMERMAN': {'prenom': 'Lauriane', 'nom': 'TIMMERMAN'},
            'Clément HUTIN': {'prenom': 'Clément', 'nom': 'HUTIN'},
            'Fatima AIT BAMAR': {'prenom': 'Fatima', 'nom': 'AIT BAMAR'},
            'Amélie DESTAILLEUR': {'prenom': 'Amélie', 'nom': 'DESTAILLEUR'},
            'Audrey VERHOEVEN': {'prenom': 'Audrey', 'nom': 'VERHOEVEN'},
            'Yann LEUPE': {'prenom': 'Yann', 'nom': 'LEUPE'},
            'Amandine BUCZINSKI': {'prenom': 'Amandine', 'nom': 'BUCZINSKI'},
            'Laura BREUILLAC': {'prenom': 'Laura', 'nom': 'BREUILLAC'},
            'Hélène HERBAUT-MOGNOLLE': {'prenom': 'Hélène', 'nom': 'HERBAUT-MOGNOLLE'},
            'Manon LEFEBVRE': {'prenom': 'Manon', 'nom': 'LEFEBVRE'},
            'Clémence KOHL': {'prenom': 'Clémence', 'nom': 'KOHL'},
            'Tony MACRIPO': {'prenom': 'Tony', 'nom': 'MACRIPO'},
            'Lucine HESSEL GORLIA': {'prenom': 'Lucine', 'nom': 'HESSEL GORLIA'},
            'Virginie DASSONEVILLE': {'prenom': 'Virginie', 'nom': 'DASSONEVILLE'},
            'Adrien THILLIEZ': {'prenom': 'Adrien', 'nom': 'THILLIEZ'},
            'Margot MONTAGNE': {'prenom': 'Margot', 'nom': 'MONTAGNE'},
            'Marine AGNERAY': {'prenom': 'Marine', 'nom': 'AGNERAY'},
            'Maïthé MORISOT': {'prenom': 'Maïthé', 'nom': 'MORISOT'},
            'Thomas ONRAET': {'prenom': 'Thomas', 'nom': 'ONRAET'},
            'Marion POULLAIN': {'prenom': 'Marion', 'nom': 'POULLAIN'}
        }
        
        if full_name in name_corrections:
            lawyer_data['prenom'] = name_corrections[full_name]['prenom']
            lawyer_data['nom'] = name_corrections[full_name]['nom']
        else:
            # Algorithme générique pour les nouveaux cas
            parts = full_name.split()
            
            if len(parts) == 1:
                lawyer_data['prenom'] = ''
                lawyer_data['nom'] = parts[0]
            elif len(parts) == 2:
                lawyer_data['prenom'] = parts[0]
                lawyer_data['nom'] = parts[1]
            else:
                # Gestion des noms composés avec particules ou tirets
                if any(part in ['DE', 'DU', 'DES', 'LA', 'LE', 'VAN', 'VON', 'AIT', 'BEN'] for part in parts[1:]):
                    lawyer_data['prenom'] = parts[0]
                    lawyer_data['nom'] = ' '.join(parts[1:])
                elif '-' in parts[0]:
                    lawyer_data['prenom'] = parts[0]
                    lawyer_data['nom'] = ' '.join(parts[1:])
                else:
                    lawyer_data['prenom'] = parts[0]
                    lawyer_data['nom'] = ' '.join(parts[1:])
        
        return lawyer_data
        
    def search_by_letter(self, letter):
        """Recherche alphabétique par lettre"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Recherche du champ de recherche
            search_selectors = [
                "input[type='search']", "input[name='search']", 
                "#search", ".search-field", "input.search"
            ]
            
            for selector in search_selectors:
                try:
                    search_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_field.clear()
                    search_field.send_keys(letter)
                    
                    # Soumettre la recherche
                    search_field.submit()
                    time.sleep(3)
                    return True
                except:
                    continue
                    
            return False
            
        except Exception as e:
            print(f"❌ Erreur recherche lettre {letter}: {e}")
            return False
            
    def extract_all_lawyers(self):
        """Extraction exhaustive de tous les avocats"""
        print("🎯 Début de l'extraction exhaustive des avocats de Dunkerque")
        print("-" * 60)
        
        self.setup_driver()
        
        try:
            # 1. Extraction par défaut
            print("📋 1. Extraction par défaut...")
            self.driver.get(self.base_url)
            time.sleep(5)
            
            cards = self.get_lawyer_cards()
            print(f"✅ {len(cards)} cartes trouvées par défaut")
            
            for i, card in enumerate(cards, 1):
                lawyer_data = self.extract_lawyer_details(card)
                if lawyer_data and lawyer_data['nom_complet']:
                    lawyer_data = self.correct_names_and_surnames(lawyer_data)
                    
                    # Éviter les doublons
                    identifier = f"{lawyer_data['nom_complet']}-{lawyer_data['email']}"
                    if identifier not in self.seen_urls:
                        self.all_lawyers.append(lawyer_data)
                        self.seen_urls.add(identifier)
                        print(f"   {i:2d}. {lawyer_data['nom_complet']}")
                        
            print(f"✅ {len(self.all_lawyers)} avocats extraits par défaut")
            
            # 2. Recherche alphabétique pour les manquants
            print("\n🔤 2. Recherche alphabétique complémentaire...")
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            
            for letter in alphabet:
                print(f"🔍 Recherche lettre {letter}...")
                
                if self.search_by_letter(letter):
                    time.sleep(2)
                    cards = self.get_lawyer_cards()
                    
                    new_lawyers = 0
                    for card in cards:
                        lawyer_data = self.extract_lawyer_details(card)
                        if lawyer_data and lawyer_data['nom_complet']:
                            lawyer_data = self.correct_names_and_surnames(lawyer_data)
                            
                            identifier = f"{lawyer_data['nom_complet']}-{lawyer_data['email']}"
                            if identifier not in self.seen_urls:
                                self.all_lawyers.append(lawyer_data)
                                self.seen_urls.add(identifier)
                                print(f"   ➕ Nouveau: {lawyer_data['nom_complet']}")
                                new_lawyers += 1
                                
                    if new_lawyers == 0:
                        print(f"   ➖ Aucun nouveau avocat pour la lettre {letter}")
                        
                # Redémarrage périodique du driver
                if len(self.all_lawyers) % 20 == 0:
                    self.restart_driver()
                    
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            traceback.print_exc()
        finally:
            self.close_driver()
            
        return self.all_lawyers
        
    def save_results(self, lawyers):
        """Sauvegarde des résultats dans différents formats"""
        if not lawyers:
            print("❌ Aucun résultat à sauvegarder!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON
        json_filename = f"dunkerque_FINAL_COMPLET_{len(lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(lawyers, f, ensure_ascii=False, indent=2)
        print(f"📁 JSON: {json_filename}")
        
        # 2. CSV
        csv_filename = f"dunkerque_FINAL_COMPLET_{len(lawyers)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                         'annee_inscription', 'specialisations', 'structure', 'url_fiche']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in lawyers:
                lawyer_copy = lawyer.copy()
                lawyer_copy['specialisations'] = '; '.join(lawyer.get('specialisations', []))
                lawyer_copy.pop('autres_infos', None)
                writer.writerow(lawyer_copy)
        print(f"📁 CSV: {csv_filename}")
        
        # 3. Emails uniquement
        emails = [l['email'] for l in lawyers if l.get('email')]
        email_filename = f"dunkerque_FINAL_EMAILS_{len(emails)}_sur_{len(lawyers)}_{timestamp}.txt"
        with open(email_filename, 'w', encoding='utf-8') as f:
            f.write(f"=== EMAILS AVOCATS BARREAU DE DUNKERQUE ===\n")
            f.write(f"Extraction du {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n")
            f.write(f"Total: {len(emails)} emails sur {len(lawyers)} avocats ({len(emails)/len(lawyers)*100:.1f}%)\n\n")
            for email in sorted(emails):
                f.write(f"{email}\n")
        print(f"📁 Emails: {email_filename}")
        
        # 4. Rapport détaillé
        report_filename = f"dunkerque_RAPPORT_FINAL_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("🏛️ RAPPORT D'EXTRACTION - BARREAU DE DUNKERQUE\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            f.write(f"URL source: {self.base_url}\n\n")
            
            f.write("📊 STATISTIQUES GÉNÉRALES:\n")
            f.write(f"- Total avocats extraits: {len(lawyers)}\n")
            f.write(f"- Avocats avec email: {len(emails)} ({len(emails)/len(lawyers)*100:.1f}%)\n")
            
            phones = [l['telephone'] for l in lawyers if l.get('telephone')]
            f.write(f"- Avocats avec téléphone: {len(phones)} ({len(phones)/len(lawyers)*100:.1f}%)\n")
            
            years = [l['annee_inscription'] for l in lawyers if l.get('annee_inscription')]
            f.write(f"- Avocats avec année inscription: {len(years)} ({len(years)/len(lawyers)*100:.1f}%)\n")
            
            f.write("\n📋 LISTE COMPLÈTE DES AVOCATS:\n")
            f.write("-" * 60 + "\n")
            for i, lawyer in enumerate(sorted(lawyers, key=lambda x: x['nom']), 1):
                f.write(f"{i:2d}. {lawyer['nom_complet']}\n")
                f.write(f"    Prénom: {lawyer['prenom']} | Nom: {lawyer['nom']}\n")
                if lawyer['email']:
                    f.write(f"    Email: {lawyer['email']}\n")
                if lawyer['telephone']:
                    f.write(f"    Tél: {lawyer['telephone']}\n")
                if lawyer['annee_inscription']:
                    f.write(f"    Inscription: {lawyer['annee_inscription']}\n")
                f.write("\n")
                
        print(f"📁 Rapport: {report_filename}")
        
        return {
            'json': json_filename,
            'csv': csv_filename,
            'emails': email_filename,
            'report': report_filename
        }

def main():
    """Fonction principale"""
    scraper = DunkerqueScraperFinal()
    
    try:
        lawyers = scraper.extract_all_lawyers()
        
        if lawyers:
            print("\n" + "=" * 60)
            print("🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print(f"✅ {len(lawyers)} avocats extraits au total")
            
            files = scraper.save_results(lawyers)
            
            print("\n📁 Fichiers générés:")
            for file_type, filename in files.items():
                print(f"   {file_type.upper()}: {filename}")
                
            # Statistiques finales
            emails = [l['email'] for l in lawyers if l.get('email')]
            phones = [l['telephone'] for l in lawyers if l.get('telephone')]
            
            print(f"\n📊 Statistiques:")
            print(f"   📧 Emails: {len(emails)}/{len(lawyers)} ({len(emails)/len(lawyers)*100:.1f}%)")
            print(f"   📞 Téléphones: {len(phones)}/{len(lawyers)} ({len(phones)/len(lawyers)*100:.1f}%)")
            print(f"   🎯 Objectif 79 avocats: {'✅ ATTEINT' if len(lawyers) >= 79 else '❌ PAS ATTEINT'}")
            
        else:
            print("❌ Aucun avocat extrait!")
            
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()