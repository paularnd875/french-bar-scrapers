#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import csv
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

class SablesOlonneLawyerScraperFinalCorrected:
    def __init__(self, headless=True):
        """Initialise le scraper avec configuration améliorée - VERSION CORRIGÉE SPÉCIALISATIONS"""
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
            
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        
        print("✅ Scraper corrigé initialisé avec succès")

    def accept_cookies(self):
        """Accepte les cookies de manière robuste"""
        try:
            cookie_selectors = [
                "button[onclick*='accepter']",
                "button[onclick*='accept']", 
                ".cookie-accept",
                "#cookie-accept"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    cookie_button.click()
                    print("✅ Cookies acceptés")
                    time.sleep(2)
                    return True
                except:
                    continue
            
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if any(word in button.text.lower() for word in ['accepter', 'accept', 'ok']):
                        button.click()
                        print("✅ Cookies acceptés (méthode texte)")
                        time.sleep(2)
                        return True
            except:
                pass
                
            print("⚠️ Aucun bouton de cookies trouvé, continue...")
            return True
            
        except Exception as e:
            print(f"⚠️ Erreur cookies (non bloquante): {e}")
            return True

    def extract_lawyer_basic_info(self):
        """Extrait les informations de base de tous les avocats"""
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "annuaireFicheMiniAvocat")))
            
            lawyer_cards = self.driver.find_elements(By.CLASS_NAME, "annuaireFicheMiniAvocat")
            print(f"🔍 {len(lawyer_cards)} avocats trouvés sur la page")
            
            lawyers_info = []
            
            for i, card in enumerate(lawyer_cards, 1):
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, "h4 > a")
                    lawyer_url = link_element.get_attribute('href')
                    
                    spans = card.find_elements(By.TAG_NAME, "span")
                    prenom = ""
                    nom = ""
                    
                    for span in spans:
                        class_name = span.get_attribute('class') or ""
                        text = span.text.strip()
                        
                        if 'prenom' in class_name.lower() and text:
                            prenom = text
                        elif 'nom' in class_name.lower() and text:
                            nom = text
                    
                    if not prenom and not nom:
                        full_text = link_element.text.strip()
                        if full_text and full_text != "Maître":
                            parts = full_text.split()
                            if len(parts) >= 2:
                                prenom = " ".join(parts[:-1])
                                nom = parts[-1]
                            elif len(parts) == 1:
                                nom = parts[0]
                    
                    if lawyer_url and (prenom or nom):
                        lawyer_info = {
                            'prenom': prenom,
                            'nom': nom,
                            'url': lawyer_url
                        }
                        lawyers_info.append(lawyer_info)
                        print(f"✅ Avocat {i}: {prenom} {nom}")
                    
                except Exception as e:
                    print(f"⚠️ Erreur avocat {i}: {e}")
                    continue
            
            print(f"📊 Total avocats extraits: {len(lawyers_info)}")
            return lawyers_info
            
        except Exception as e:
            print(f"❌ Erreur extraction de base: {e}")
            return []

    def extract_specializations(self, page_text, lines):
        """Extrait les spécialisations avec filtrage amélioré"""
        specializations = []
        
        try:
            # Méthode 1: Chercher "SPÉCIALITÉS" et récupérer ce qui suit
            for i, line in enumerate(lines):
                line_clean = line.strip()
                if line_clean.upper() in ['SPÉCIALITÉS', 'SPECIALITES', 'SPÉCIALITÉ', 'SPECIALITE']:
                    print(f"🎯 Section spécialisations trouvée")
                    
                    # Récupérer les lignes suivantes qui sont des spécialisations
                    for j in range(i + 1, min(i + 10, len(lines))):
                        next_line = lines[j].strip()
                        
                        if next_line and len(next_line) > 3:
                            # Filtres pour exclure les éléments parasites
                            exclude_patterns = [
                                # Formulaire de contact
                                r'contacter', r'j\'accepte', r'envoyer', r'champs', 
                                r'astérisque', r'obligatoire', r'conformément',
                                # Coordonnées
                                r'rue ', r'avenue ', r'boulevard ', r'place ',
                                r'\d{5}', r'tél\s*:', r'fax\s*:', r'email',
                                r'@', r'\+33', r'\d{10}',
                                # Navigation
                                r'ordre des avocats', r'barreau', r'mentions légales',
                                r'contact', r'espace avocat', r'annuaire',
                                # Mots seuls sans contexte
                                r'^cabinet$', r'^avocat$', r'^maître$'
                            ]
                            
                            # Vérifier si la ligne doit être exclue
                            should_exclude = any(re.search(pattern, next_line.lower()) for pattern in exclude_patterns)
                            
                            if not should_exclude:
                                # Vérifier si c'est une vraie spécialisation
                                valid_spec_patterns = [
                                    r'droit\s+(civil|pénal|commercial|du travail|de la famille|immobilier|fiscal|social|public|administratif)',
                                    r'(divorce|succession|contrat|responsabilité|contentieux)',
                                    r'(médiation|arbitrage|négociation)',
                                    r'droit\s+(des affaires|bancaire|boursier|de la consommation)',
                                    r'(propriété intellectuelle|nouvelles technologies)',
                                    r'droit\s+(international|européen)',
                                    r'(urbanisme|environnement|construction)'
                                ]
                                
                                # Si c'est court et contient des mots-clés juridiques, c'est probablement une spécialisation
                                is_legal_domain = any(re.search(pattern, next_line.lower()) for pattern in valid_spec_patterns)
                                is_short_and_relevant = len(next_line.split()) <= 5 and any(word in next_line.lower() for word in ['droit', 'civil', 'pénal', 'commercial', 'travail', 'famille', 'immobilier', 'fiscal', 'social'])
                                
                                if is_legal_domain or is_short_and_relevant:
                                    specializations.append(next_line)
                                    print(f"  ✅ Spécialisation: {next_line}")
                                else:
                                    # Si on arrive à une ligne qui n'est clairement pas une spécialisation, on s'arrête
                                    if len(next_line) > 50 or any(word in next_line.lower() for word in ['les sables', 'bp ', 'cedex', 'france']):
                                        break
                    break
            
            # Méthode 2: Si pas trouvé par "SPÉCIALITÉS", chercher directement les domaines
            if not specializations:
                print("🔍 Recherche directe des domaines de droit...")
                direct_spec_patterns = [
                    r'droit\s+(civil|pénal|commercial|du travail|de la famille|immobilier|fiscal|social|public)',
                    r'(divorce|succession|contrat|responsabilité|contentieux)'
                ]
                
                for line in lines:
                    line_clean = line.strip()
                    if line_clean and 5 < len(line_clean) < 100:
                        for pattern in direct_spec_patterns:
                            if re.search(pattern, line_clean.lower()):
                                if line_clean not in specializations:
                                    specializations.append(line_clean)
                                    print(f"  ✅ Spécialisation directe: {line_clean}")
            
            # Nettoyer et déduplicuer
            clean_specs = []
            for spec in specializations:
                if spec and spec not in clean_specs:
                    # Dernière vérification pour éviter les doublons évidents
                    if not any(existing in spec or spec in existing for existing in clean_specs):
                        clean_specs.append(spec)
            
            return clean_specs
            
        except Exception as e:
            print(f"⚠️ Erreur extraction spécialisations: {e}")
            return []

    def extract_detailed_info(self, lawyer_info):
        """Extrait les informations détaillées d'un avocat depuis sa page individuelle"""
        try:
            print(f"🔍 Extraction détails: {lawyer_info['prenom']} {lawyer_info['nom']}")
            
            self.driver.get(lawyer_info['url'])
            time.sleep(2)
            
            lawyer_data = {
                'prenom': lawyer_info['prenom'],
                'nom': lawyer_info['nom'],
                'email': '',
                'annee_inscription': '',
                'specialisations': '',
                'structure': '',
                'cabinet': '',
                'url': lawyer_info['url']
            }
            
            # Récupérer le texte de la page une seule fois
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = page_text.split('\n')
            
            # EXTRACTION EMAIL
            try:
                page_source = self.driver.page_source
                # Pattern pour emails normaux ET encodés en URL
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z0-9]{2,}\b'
                emails = re.findall(email_pattern, page_source)
                
                valid_emails = []
                for email in emails:
                    if not email.endswith(('.png', '.jpg', '.gif', '.css', '.js')):
                        # Décoder l'email s'il est encodé en URL
                        try:
                            from urllib.parse import unquote
                            decoded_email = unquote(email)
                            valid_emails.append(decoded_email)
                        except:
                            valid_emails.append(email)
                
                if valid_emails:
                    # Prendre le premier email valide et s'assurer qu'il est bien décodé
                    best_email = valid_emails[0]
                    # Vérification finale pour s'assurer que l'email est correct
                    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', best_email):
                        lawyer_data['email'] = best_email
                        print(f"✅ Email: {best_email}")
                    else:
                        # Si toujours encodé, essayer une autre approche
                        clean_email = best_email.replace('%40', '@').replace('%2E', '.')
                        # Décoder manuellement les caractères courants
                        clean_email = re.sub(r'%([0-9A-Fa-f]{2})', lambda m: chr(int(m.group(1), 16)), clean_email)
                        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', clean_email):
                            lawyer_data['email'] = clean_email
                            print(f"✅ Email (décodé): {clean_email}")
                        else:
                            print(f"⚠️ Email problématique: {best_email}")
            except Exception as e:
                print(f"⚠️ Erreur email: {e}")
            
            # EXTRACTION ANNÉE D'INSCRIPTION
            try:
                year_patterns = [
                    r'prestation.*?serment.*?(\d{4})',
                    r'inscrit.*?(\d{4})',
                    r'barreau.*?(\d{4})',
                    r'serment.*?(\d{4})',
                    r'inscription.*?(\d{4})'
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, page_text.lower())
                    for match in matches:
                        year = int(match)
                        if 1950 <= year <= 2025:
                            lawyer_data['annee_inscription'] = str(year)
                            print(f"✅ Année: {year}")
                            break
                    if lawyer_data['annee_inscription']:
                        break
                        
            except Exception as e:
                print(f"⚠️ Erreur année: {e}")
            
            # EXTRACTION CABINET/STRUCTURE
            try:
                h4_elements = self.driver.find_elements(By.TAG_NAME, "h4")
                for h4 in h4_elements:
                    h4_text = h4.text.strip()
                    if h4_text and len(h4_text) > 5:
                        cabinet_indicators = ['cabinet', 'scp', 'selarl', 'sarl', 'associés', 'société', 'avocats']
                        if any(indicator in h4_text.lower() for indicator in cabinet_indicators):
                            if len(h4_text) < 150 and '@' not in h4_text:
                                lawyer_data['structure'] = h4_text
                                lawyer_data['cabinet'] = h4_text
                                print(f"✅ Cabinet (h4): {h4_text}")
                                break
                
                # Si pas trouvé, chercher alternatives
                if not lawyer_data['cabinet']:
                    for line in lines:
                        line_clean = line.strip()
                        if line_clean and len(line_clean) > 8:
                            cabinet_indicators = ['cabinet', 'scp', 'selarl', 'sarl', 'associés', 'société']
                            if any(indicator in line_clean.lower() for indicator in cabinet_indicators):
                                if '@' not in line_clean and len(line_clean) < 150:
                                    if not any(word in line_clean.lower() for word in ['avocat au', 'membre', 'inscrit', 'barreau de']):
                                        lawyer_data['structure'] = line_clean
                                        lawyer_data['cabinet'] = line_clean
                                        print(f"✅ Cabinet (texte): {line_clean}")
                                        break
                
                if not lawyer_data['cabinet']:
                    for line in lines:
                        line_clean = line.strip()
                        if 'AVOCATS' in line_clean.upper() and len(line_clean) > 10 and len(line_clean) < 100:
                            if '@' not in line_clean:
                                lawyer_data['structure'] = line_clean
                                lawyer_data['cabinet'] = line_clean
                                print(f"✅ Cabinet (AVOCATS): {line_clean}")
                                break
                
                if not lawyer_data['cabinet']:
                    print("⚠️ Pas de cabinet trouvé")
                    
            except Exception as e:
                print(f"⚠️ Erreur cabinet: {e}")
            
            # EXTRACTION SPÉCIALISATIONS - VERSION CORRIGÉE
            try:
                specializations = self.extract_specializations(page_text, lines)
                
                if specializations:
                    lawyer_data['specialisations'] = '; '.join(specializations)
                    print(f"✅ Spécialisations: {lawyer_data['specialisations']}")
                else:
                    print("❌ Aucune spécialisation trouvée")
                    
            except Exception as e:
                print(f"⚠️ Erreur spécialisations: {e}")
            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur extraction détaillée: {e}")
            return lawyer_info

    def scrape_all_lawyers(self, max_lawyers=None):
        """Scrape tous les avocats avec informations détaillées"""
        try:
            print("🚀 Début du scraping Sables d'Olonne - VERSION CORRIGÉE SPÉCIALISATIONS")
            
            self.driver.get("https://www.barreaudessablesdolonne.fr/annuaire-des-avocats/liste-des-avocats.htm")
            time.sleep(3)
            
            self.accept_cookies()
            
            lawyers_basic = self.extract_lawyer_basic_info()
            if not lawyers_basic:
                print("❌ Aucun avocat trouvé")
                return []
            
            if max_lawyers:
                lawyers_basic = lawyers_basic[:max_lawyers]
                print(f"🔬 Mode test: extraction de {max_lawyers} avocats")
            
            all_lawyers = []
            total = len(lawyers_basic)
            
            for i, lawyer_basic in enumerate(lawyers_basic, 1):
                print(f"\n{'='*60}")
                print(f"📋 AVOCAT {i}/{total}")
                print(f"{'='*60}")
                
                try:
                    detailed_info = self.extract_detailed_info(lawyer_basic)
                    all_lawyers.append(detailed_info)
                    
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"❌ Erreur avocat {i}: {e}")
                    continue
            
            return all_lawyers
            
        except Exception as e:
            print(f"❌ Erreur globale: {e}")
            return []

    def save_results(self, lawyers_data, prefix="SABLES_OLONNE_CORRIGE"):
        """Sauvegarde les résultats en CSV et JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_filename = f"{prefix}_{len(lawyers_data)}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['prenom', 'nom', 'email', 'annee_inscription', 'specialisations', 'structure', 'cabinet', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(lawyers_data)
        
        # JSON
        json_filename = f"{prefix}_{len(lawyers_data)}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        # Emails
        emails = [lawyer['email'] for lawyer in lawyers_data if lawyer.get('email')]
        emails_filename = f"{prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as emailfile:
            for email in emails:
                emailfile.write(f"{email}\n")
        
        # Rapport détaillé
        rapport_filename = f"{prefix}_RAPPORT_COMPLET_{timestamp}.txt"
        with open(rapport_filename, 'w', encoding='utf-8') as rapport:
            rapport.write(f"RAPPORT EXTRACTION BARREAU SABLES D'OLONNE - VERSION CORRIGÉE\n")
            rapport.write(f"{'='*70}\n\n")
            rapport.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            rapport.write(f"Total avocats extraits: {len(lawyers_data)}\n")
            rapport.write(f"Emails trouvés: {len(emails)} ({len(emails)/len(lawyers_data)*100:.1f}%)\n")
            
            years_found = len([l for l in lawyers_data if l.get('annee_inscription')])
            cabinets_found = len([l for l in lawyers_data if l.get('cabinet')])
            specs_found = len([l for l in lawyers_data if l.get('specialisations')])
            
            rapport.write(f"Années d'inscription: {years_found} ({years_found/len(lawyers_data)*100:.1f}%)\n")
            rapport.write(f"Cabinets/Structures: {cabinets_found} ({cabinets_found/len(lawyers_data)*100:.1f}%)\n")
            rapport.write(f"Spécialisations: {specs_found} ({specs_found/len(lawyers_data)*100:.1f}%)\n\n")
            
            # Détail des spécialisations trouvées
            rapport.write(f"DÉTAIL DES SPÉCIALISATIONS:\n")
            rapport.write(f"-" * 30 + "\n")
            for lawyer in lawyers_data:
                if lawyer.get('specialisations'):
                    rapport.write(f"{lawyer['prenom']} {lawyer['nom']}: {lawyer['specialisations']}\n")
            
            rapport.write(f"\nFichiers générés:\n")
            rapport.write(f"- CSV: {csv_filename}\n")
            rapport.write(f"- JSON: {json_filename}\n")
            rapport.write(f"- Emails: {emails_filename}\n")
            rapport.write(f"- Rapport: {rapport_filename}\n")
        
        print(f"\n💾 Résultats sauvegardés:")
        print(f"   📊 CSV: {csv_filename}")
        print(f"   📋 JSON: {json_filename}")
        print(f"   📧 Emails: {emails_filename}")
        print(f"   📄 Rapport: {rapport_filename}")
        
        return csv_filename, json_filename, emails_filename, rapport_filename

    def close(self):
        """Ferme le navigateur"""
        self.driver.quit()
        print("✅ Navigateur fermé")

def main():
    """Fonction principale - Production corrigée"""
    scraper = SablesOlonneLawyerScraperFinalCorrected(headless=True)
    
    try:
        lawyers_data = scraper.scrape_all_lawyers()
        
        if lawyers_data:
            files = scraper.save_results(lawyers_data)
            
            print(f"\n🎉 EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print(f"📊 {len(lawyers_data)} avocats extraits")
            print(f"📧 {len([l for l in lawyers_data if l.get('email')])} emails récupérés")
            print(f"🏢 {len([l for l in lawyers_data if l.get('cabinet')])} cabinets identifiés")
            print(f"⚖️ {len([l for l in lawyers_data if l.get('specialisations')])} avocats avec spécialisations")
            
        else:
            print("❌ Aucun résultat obtenu")
            
    finally:
        scraper.close()

def test_mode():
    """Mode test sur quelques avocats incluant Liliane BARRE"""
    scraper = SablesOlonneLawyerScraperFinalCorrected(headless=False)
    
    try:
        # Test sur 10 avocats pour avoir plus de chances d'avoir des spécialisations
        lawyers_data = scraper.scrape_all_lawyers(max_lawyers=10)
        
        if lawyers_data:
            files = scraper.save_results(lawyers_data, prefix="SABLES_OLONNE_TEST_CORRIGE")
            print(f"\n🧪 TEST TERMINÉ: {len(lawyers_data)} avocats testés")
            
            with_specs = [l for l in lawyers_data if l.get('specialisations')]
            print(f"⚖️ Avocats avec spécialisations: {len(with_specs)}")
            
            for lawyer in with_specs:
                print(f"\n👤 {lawyer['prenom']} {lawyer['nom']}")
                print(f"   📧 Email: {lawyer.get('email', 'Non trouvé')}")
                print(f"   📅 Année: {lawyer.get('annee_inscription', 'Non trouvé')}")
                print(f"   🏢 Cabinet: {lawyer.get('cabinet', 'Non trouvé')}")
                print(f"   ⚖️ Spécialisations: {lawyer.get('specialisations', 'Non trouvé')}")
        else:
            print("❌ Aucun résultat de test")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 MODE TEST CORRIGÉ ACTIVÉ")
        test_mode()
    else:
        print("🚀 MODE PRODUCTION CORRIGÉ")
        main()