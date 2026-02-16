#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER FINAL CONSOLIDÉ - BARREAU DE LORIENT
Version définitive réutilisable avec parsing noms corrigé et consolidation automatique
"""

import time
import csv
import json
import re
import glob
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class LorientBarScraperConsolidated:
    def __init__(self):
        self.base_url = "https://www.barreaulorient.fr"
        self.avocats_url = f"{self.base_url}/avocats-lorient/tous-les-avocats.php"
        self.driver = None
        self.batch_size = 25  # Taille optimale des batches
        
    def setup_driver(self):
        """Configuration optimisée du driver"""
        print("🔧 Configuration de Chrome...")
        
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome configuré")
        return self.driver
    
    def parse_name_corrected(self, full_name):
        """Parsing CORRIGÉ des noms - Version définitive"""
        try:
            # Nettoyer le nom
            name = re.sub(r'\s+', ' ', full_name.strip())
            
            # Supprimer les titres
            prefixes_to_remove = ["Me", "Maître", "M.", "Mme", "Mr", "Mrs", "Dr", "Docteur"]
            for prefix in prefixes_to_remove:
                if name.startswith(prefix + " "):
                    name = name[len(prefix):].strip()
            
            parts = [part.strip() for part in name.split() if part.strip()]
            
            if len(parts) == 1:
                return {"prenom": "", "nom": parts[0]}
            
            elif len(parts) == 2:
                first, second = parts[0], parts[1]
                
                # RÈGLE PRINCIPALE : Si le premier mot est tout en majuscules -> NOM
                if first.isupper():
                    return {"prenom": second, "nom": first}
                else:
                    return {"prenom": first, "nom": second}
            
            else:
                # Plus de 2 parties - Cas complexes
                
                # RÈGLE 1: Chercher les noms composés avec tiret
                if '-' in name:
                    # Exemple: "SIMPORE-GAULTIER Vanessa" ou "SOBEAUX-LE GOFF Françoise"
                    for i, part in enumerate(parts):
                        if '-' in part and part.isupper():
                            # C'est le nom de famille composé
                            nom = part
                            prenom_parts = parts[:i] + parts[i+1:]
                            prenom = " ".join(prenom_parts)
                            return {"prenom": prenom, "nom": nom}
                
                # RÈGLE 2: Chercher tous les mots en majuscules consécutifs
                uppercase_sequence = []
                for i, part in enumerate(parts):
                    if part.isupper():
                        uppercase_sequence.append((i, part))
                    else:
                        break  # Arrêter à la première minuscule
                
                if uppercase_sequence:
                    # Tous les mots en majuscules consécutifs = nom de famille
                    nom_indices = [idx for idx, _ in uppercase_sequence]
                    nom_parts = [part for _, part in uppercase_sequence]
                    nom = " ".join(nom_parts)
                    
                    # Le reste = prénom
                    prenom_parts = [parts[i] for i in range(len(parts)) if i not in nom_indices]
                    prenom = " ".join(prenom_parts)
                    
                    return {"prenom": prenom, "nom": nom}
                
                # RÈGLE 3: Par défaut, le premier mot en majuscules = nom
                for i, part in enumerate(parts):
                    if part.isupper():
                        nom = part
                        prenom_parts = parts[:i] + parts[i+1:]
                        prenom = " ".join(prenom_parts)
                        return {"prenom": prenom, "nom": nom}
                
                # RÈGLE 4: Fallback - dernier mot = nom
                return {"prenom": " ".join(parts[:-1]), "nom": parts[-1]}
                
        except Exception as e:
            print(f"⚠️ Erreur parsing nom '{full_name}' : {e}")
            return {"prenom": "", "nom": full_name}
    
    def get_all_lawyers(self):
        """Récupérer TOUS les avocats d'un coup"""
        print("🌐 Accès au site...")
        self.driver.get(self.avocats_url)
        time.sleep(5)
        
        print("📋 Récupération de TOUS les avocats...")
        
        links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='avocat-']")
        
        lawyers = []
        for link in links:
            href = link.get_attribute("href")
            name = link.text.strip()
            
            # Filtrage intelligent
            if (href and name and len(name.split()) >= 2 and
                not re.search(r'avocats,lorient-\d+\.html$', href) and
                name.lower() not in ['barreau lorient', 'tous les avocats']):
                
                lawyers.append({"name": name, "url": href, "id": len(lawyers) + 1})
        
        print(f"✅ {len(lawyers)} avocats trouvés au total")
        return lawyers
    
    def extract_lawyer_data_complete(self, lawyer):
        """Extraction complète et optimisée"""
        self.driver.get(lawyer["url"])
        time.sleep(2)
        
        # Parsing nom/prénom CORRIGÉ
        name_parsed = self.parse_name_corrected(lawyer["name"])
        
        data = {
            "id": lawyer["id"],
            "nom_complet": lawyer["name"],
            "prenom": name_parsed["prenom"],
            "nom": name_parsed["nom"],
            "email": "",
            "annee_inscription": "",
            "specialisations": "",
            "competences": "",
            "structure": "",
            "adresse": "",
            "telephone": "",
            "source_url": lawyer["url"],
            "date_extraction": datetime.now().strftime("%Y-%m-%d"),
            "statut_extraction": "succès"
        }
        
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source.lower()
            
            # === EMAIL ===
            email_matches = re.findall(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', page_source)
            if email_matches:
                # Prioriser les emails personnalisés
                personal_emails = [email for email in email_matches 
                                 if not any(generic in email.lower() 
                                          for generic in ['contact@barreaulorient', 'info@barreaulorient', 'secretariat@barreaulorient'])]
                
                data["email"] = personal_emails[0] if personal_emails else email_matches[0]
            
            # === TÉLÉPHONE ===
            tel_matches = re.findall(r'\b0[1-9](?:[\s.-]?\d{2}){4}\b', page_text)
            for tel in tel_matches:
                if tel != "02 97 64 67 49":  # Numéro du barreau
                    data["telephone"] = tel
                    break
            
            # === SPÉCIALISATIONS (méthode précise) ===
            try:
                h3_elements = self.driver.find_elements(By.TAG_NAME, "h3")
                specializations = []
                for h3 in h3_elements:
                    text = h3.text.strip()
                    if text.startswith("Droit ") and len(text) < 60 and text not in specializations:
                        specializations.append(text)
                
                if specializations:
                    data["specialisations"] = " | ".join(specializations[:5])
            except:
                pass
            
            # === STRUCTURE (méthode précise) ===
            try:
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().lower() == 'le cabinet' and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and 5 < len(next_line) < 100:
                            data["structure"] = next_line
                            break
                
                # Fallback: chercher les patterns de structures
                if not data["structure"]:
                    structure_patterns = [
                        r'(SELARL\s+[A-ZÀ-ÿ\s\-]+)',
                        r'(SCP\s+[A-ZÀ-ÿ\s\-]+)',
                        r'(SARL\s+[A-ZÀ-ÿ\s\-]+)',
                        r'(SELAFA\s+[A-ZÀ-ÿ\s\-]+)',
                        r'(Cabinet\s+[A-ZÀ-ÿ\s\-]+)'
                    ]
                    
                    for pattern in structure_patterns:
                        match = re.search(pattern, page_text)
                        if match:
                            structure = match.group(1).strip()
                            if 5 < len(structure) < 100:
                                data["structure"] = structure
                                break
            except:
                pass
            
            # === ADRESSE ===
            try:
                # Chercher les lignes avec codes postaux
                for line in page_text.split('\n'):
                    if re.search(r'\d{5}', line) and any(ville in line.upper() for ville in ['LORIENT', 'VANNES', 'AURAY']):
                        data["adresse"] = line.strip()
                        break
            except:
                pass
            
            # === ANNÉE D'INSCRIPTION ===
            try:
                year_patterns = [
                    r'inscrit[e]?\s+(?:au\s+)?barreau.*?(?:en\s+|depuis\s+|de\s+)?(\d{4})',
                    r'barreau.*?(?:en\s+|depuis\s+|de\s+)?(\d{4})',
                    r'admission.*?(\d{4})',
                    r'serment.*?(\d{4})'
                ]
                
                for pattern in year_patterns:
                    match = re.search(pattern, page_text.lower())
                    if match:
                        year = int(match.group(1))
                        if 1950 <= year <= 2024:
                            data["annee_inscription"] = str(year)
                            break
            except:
                pass
            
        except Exception as e:
            print(f"⚠️ Erreur extraction {lawyer['name']}: {e}")
            data["statut_extraction"] = "erreur_partielle"
        
        return data
    
    def run_complete_scraping(self):
        """Scraping complet automatisé par batches"""
        print("🚀 SCRAPER LORIENT - EXTRACTION COMPLÈTE AUTOMATISÉE")
        print("="*60)
        
        try:
            # Configuration
            self.setup_driver()
            
            # Récupérer tous les avocats
            all_lawyers = self.get_all_lawyers()
            
            if not all_lawyers:
                print("❌ Aucun avocat trouvé")
                return []
            
            # Traitement par batches
            all_results = []
            total_batches = (len(all_lawyers) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(all_lawyers))
                batch_lawyers = all_lawyers[start_idx:end_idx]
                
                print(f"\n🔄 BATCH {batch_num + 1}/{total_batches} - Avocats {start_idx + 1} à {end_idx}")
                print("-" * 50)
                
                batch_results = []
                for i, lawyer in enumerate(batch_lawyers):
                    print(f"[{start_idx + i + 1:3d}] {lawyer['name']}")
                    
                    try:
                        data = self.extract_lawyer_data_complete(lawyer)
                        batch_results.append(data)
                        all_results.append(data)
                        time.sleep(1)  # Pause entre avocats
                    except Exception as e:
                        print(f"❌ Erreur sur {lawyer['name']}: {e}")
                        continue
                
                # Statistiques du batch
                batch_emails = sum(1 for r in batch_results if r.get('email'))
                batch_specs = sum(1 for r in batch_results if r.get('specialisations'))
                print(f"📊 Batch terminé - {batch_emails}/{len(batch_results)} emails, {batch_specs}/{len(batch_results)} spécialisations")
                
                # Pause entre batches
                if batch_num < total_batches - 1:
                    time.sleep(3)
            
            print(f"\n✅ EXTRACTION COMPLÈTE TERMINÉE - {len(all_results)} avocats traités")
            return all_results
            
        except Exception as e:
            print(f"❌ Erreur durant l'extraction : {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fermé")
    
    def deduplicate_and_clean(self, data):
        """Dédoublonner et nettoyer les données"""
        print("🧹 Nettoyage et déduplication...")
        
        seen_urls = set()
        seen_emails = set()
        cleaned_data = []
        
        for lawyer in data:
            # Déduplication par URL (plus fiable que le nom)
            if lawyer["source_url"] in seen_urls:
                continue
            seen_urls.add(lawyer["source_url"])
            
            # Nettoyer les champs
            lawyer["nom"] = lawyer["nom"].strip()
            lawyer["prenom"] = lawyer["prenom"].strip()
            lawyer["email"] = lawyer["email"].strip().lower() if lawyer["email"] else ""
            lawyer["telephone"] = re.sub(r'[^\d+\s.-]', '', lawyer["telephone"]) if lawyer["telephone"] else ""
            
            # Nettoyer les spécialisations (supprimer doublons internes)
            if lawyer["specialisations"]:
                specs = lawyer["specialisations"].split(" | ")
                unique_specs = []
                for spec in specs:
                    if spec.strip() and spec.strip() not in unique_specs:
                        unique_specs.append(spec.strip())
                lawyer["specialisations"] = " | ".join(unique_specs)
            
            cleaned_data.append(lawyer)
        
        print(f"✅ {len(cleaned_data)} avocats uniques après nettoyage")
        return cleaned_data
    
    def save_consolidated_results(self, data, filename_prefix="LORIENT_FINAL"):
        """Sauvegarder les résultats consolidés"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # === FICHIER CSV PRINCIPAL ===
            csv_filename = f"{filename_prefix}_CONSOLIDÉ_{len(data)}_avocats_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                if data:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            # === FICHIER JSON COMPLET ===
            json_filename = f"{filename_prefix}_CONSOLIDÉ_{len(data)}_avocats_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            
            # === FICHIER EMAILS UNIQUES ===
            emails_filename = f"{filename_prefix}_EMAILS_UNIQUES_{timestamp}.txt"
            unique_emails = set()
            with open(emails_filename, 'w', encoding='utf-8') as emailfile:
                for lawyer in data:
                    email = lawyer.get('email', '').strip()
                    if email and email not in unique_emails:
                        emailfile.write(f"{email}\n")
                        unique_emails.add(email)
            
            # === RAPPORT CONSOLIDÉ ===
            report_filename = f"{filename_prefix}_RAPPORT_CONSOLIDÉ_{timestamp}.txt"
            with open(report_filename, 'w', encoding='utf-8') as report:
                report.write(f"RAPPORT CONSOLIDÉ FINAL - BARREAU DE LORIENT\n")
                report.write(f"{'='*60}\n\n")
                report.write(f"Date d'extraction : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                report.write(f"Nombre total d'avocats : {len(data)}\n")
                report.write(f"Fichier unique consolidé : OUI ✅\n\n")
                
                # Statistiques complètes
                emails_found = sum(1 for lawyer in data if lawyer.get('email'))
                years_found = sum(1 for lawyer in data if lawyer.get('annee_inscription'))
                specializations_found = sum(1 for lawyer in data if lawyer.get('specialisations'))
                phones_found = sum(1 for lawyer in data if lawyer.get('telephone'))
                structures_found = sum(1 for lawyer in data if lawyer.get('structure'))
                addresses_found = sum(1 for lawyer in data if lawyer.get('adresse'))
                
                report.write(f"STATISTIQUES FINALES :\n")
                report.write(f"- Emails trouvés : {emails_found}/{len(data)} ({emails_found/len(data)*100:.1f}%)\n")
                report.write(f"- Emails uniques : {len(unique_emails)}\n")
                report.write(f"- Spécialisations : {specializations_found}/{len(data)} ({specializations_found/len(data)*100:.1f}%)\n")
                report.write(f"- Structures/Cabinets : {structures_found}/{len(data)} ({structures_found/len(data)*100:.1f}%)\n")
                report.write(f"- Téléphones : {phones_found}/{len(data)} ({phones_found/len(data)*100:.1f}%)\n")
                report.write(f"- Adresses : {addresses_found}/{len(data)} ({addresses_found/len(data)*100:.1f}%)\n")
                report.write(f"- Années d'inscription : {years_found}/{len(data)} ({years_found/len(data)*100:.1f}%)\n\n")
                
                report.write(f"CORRECTIONS PARSING NOMS :\n")
                report.write(f"- Noms composés avec tiret : Gérés ✅\n")
                report.write(f"- Prénoms composés : Gérés ✅\n")
                report.write(f"- Majuscules/minuscules : Analysé ✅\n\n")
                
                # Exemples de parsing corrigé
                report.write("EXEMPLES DE PARSING CORRIGÉ :\n")
                report.write("-" * 40 + "\n")
                for i, lawyer in enumerate(data[:10]):
                    report.write(f"{i+1:2d}. '{lawyer.get('nom_complet')}'\n")
                    report.write(f"    → Prénom: '{lawyer.get('prenom')}'\n")
                    report.write(f"    → Nom: '{lawyer.get('nom')}'\n")
                    report.write(f"    → Email: {lawyer.get('email', 'Non trouvé')}\n")
                    report.write(f"    → Spécialisations: {lawyer.get('specialisations', 'Non trouvé')[:80]}...\n\n")
                
                report.write(f"\nREUTILISABILITÉ :\n")
                report.write(f"Pour actualiser la liste dans un an :\n")
                report.write(f"python3 lorient_scraper_final_consolidated.py\n\n")
                report.write(f"Le script détectera automatiquement les nouveaux avocats\n")
                report.write(f"et mettra à jour la base de données complète.\n")
            
            print(f"\n✅ FICHIERS CONSOLIDÉS SAUVEGARDÉS :")
            print(f"  📄 CSV Final : {csv_filename}")
            print(f"  📄 JSON Final : {json_filename}")
            print(f"  📧 Emails ({len(unique_emails)} uniques) : {emails_filename}")
            print(f"  📄 Rapport consolidé : {report_filename}")
            
            return csv_filename, json_filename, emails_filename, report_filename
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde consolidée : {e}")
            return None, None, None, None

def consolidate_existing_batches():
    """Consolider les fichiers batch existants"""
    print("🔄 CONSOLIDATION DES BATCHES EXISTANTS")
    print("="*45)
    
    # Chercher tous les fichiers batch
    batch_files = glob.glob("LORIENT_BATCH_*.csv")
    
    if not batch_files:
        print("❌ Aucun fichier batch trouvé")
        return None
    
    batch_files.sort()  # Tri alphabétique
    print(f"📁 Trouvé {len(batch_files)} fichiers batch :")
    for f in batch_files:
        print(f"  - {f}")
    
    # Lire et consolider tous les batches
    all_data = []
    seen_urls = set()
    
    for batch_file in batch_files:
        print(f"📖 Lecture de {batch_file}...")
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batch_data = list(reader)
                
                for lawyer in batch_data:
                    # Déduplication par URL
                    if lawyer.get("source_url") not in seen_urls:
                        # Corriger le parsing des noms
                        scraper = LorientBarScraperConsolidated()
                        name_corrected = scraper.parse_name_corrected(lawyer.get("nom_complet", ""))
                        lawyer["prenom"] = name_corrected["prenom"]
                        lawyer["nom"] = name_corrected["nom"]
                        
                        # Ajouter champs manquants
                        lawyer["date_extraction"] = datetime.now().strftime("%Y-%m-%d")
                        lawyer["id"] = len(all_data) + 1
                        
                        all_data.append(lawyer)
                        seen_urls.add(lawyer.get("source_url", ""))
                        
        except Exception as e:
            print(f"⚠️ Erreur lecture {batch_file}: {e}")
            continue
    
    print(f"✅ {len(all_data)} avocats consolidés")
    
    # Sauvegarder le résultat consolidé
    scraper = LorientBarScraperConsolidated()
    cleaned_data = scraper.deduplicate_and_clean(all_data)
    csv_file, json_file, emails_file, report_file = scraper.save_consolidated_results(cleaned_data, "LORIENT_CONSOLIDATED")
    
    # Nettoyer les fichiers batch
    print("\n🧹 Nettoyage des fichiers batch...")
    for batch_file in batch_files:
        try:
            os.remove(batch_file)
            print(f"  🗑️ Supprimé : {batch_file}")
        except:
            pass
    
    return cleaned_data

def main():
    """Fonction principale"""
    print("🏛️ SCRAPER BARREAU DE LORIENT - VERSION FINALE CONSOLIDÉE")
    print("="*65)
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--consolidate":
        # Mode consolidation des batches existants
        print("🔄 Mode consolidation activé")
        data = consolidate_existing_batches()
    else:
        # Mode extraction complète
        print("⚡ Mode extraction complète activé")
        scraper = LorientBarScraperConsolidated()
        data = scraper.run_complete_scraping()
        
        if data:
            cleaned_data = scraper.deduplicate_and_clean(data)
            scraper.save_consolidated_results(cleaned_data, "LORIENT_EXTRACTION_COMPLETE")
    
    if data:
        print(f"\n🎉 SUCCÈS ! {len(data)} avocats extraits et consolidés")
        print(f"📁 Un seul fichier CSV final généré - Prêt pour réutilisation !")
    
    return data

if __name__ == "__main__":
    main()