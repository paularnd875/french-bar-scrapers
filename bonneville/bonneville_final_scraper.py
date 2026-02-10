#!/usr/bin/env python3
"""
Scraper final pour le Barreau de Bonneville
Extrait toutes les données des avocats depuis le PDF du tableau
"""

import os
import json
import csv
import time
import requests
import PyPDF2
import fitz  # PyMuPDF
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BonnevilleFinalScraper:
    def __init__(self, headless=True):
        self.base_url = "https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/"
        self.pdf_url = "https://www.ordre-avocats-bonneville.com/wp-content/uploads/2025/04/TABLEAU-ORDRE-2025.pdf"
        self.headless = headless
        self.driver = None
        self.lawyers_data = []
        
    def setup_driver(self):
        """Configure le driver Chrome"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def download_pdf(self):
        """Télécharge le PDF du tableau des avocats"""
        print("📄 Téléchargement du PDF du tableau...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(self.pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            pdf_filename = "bonneville_tableau_ordre_2025.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ PDF téléchargé : {pdf_filename}")
            return pdf_filename
            
        except Exception as e:
            print(f"❌ Erreur téléchargement PDF : {e}")
            return None
            
    def extract_text_from_pdf(self, pdf_path):
        """Extrait le texte du PDF"""
        print("📖 Extraction du texte du PDF...")
        
        text_content = ""
        
        try:
            # Essayer avec PyMuPDF d'abord (plus précis)
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
                
            doc.close()
            print(f"✅ Texte extrait avec PyMuPDF ({len(text_content)} caractères)")
            
        except Exception as e:
            print(f"⚠️ Échec PyMuPDF : {e}, essai avec PyPDF2...")
            
            # Fallback avec PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text_content += page.extract_text()
                        
                print(f"✅ Texte extrait avec PyPDF2 ({len(text_content)} caractères)")
                
            except Exception as e2:
                print(f"❌ Erreur extraction PDF : {e2}")
                return None
                
        # Sauvegarder le texte brut pour debug
        with open("bonneville_pdf_text.txt", "w", encoding='utf-8') as f:
            f.write(text_content)
            
        return text_content
        
    def parse_lawyers_from_text(self, text_content):
        """Parse les avocats depuis le texte extrait"""
        print("🔍 Parsing des avocats depuis le texte...")
        
        lawyers = []
        
        # Patterns pour identifier les avocats
        # Format typique : Nom Prénom (parfois avec "Me" ou "Maître")
        patterns = [
            # Pattern principal : Nom en majuscules suivi du prénom
            r'^([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ\s-]+)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûüç-]+(?:\s[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûüç-]+)*)',
            
            # Pattern avec Me. ou Maître
            r'(?:Me\.?|Maître)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ\s-]+)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûüç-]+)',
            
            # Pattern simple : prénom nom
            r'^([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûüç-]+)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ\s-]+)',
        ]
        
        lines = text_content.split('\n')
        current_lawyer = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
                
            # Chercher un avocat
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    if current_lawyer:
                        lawyers.append(current_lawyer)
                    
                    # Déterminer nom et prénom
                    if pattern == patterns[0]:  # Nom en majuscules puis prénom
                        nom = match.group(1).strip()
                        prenom = match.group(2).strip()
                    else:  # Autres patterns
                        prenom = match.group(1).strip()
                        nom = match.group(2).strip()
                    
                    current_lawyer = {
                        'nom': nom,
                        'prenom': prenom,
                        'nom_complet': f"{prenom} {nom}",
                        'email': '',
                        'telephone': '',
                        'adresse': '',
                        'annee_inscription': '',
                        'specialisations': '',
                        'structure': '',
                        'ligne_source': line
                    }
                    break
            
            # Si on a un avocat en cours, chercher ses informations dans les lignes suivantes
            if current_lawyer and not re.search(patterns[0], line) and not re.search(patterns[1], line):
                
                # Email
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', line)
                if email_match:
                    current_lawyer['email'] = email_match.group(1)
                    
                # Téléphone
                phone_match = re.search(r'(?:tél|tel|phone)?[:\s]*([0-9\s\.\-\+]{10,})', line, re.IGNORECASE)
                if phone_match:
                    current_lawyer['telephone'] = phone_match.group(1).strip()
                    
                # Année d'inscription
                year_match = re.search(r'(?:inscr|depuis|année)[a-z]*[:\s]*([12][0-9]{3})', line, re.IGNORECASE)
                if year_match:
                    current_lawyer['annee_inscription'] = year_match.group(1)
                    
                # Adresse (si elle contient des mots-clés d'adresse)
                if re.search(r'(?:rue|avenue|place|chemin|boulevard|allée|impasse|square)[^@]*$', line, re.IGNORECASE):
                    current_lawyer['adresse'] = line
                    
                # Structure (cabinet, etc.)
                if re.search(r'cabinet|société|sarl|scp|selarl|avocat', line, re.IGNORECASE):
                    if len(line) < 150:  # Éviter les longues descriptions
                        current_lawyer['structure'] = line
                        
                # Spécialisations
                if re.search(r'droit|spécial|compétence|domaine', line, re.IGNORECASE):
                    if len(line) < 200:
                        current_lawyer['specialisations'] = line
                        
        # Ajouter le dernier avocat
        if current_lawyer:
            lawyers.append(current_lawyer)
            
        print(f"✅ {len(lawyers)} avocats extraits du PDF")
        
        # Afficher un échantillon pour vérification
        if lawyers:
            print("\n📋 Échantillon des premiers avocats :")
            for i, lawyer in enumerate(lawyers[:3]):
                print(f"  {i+1}. {lawyer['nom_complet']}")
                if lawyer['email']:
                    print(f"     📧 {lawyer['email']}")
                if lawyer['telephone']:
                    print(f"     📞 {lawyer['telephone']}")
                    
        return lawyers
        
    def enhance_lawyer_data(self, lawyers):
        """Enrichit les données en visitant les fiches individuelles sur le site"""
        if not self.headless:
            print("🌐 Enrichissement des données via le site web...")
            
            try:
                self.setup_driver()
                self.driver.get(self.base_url)
                time.sleep(3)
                
                # Accepter les cookies si présents
                try:
                    cookie_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tout accepter')]"))
                    )
                    cookie_btn.click()
                    time.sleep(2)
                except:
                    pass
                    
                # Pour chaque avocat, chercher des informations supplémentaires
                enhanced_lawyers = []
                for i, lawyer in enumerate(lawyers):
                    if i >= 5:  # Limiter pour le test
                        break
                        
                    print(f"  Enrichissement {i+1}/{min(5, len(lawyers))}: {lawyer['nom_complet']}")
                    
                    # Chercher l'avocat sur le site
                    try:
                        # Effectuer une recherche ou navigation spécifique
                        page_source = self.driver.page_source.lower()
                        
                        # Vérifier si l'avocat a des informations spécialisées sur le site
                        name_parts = [lawyer['nom'].lower(), lawyer['prenom'].lower()]
                        
                        for part in name_parts:
                            if part in page_source:
                                # Extraire le contexte autour du nom
                                context_match = re.search(f'.{{0,200}}{re.escape(part)}.{{0,200}}', page_source)
                                if context_match:
                                    context = context_match.group(0)
                                    
                                    # Chercher email dans le contexte
                                    email_in_context = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', context)
                                    if email_in_context and not lawyer['email']:
                                        lawyer['email'] = email_in_context.group(1)
                                        
                                break
                                
                    except Exception as e:
                        print(f"    ⚠️ Erreur enrichissement : {e}")
                        
                    enhanced_lawyers.append(lawyer)
                    
                return enhanced_lawyers
                
            except Exception as e:
                print(f"❌ Erreur enrichissement général : {e}")
                return lawyers
            finally:
                if self.driver:
                    self.driver.quit()
        else:
            return lawyers
            
    def save_results(self, lawyers):
        """Sauvegarde les résultats"""
        if not lawyers:
            print("ℹ️ Aucune donnée à sauvegarder")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde CSV
        csv_filename = f"bonneville_avocats_complet_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                         'adresse', 'annee_inscription', 'specialisations', 'structure']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in lawyers:
                # Nettoyer les données
                clean_lawyer = {}
                for key in fieldnames:
                    value = lawyer.get(key, '')
                    if isinstance(value, str):
                        value = value.strip().replace('\n', ' ').replace('\t', ' ')
                        # Supprimer les espaces multiples
                        value = re.sub(r'\s+', ' ', value)
                    clean_lawyer[key] = value
                    
                writer.writerow(clean_lawyer)
                
        # Sauvegarde JSON
        json_filename = f"bonneville_avocats_complet_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
            
        # Fichier texte avec emails seulement
        emails_filename = f"bonneville_emails_seulement_{timestamp}.txt"
        emails = [lawyer['email'] for lawyer in lawyers if lawyer.get('email')]
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in emails:
                emailfile.write(f"{email}\n")
                
        # Rapport final
        report_filename = f"bonneville_rapport_complet_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"RAPPORT D'EXTRACTION - BARREAU DE BONNEVILLE\n")
            reportfile.write(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            reportfile.write(f"{'='*50}\n\n")
            
            reportfile.write(f"STATISTIQUES :\n")
            reportfile.write(f"Total avocats : {len(lawyers)}\n")
            
            emails_found = sum(1 for lawyer in lawyers if lawyer.get('email'))
            phones_found = sum(1 for lawyer in lawyers if lawyer.get('telephone'))
            addresses_found = sum(1 for lawyer in lawyers if lawyer.get('adresse'))
            years_found = sum(1 for lawyer in lawyers if lawyer.get('annee_inscription'))
            specs_found = sum(1 for lawyer in lawyers if lawyer.get('specialisations'))
            structures_found = sum(1 for lawyer in lawyers if lawyer.get('structure'))
            
            reportfile.write(f"Emails trouvés : {emails_found}\n")
            reportfile.write(f"Téléphones trouvés : {phones_found}\n")
            reportfile.write(f"Adresses trouvées : {addresses_found}\n")
            reportfile.write(f"Années inscription : {years_found}\n")
            reportfile.write(f"Spécialisations : {specs_found}\n")
            reportfile.write(f"Structures : {structures_found}\n\n")
            
            reportfile.write(f"FICHIERS GÉNÉRÉS :\n")
            reportfile.write(f"- {csv_filename}\n")
            reportfile.write(f"- {json_filename}\n")
            reportfile.write(f"- {emails_filename}\n")
            reportfile.write(f"- {report_filename}\n")
            
        print(f"\n✅ EXTRACTION TERMINÉE")
        print(f"📊 {len(lawyers)} avocats extraits")
        print(f"📧 {emails_found} emails trouvés")
        print(f"📞 {phones_found} téléphones trouvés")
        print(f"\n📁 Fichiers générés :")
        print(f"   • {csv_filename}")
        print(f"   • {json_filename}")
        print(f"   • {emails_filename}")
        print(f"   • {report_filename}")
        
    def run_full_extraction(self):
        """Lance l'extraction complète"""
        print("🚀 DÉMARRAGE DE L'EXTRACTION COMPLÈTE - BARREAU DE BONNEVILLE")
        print("="*60)
        
        try:
            # 1. Télécharger le PDF
            pdf_path = self.download_pdf()
            if not pdf_path:
                return False
                
            # 2. Extraire le texte
            text_content = self.extract_text_from_pdf(pdf_path)
            if not text_content:
                return False
                
            # 3. Parser les avocats
            lawyers = self.parse_lawyers_from_text(text_content)
            if not lawyers:
                print("❌ Aucun avocat trouvé dans le PDF")
                return False
                
            # 4. Enrichir les données (optionnel, seulement en mode non-headless)
            lawyers = self.enhance_lawyer_data(lawyers)
            
            # 5. Sauvegarder
            self.save_results(lawyers)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur générale : {e}")
            return False

if __name__ == "__main__":
    # Mode headless par défaut (pas de fenêtres)
    scraper = BonnevilleFinalScraper(headless=True)
    
    print("Mode headless activé - aucune fenêtre ne s'ouvrira")
    success = scraper.run_full_extraction()
    
    if success:
        print("\n🎉 Extraction réussie !")
    else:
        print("\n❌ Échec de l'extraction")