#!/usr/bin/env python3
"""
Scraper exhaustif pour le Barreau de Bonneville
Recense d'abord TOUTES les fiches d'avocats avant extraction
"""

import time
import json
import csv
import requests
import fitz  # PyMuPDF
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BonnevilleExhaustiveScraper:
    def __init__(self, headless=True):
        self.base_url = "https://www.ordre-avocats-bonneville.com/barreau-bonneville-pays-mont-blanc/annuaire-avocats/"
        self.pdf_url = "https://www.ordre-avocats-bonneville.com/wp-content/uploads/2025/04/TABLEAU-ORDRE-2025.pdf"
        self.headless = headless
        self.driver = None
        self.all_lawyers = []
        
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
        
    def download_and_parse_pdf_exhaustive(self):
        """Télécharge et parse complètement le PDF pour trouver TOUS les avocats"""
        print("📄 Téléchargement du PDF complet...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(self.pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            pdf_filename = "tableau_bonneville_complet.pdf"
            with open(pdf_filename, 'wb') as f:
                f.write(response.content)
                
            print(f"✅ PDF téléchargé : {pdf_filename}")
            
            # Extraire le texte complet
            doc = fitz.open(pdf_filename)
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                full_text += f"\n=== PAGE {page_num + 1} ===\n"
                full_text += page_text
                
            doc.close()
            
            # Sauvegarder le texte complet pour analyse
            with open("bonneville_pdf_complet.txt", "w", encoding='utf-8') as f:
                f.write(full_text)
                
            print(f"✅ Texte complet extrait ({len(full_text)} caractères)")
            return full_text
            
        except Exception as e:
            print(f"❌ Erreur téléchargement/parsing PDF : {e}")
            return None
            
    def parse_all_lawyers_from_pdf(self, pdf_text):
        """Parse exhaustif de TOUS les avocats dans le PDF"""
        print("🔍 Recherche exhaustive de tous les avocats...")
        
        lawyers = []
        lines = pdf_text.split('\n')
        
        # Patterns améliorés pour capturer différents formats d'avocats
        patterns = [
            # Pattern principal avec structure complète
            r'([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+([A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+(?:\s+[A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)*)\s*-\s*([^-]*?)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\s\'-]+?)\s*-\s*([^0-9]+?)\s+(0[0-9][\d\.\s]+)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+([0-9]{4})',
            
            # Pattern simplifié pour noms suivis d'email et année
            r'([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+([A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+(?:\s+[A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)*)\s+.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s+([0-9]{4})',
            
            # Pattern pour lignes avec email et téléphone
            r'([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+([A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+.*?(0[0-9][\d\.\s]+)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        ]
        
        # Chercher tous les avocats avec différents patterns
        found_lawyers = set()  # Pour éviter les doublons
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 20:
                continue
                
            for pattern_num, pattern in enumerate(patterns):
                matches = re.findall(pattern, line)
                
                for match in matches:
                    if len(match) >= 4:
                        nom = match[0].strip().title()
                        prenom = match[1].strip().title()
                        
                        # Identifier email et année selon le pattern
                        if pattern_num == 0 and len(match) >= 8:  # Pattern complet
                            email = match[6]
                            annee = match[7]
                            telephone = match[5].strip()
                            ville = match[3].strip()
                        elif pattern_num == 1 and len(match) >= 4:  # Pattern simplifié
                            email = match[2]
                            annee = match[3]
                            telephone = ""
                            ville = ""
                        else:  # Autres patterns
                            email = match[-1] if '@' in match[-1] else ""
                            annee = ""
                            telephone = ""
                            ville = ""
                            
                        # Vérifier que c'est un email valide
                        if '@' in email and '.' in email:
                            lawyer_key = f"{nom}_{prenom}_{email}"
                            
                            if lawyer_key not in found_lawyers:
                                found_lawyers.add(lawyer_key)
                                
                                lawyer_info = {
                                    'nom': nom,
                                    'prenom': prenom,
                                    'nom_complet': f"{prenom} {nom}",
                                    'email': email,
                                    'telephone': telephone,
                                    'ville': ville,
                                    'annee_inscription': annee,
                                    'ligne_source': line,
                                    'ligne_numero': line_num + 1,
                                    'pattern_utilise': pattern_num + 1
                                }
                                
                                lawyers.append(lawyer_info)
                                print(f"  ✓ {len(lawyers):2d}. {prenom} {nom} - {email}")
        
        # Recherche supplémentaire avec regex plus flexible
        print("\n🔍 Recherche supplémentaire avec patterns flexibles...")
        
        # Chercher des lignes contenant email + possible nom
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Chercher des emails
            email_matches = re.findall(email_pattern, line)
            
            for email in email_matches:
                # Vérifier si cet email n'est pas déjà dans notre liste
                email_exists = any(lawyer['email'] == email for lawyer in lawyers)
                
                if not email_exists:
                    # Chercher des noms potentiels dans la même ligne ou lignes adjacentes
                    name_patterns = [
                        r'([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+([A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)',
                        r'([A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)\s+([A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][A-Za-zàáâäèéêëìíîïòóôöùúûüç\'-]+)'
                    ]
                    
                    # Chercher dans la ligne actuelle et les lignes adjacentes
                    search_lines = []
                    if line_num > 0:
                        search_lines.append(lines[line_num - 1])
                    search_lines.append(line)
                    if line_num < len(lines) - 1:
                        search_lines.append(lines[line_num + 1])
                    
                    name_found = False
                    for search_line in search_lines:
                        for name_pattern in name_patterns:
                            name_matches = re.findall(name_pattern, search_line)
                            
                            for name_match in name_matches:
                                if len(name_match) == 2:
                                    potential_nom = name_match[0].strip()
                                    potential_prenom = name_match[1].strip()
                                    
                                    # Vérifier que ce sont de vrais noms (pas des mots techniques)
                                    if (len(potential_nom) > 2 and len(potential_prenom) > 2 and
                                        not any(word in potential_nom.lower() for word in ['selarl', 'cabinet', 'scp', 'association', 'société']) and
                                        not any(word in potential_prenom.lower() for word in ['selarl', 'cabinet', 'scp', 'association', 'société'])):
                                        
                                        lawyer_info = {
                                            'nom': potential_nom.title(),
                                            'prenom': potential_prenom.title(), 
                                            'nom_complet': f"{potential_prenom.title()} {potential_nom.title()}",
                                            'email': email,
                                            'telephone': '',
                                            'ville': '',
                                            'annee_inscription': '',
                                            'ligne_source': line,
                                            'ligne_numero': line_num + 1,
                                            'pattern_utilise': 'supplementaire'
                                        }
                                        
                                        lawyers.append(lawyer_info)
                                        print(f"  + {len(lawyers):2d}. {potential_prenom.title()} {potential_nom.title()} - {email}")
                                        name_found = True
                                        break
                            
                            if name_found:
                                break
                        if name_found:
                            break
        
        print(f"\n✅ Total trouvé : {len(lawyers)} avocats")
        return lawyers
        
    def enhance_lawyer_data_from_web(self, lawyers):
        """Enrichit les données en consultant le site web si nécessaire"""
        print(f"\n🌐 Enrichissement des données via le site web...")
        
        if self.headless:
            print("Mode headless - enrichissement limité")
            return lawyers
            
        try:
            self.setup_driver()
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Accepter les cookies
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tout accepter')]"))
                )
                cookie_btn.click()
                time.sleep(2)
            except:
                pass
            
            # Pour chaque avocat sans informations complètes, essayer de les trouver
            enhanced_lawyers = []
            
            for i, lawyer in enumerate(lawyers):
                print(f"  Enrichissement {i+1}/{len(lawyers)}: {lawyer['nom_complet']}")
                
                # Si des informations manquent, chercher sur le site
                if not lawyer['telephone'] or not lawyer['ville']:
                    try:
                        # Effectuer une recherche du nom sur la page
                        page_source = self.driver.page_source.lower()
                        
                        name_variants = [
                            lawyer['nom'].lower(),
                            lawyer['prenom'].lower(),
                            lawyer['email'].split('@')[0].lower()
                        ]
                        
                        for variant in name_variants:
                            if variant in page_source and len(variant) > 3:
                                # Extraire contexte autour du nom
                                context_match = re.search(f'.{{0,300}}{re.escape(variant)}.{{0,300}}', page_source)
                                if context_match:
                                    context = context_match.group(0)
                                    
                                    # Chercher téléphone dans le contexte
                                    if not lawyer['telephone']:
                                        phone_match = re.search(r'(0[0-9][\d\.\s]{8,})', context)
                                        if phone_match:
                                            lawyer['telephone'] = phone_match.group(1).strip()
                                    
                                    # Chercher ville dans le contexte
                                    if not lawyer['ville']:
                                        city_patterns = [
                                            r'(bonneville|sallanches|cluses|saint-gervais|saint-pierre|la roche)',
                                        ]
                                        for pattern in city_patterns:
                                            city_match = re.search(pattern, context, re.IGNORECASE)
                                            if city_match:
                                                lawyer['ville'] = city_match.group(1).title()
                                                break
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
    
    def save_exhaustive_results(self, lawyers):
        """Sauvegarde les résultats exhaustifs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n💾 Sauvegarde des {len(lawyers)} avocats...")
        
        # CSV complet
        csv_filename = f"bonneville_EXHAUSTIF_{len(lawyers)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nom', 'prenom', 'nom_complet', 'email', 'telephone', 
                         'ville', 'annee_inscription', 'pattern_utilise', 'ligne_numero']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for lawyer in lawyers:
                clean_lawyer = {}
                for field in fieldnames:
                    value = lawyer.get(field, '')
                    if isinstance(value, str):
                        value = value.strip().replace('\n', ' ').replace('\t', ' ')
                        value = re.sub(r'\s+', ' ', value)
                    clean_lawyer[field] = value
                writer.writerow(clean_lawyer)
        
        # JSON complet
        json_filename = f"bonneville_EXHAUSTIF_{len(lawyers)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails uniquement
        emails_filename = f"bonneville_EMAILS_{len(lawyers)}_avocats_{timestamp}.txt"
        unique_emails = sorted(list(set([l['email'] for l in lawyers if l['email']])))
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in unique_emails:
                emailfile.write(f"{email}\n")
        
        # Rapport exhaustif
        report_filename = f"bonneville_RAPPORT_EXHAUSTIF_{len(lawyers)}_avocats_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as reportfile:
            reportfile.write(f"🏛️  EXTRACTION EXHAUSTIVE - BARREAU DE BONNEVILLE\n")
            reportfile.write("=" * 60 + "\n\n")
            
            reportfile.write(f"📅 Date extraction : {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            reportfile.write(f"🌐 Source : PDF Tableau de l'Ordre 2025\n\n")
            
            total = len(lawyers)
            emails = len([l for l in lawyers if l['email']])
            phones = len([l for l in lawyers if l['telephone']])
            cities = len([l for l in lawyers if l['ville']])
            years = len([l for l in lawyers if l['annee_inscription']])
            
            reportfile.write("📊 STATISTIQUES EXHAUSTIVES :\n")
            reportfile.write(f"   Total avocats trouvés : {total}\n")
            reportfile.write(f"   Avec email : {emails} ({emails/total*100:.1f}%)\n")
            reportfile.write(f"   Avec téléphone : {phones} ({phones/total*100:.1f}%)\n")
            reportfile.write(f"   Avec ville : {cities} ({cities/total*100:.1f}%)\n")
            reportfile.write(f"   Avec année : {years} ({years/total*100:.1f}%)\n\n")
            
            reportfile.write("📋 LISTE EXHAUSTIVE :\n")
            reportfile.write("-" * 50 + "\n")
            
            for i, lawyer in enumerate(lawyers, 1):
                reportfile.write(f"{i:2d}. {lawyer['nom_complet']}\n")
                reportfile.write(f"    📧 {lawyer['email']}\n")
                if lawyer['telephone']:
                    reportfile.write(f"    📞 {lawyer['telephone']}\n")
                if lawyer['ville']:
                    reportfile.write(f"    📍 {lawyer['ville']}\n")
                if lawyer['annee_inscription']:
                    reportfile.write(f"    📅 {lawyer['annee_inscription']}\n")
                reportfile.write(f"    🔍 Pattern: {lawyer['pattern_utilise']} (ligne {lawyer['ligne_numero']})\n\n")
        
        print(f"✅ Sauvegarde terminée !")
        print(f"\n📁 FICHIERS EXHAUSTIFS GÉNÉRÉS :")
        print(f"   • {csv_filename}")
        print(f"   • {json_filename}")  
        print(f"   • {emails_filename}")
        print(f"   • {report_filename}")
        
        return {
            'csv': csv_filename,
            'json': json_filename,
            'emails': emails_filename,
            'report': report_filename
        }
    
    def run_exhaustive_extraction(self):
        """Lance l'extraction exhaustive complète"""
        print("🚀 EXTRACTION EXHAUSTIVE - BARREAU DE BONNEVILLE")
        print("=" * 55)
        print("Objectif : Trouver TOUS les avocats (~60 attendus)")
        print("=" * 55)
        
        try:
            start_time = time.time()
            
            # 1. Télécharger et parser complètement le PDF
            pdf_text = self.download_and_parse_pdf_exhaustive()
            if not pdf_text:
                return False
            
            # 2. Parser exhaustivement tous les avocats
            all_lawyers = self.parse_all_lawyers_from_pdf(pdf_text)
            if not all_lawyers:
                print("❌ Aucun avocat trouvé dans le PDF")
                return False
                
            print(f"\n✅ PREMIÈRE PHASE : {len(all_lawyers)} avocats trouvés")
            
            # 3. Enrichir les données si possible
            enriched_lawyers = self.enhance_lawyer_data_from_web(all_lawyers)
            
            # 4. Sauvegarder tout
            files = self.save_exhaustive_results(enriched_lawyers)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n🎉 EXTRACTION EXHAUSTIVE TERMINÉE !")
            print(f"⏱️  Durée : {duration:.1f} secondes")
            print(f"📊 {len(enriched_lawyers)} avocats extraits")
            
            if len(enriched_lawyers) >= 50:
                print("✅ Objectif atteint : Plus de 50 avocats trouvés !")
            elif len(enriched_lawyers) >= 30:
                print("⚠️ Objectif partiellement atteint")
            else:
                print("❌ Objectif non atteint - investigation nécessaire")
                
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction exhaustive : {e}")
            return False

if __name__ == "__main__":
    # Lancement en mode headless par défaut
    scraper = BonnevilleExhaustiveScraper(headless=True)
    success = scraper.run_exhaustive_extraction()
    
    if not success:
        print("\n❌ ÉCHEC DE L'EXTRACTION EXHAUSTIVE")
        exit(1)
    else:
        print("\n✅ EXTRACTION EXHAUSTIVE RÉUSSIE !")
        print("📈 Vérifiez les fichiers générés pour voir tous les avocats trouvés")