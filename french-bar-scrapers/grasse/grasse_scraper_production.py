#!/usr/bin/env python3
"""
SCRAPER PRODUCTION - BARREAU DE GRASSE
Script final pour extraire TOUS les avocats en mode headless (sans interface)
Toutes les données : prénom, nom, email, téléphone, spécialisations, adresse, etc.
"""

import time
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class GrasseProductionScraper:
    def __init__(self):
        self.setup_driver()
        self.lawyers_data = []
        self.base_url = "https://www.avocats-grasse.com/fr/annuaire-avocats"
        
    def setup_driver(self):
        """Configuration du driver Chrome en mode headless"""
        chrome_options = Options()
        
        # Mode headless et optimisations
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        
        print("🤖 Driver Chrome configuré en mode headless")
        
    def accept_cookies_if_present(self):
        """Accepter les cookies si la bannière est présente"""
        try:
            cookie_selectors = [
                "button[id*='cookie']",
                "button[class*='cookie']", 
                "button[id*='accept']",
                "button[class*='accept']",
                ".cookie-consent button",
                "#cookie-consent button",
                ".gdpr-consent button"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    cookie_button.click()
                    print(f"✅ Cookies acceptés")
                    time.sleep(2)
                    return True
                except TimeoutException:
                    continue
                    
            return False
            
        except Exception as e:
            return False
    
    def extract_lawyer_info(self, lawyer_element):
        """Extraire les informations complètes d'un avocat"""
        lawyer_data = {
            'prenom': '',
            'nom': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'code_postal': '',
            'ville': '',
            'specialisations': [],
            'annee_inscription': '',
            'structure': '',
            'site_web': ''
        }
        
        try:
            # Récupérer tout le texte de l'élément
            full_text = lawyer_element.text.strip()
            
            # 1. Nom et prénom - Format: "NOM Prénom Ville (Code postal)"
            try:
                name_element = lawyer_element.find_element(By.CSS_SELECTOR, "h3, h4, .name, strong")
                name_text = name_element.text.strip()
                
                # Parser avec regex : "NOM Prénom Ville (Code postal)"
                name_match = re.match(r'([A-Z\s-]+?)\s+([A-Za-zÀ-ÿ\s-]+?)\s+([A-Za-zÀ-ÿ\s-]+)\s*\((\d{5})\)', name_text)
                
                if name_match:
                    lawyer_data['nom'] = name_match.group(1).strip()
                    lawyer_data['prenom'] = name_match.group(2).strip()
                    lawyer_data['ville'] = name_match.group(3).strip()
                    lawyer_data['code_postal'] = name_match.group(4).strip()
                else:
                    # Format alternatif: essayer juste "NOM Prénom"
                    name_parts = name_text.split()
                    if len(name_parts) >= 2:
                        lawyer_data['nom'] = name_parts[0]
                        lawyer_data['prenom'] = " ".join(name_parts[1:])
                        
            except NoSuchElementException:
                # Extraire depuis la première ligne du texte
                first_line = full_text.split('\n')[0] if full_text else ""
                name_match = re.match(r'([A-Z\s-]+?)\s+([A-Za-zÀ-ÿ\s-]+)', first_line)
                if name_match:
                    lawyer_data['nom'] = name_match.group(1).strip()
                    lawyer_data['prenom'] = name_match.group(2).strip()
            
            # 2. Email
            try:
                email_element = lawyer_element.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                lawyer_data['email'] = email_element.get_attribute('href').replace('mailto:', '')
            except NoSuchElementException:
                # Recherche avec regex dans le texte
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', full_text)
                if email_match:
                    lawyer_data['email'] = email_match.group(1)
            
            # 3. Téléphone
            try:
                phone_element = lawyer_element.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
                lawyer_data['telephone'] = phone_element.text.strip()
            except NoSuchElementException:
                # Recherche avec regex
                phone_matches = re.findall(r'(?:Tél\s*[:.]?\s*)?(\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2})', full_text)
                if phone_matches:
                    lawyer_data['telephone'] = phone_matches[0]
            
            # 4. Spécialisations depuis "Domaines d'activités"
            specializations_match = re.search(r'Domaines d\'activités\s*[:\n]\s*(.+?)(?:\n|$)', full_text, re.IGNORECASE | re.MULTILINE)
            if specializations_match:
                spec_text = specializations_match.group(1).strip()
                # Nettoyer le texte
                spec_text = re.sub(r'^[:\s,]+', '', spec_text)
                spec_text = re.sub(r'[,\s]+$', '', spec_text)
                
                if spec_text:
                    # Séparer par les virgules
                    specializations = [s.strip() for s in spec_text.split(',') if s.strip()]
                    lawyer_data['specialisations'] = specializations
            
            # 5. Adresse depuis Google Maps
            try:
                maps_link = lawyer_element.find_element(By.CSS_SELECTOR, "a[href*='maps.google']")
                maps_url = maps_link.get_attribute('href')
                
                # Extraire l'adresse depuis l'URL
                address_match = re.search(r'q=([^&]+)', maps_url)
                if address_match:
                    from urllib.parse import unquote
                    address_encoded = address_match.group(1)
                    address_decoded = unquote(address_encoded).replace('%0D%0A', '\n')
                    
                    # Parser l'adresse
                    address_lines = address_decoded.split(',')
                    if len(address_lines) >= 1:
                        # Première partie = adresse
                        lawyer_data['adresse'] = address_lines[0].strip()
                        
                        # Rechercher code postal et ville s'ils ne sont pas déjà remplis
                        if not lawyer_data['code_postal'] or not lawyer_data['ville']:
                            for part in address_lines:
                                postal_match = re.search(r'(\d{5})', part)
                                if postal_match and not lawyer_data['code_postal']:
                                    lawyer_data['code_postal'] = postal_match.group(1)
                                
                                # Ville = partie avec lettres mais sans code postal
                                if re.search(r'[A-Za-zÀ-ÿ\s-]+', part) and not re.search(r'\d{5}', part) and not lawyer_data['ville']:
                                    city_clean = re.sub(r'^\s*,?\s*', '', part).strip()
                                    if city_clean and len(city_clean) > 1:
                                        lawyer_data['ville'] = city_clean
                        
            except NoSuchElementException:
                pass
            
            # 6. Année d'inscription (si mentionnée)
            year_match = re.search(r'(?:inscrit|inscription).*?(\d{4})', full_text, re.IGNORECASE)
            if year_match:
                year = int(year_match.group(1))
                if 1950 <= year <= datetime.now().year:  # Validation de l'année
                    lawyer_data['annee_inscription'] = str(year)
            
            # 7. Structure/Cabinet
            cabinet_patterns = [
                r'Cabinet\s+([A-Za-zÀ-ÿ\s&.-]+?)(?:\n|$)',
                r'SCP\s+([A-Za-zÀ-ÿ\s&.-]+?)(?:\n|$)',
                r'Société\s+([A-Za-zÀ-ÿ\s&.-]+?)(?:\n|$)',
                r'SELARL\s+([A-Za-zÀ-ÿ\s&.-]+?)(?:\n|$)',
                r'([A-Za-zÀ-ÿ\s&.-]+)\s+[Aa]vocats?(?:\n|$)'
            ]
            
            for pattern in cabinet_patterns:
                cabinet_match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
                if cabinet_match:
                    structure = cabinet_match.group(1).strip()
                    # Validation : ne pas prendre des noms de personnes
                    if len(structure) > 3 and not re.match(r'^[A-Z]+\s+[A-Za-z]+$', structure):
                        lawyer_data['structure'] = structure
                        break
                
        except Exception as e:
            print(f"⚠️  Erreur extraction avocat: {e}")
        
        return lawyer_data
    
    def get_lawyers_from_page(self, page_num):
        """Extraire tous les avocats de la page courante"""
        lawyers = []
        
        try:
            # Attendre le chargement complet de la page
            time.sleep(4)
            
            # Les avocats sont dans des balises <article>
            lawyer_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            
            if not lawyer_elements:
                print(f"⚠️  Aucun élément <article> trouvé sur la page {page_num}")
                return lawyers
                
            print(f"📋 {len(lawyer_elements)} avocats détectés sur la page {page_num}")
            
            for i, element in enumerate(lawyer_elements):
                try:
                    lawyer_data = self.extract_lawyer_info(element)
                    
                    # Validation : doit avoir au moins un nom ou un email
                    if lawyer_data['nom'] or lawyer_data['prenom'] or lawyer_data['email']:
                        lawyers.append(lawyer_data)
                    else:
                        print(f"   ⚠️  Avocat {i+1} ignoré (données insuffisantes)")
                    
                except Exception as e:
                    print(f"   ❌ Erreur avocat {i+1}: {e}")
                    continue
                    
            print(f"✅ {len(lawyers)} avocats valides extraits de la page {page_num}")
                    
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des avocats page {page_num}: {e}")
            
        return lawyers
    
    def get_total_pages(self):
        """Détecter le nombre total de pages"""
        try:
            # Chercher les liens de pagination
            page_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='page-']")
            max_page = 1
            
            for link in page_links:
                href = link.get_attribute('href') or ''
                text = link.text.strip()
                
                # Extraire depuis l'href
                page_match = re.search(r'page-(\d+)', href)
                if page_match:
                    page_num = int(page_match.group(1))
                    max_page = max(max_page, page_num)
                
                # Ou depuis le texte
                if text.isdigit():
                    page_num = int(text)
                    max_page = max(max_page, page_num)
                    
            return max_page
            
        except Exception as e:
            print(f"⚠️  Erreur détection pages: {e}")
            return 1
    
    def navigate_to_page(self, page_num):
        """Naviguer vers une page spécifique"""
        try:
            url = f"{self.base_url}/page-{page_num}"
            self.driver.get(url)
            
            # Attendre que la page se charge
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "article")))
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"❌ Erreur navigation page {page_num}: {e}")
            return False
    
    def scrape_all_pages(self):
        """Scraper TOUTES les pages de l'annuaire"""
        print("🚀 DÉBUT DU SCRAPING COMPLET - MODE PRODUCTION")
        print("=" * 70)
        
        try:
            # Page 1
            print("🔗 Connexion à la première page...")
            self.driver.get(f"{self.base_url}/page-1")
            
            # Accepter les cookies
            self.accept_cookies_if_present()
            
            # Détecter le nombre total de pages
            total_pages = self.get_total_pages()
            print(f"📄 TOTAL DE PAGES DÉTECTÉES: {total_pages}")
            print(f"🎯 Scraping prévu sur {total_pages} pages\n")
            
            start_time = time.time()
            
            for page_num in range(1, total_pages + 1):
                page_start = time.time()
                print(f"📖 PAGE {page_num}/{total_pages}")
                
                # Navigation (sauf pour la première page)
                if page_num > 1:
                    success = self.navigate_to_page(page_num)
                    if not success:
                        print(f"   ⏭️  Page {page_num} ignorée (erreur navigation)")
                        continue
                
                # Extraction des avocats
                page_lawyers = self.get_lawyers_from_page(page_num)
                
                if page_lawyers:
                    self.lawyers_data.extend(page_lawyers)
                    print(f"   ✅ {len(page_lawyers)} avocats ajoutés")
                else:
                    print(f"   ⚠️  Aucun avocat extrait de cette page")
                
                page_time = time.time() - page_start
                total_so_far = len(self.lawyers_data)
                print(f"   ⏱️  Page traitée en {page_time:.1f}s - Total: {total_so_far} avocats")
                
                # Sauvegarde intermédiaire tous les 5 pages
                if page_num % 5 == 0:
                    print(f"   💾 Sauvegarde intermédiaire...")
                    self.save_results(f"grasse_partial_p{page_num}")
                
                print()  # Ligne vide pour la lisibilité
                
            # Statistiques finales
            total_time = time.time() - start_time
            print("🎉 SCRAPING COMPLET TERMINÉ!")
            print("=" * 50)
            print(f"📊 TOTAL D'AVOCATS EXTRAITS: {len(self.lawyers_data)}")
            print(f"⏱️  TEMPS TOTAL: {total_time/60:.1f} minutes")
            print(f"📈 MOYENNE: {len(self.lawyers_data)/total_time*60:.1f} avocats/minute")
            
            return self.lawyers_data
            
        except KeyboardInterrupt:
            print("\n⏹️  SCRAPING INTERROMPU PAR L'UTILISATEUR")
            if self.lawyers_data:
                print(f"💾 Sauvegarde des {len(self.lawyers_data)} avocats déjà extraits...")
                self.save_results("grasse_interrupted")
            return self.lawyers_data
            
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE: {e}")
            if self.lawyers_data:
                print(f"💾 Sauvegarde de secours ({len(self.lawyers_data)} avocats)...")
                self.save_results("grasse_emergency")
            return []
    
    def save_results(self, filename_prefix="grasse_production"):
        """Sauvegarder tous les résultats avec rapports détaillés"""
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_lawyers = len(self.lawyers_data)
        
        print(f"💾 Sauvegarde de {total_lawyers} avocats...")
        
        # 1. JSON complet
        json_filename = f"{filename_prefix}_{total_lawyers}_avocats_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        print(f"   ✅ JSON: {json_filename}")
        
        # 2. CSV complet
        csv_filename = f"{filename_prefix}_{total_lawyers}_avocats_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.lawyers_data:
                fieldnames = ['prenom', 'nom', 'email', 'telephone', 'adresse', 'code_postal', 'ville', 
                            'specialisations', 'annee_inscription', 'structure', 'site_web']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations']) if lawyer['specialisations'] else ''
                    writer.writerow(lawyer_copy)
        print(f"   ✅ CSV: {csv_filename}")
        
        # 3. Fichier emails uniquement
        emails_filename = f"{filename_prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            emails_count = 0
            for lawyer in self.lawyers_data:
                if lawyer['email']:
                    f.write(f"{lawyer['email']}\n")
                    emails_count += 1
        print(f"   📧 {emails_count} Emails: {emails_filename}")
        
        # 4. Rapport de production détaillé
        report_filename = f"{filename_prefix}_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT DE PRODUCTION - SCRAPING BARREAU DE GRASSE\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Date de production: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            f.write(f"URL source: {self.base_url}\n")
            f.write(f"Nombre total d'avocats extraits: {total_lawyers}\n\n")
            
            # Statistiques de qualité
            with_email = sum(1 for l in self.lawyers_data if l['email'])
            with_phone = sum(1 for l in self.lawyers_data if l['telephone'])
            with_specializations = sum(1 for l in self.lawyers_data if l['specialisations'])
            with_address = sum(1 for l in self.lawyers_data if l['adresse'])
            with_structure = sum(1 for l in self.lawyers_data if l['structure'])
            
            f.write("STATISTIQUES DE QUALITÉ DES DONNÉES:\n")
            f.write(f"- Avocats avec email: {with_email} ({with_email/total_lawyers*100:.1f}%)\n")
            f.write(f"- Avocats avec téléphone: {with_phone} ({with_phone/total_lawyers*100:.1f}%)\n")
            f.write(f"- Avocats avec spécialisations: {with_specializations} ({with_specializations/total_lawyers*100:.1f}%)\n")
            f.write(f"- Avocats avec adresse complète: {with_address} ({with_address/total_lawyers*100:.1f}%)\n")
            f.write(f"- Avocats avec structure/cabinet: {with_structure} ({with_structure/total_lawyers*100:.1f}%)\n\n")
            
            # Répartition géographique
            cities = {}
            for lawyer in self.lawyers_data:
                city = lawyer['ville']
                if city:
                    cities[city] = cities.get(city, 0) + 1
            
            if cities:
                f.write("RÉPARTITION GÉOGRAPHIQUE (TOP 15):\n")
                for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:15]:
                    percentage = count/total_lawyers*100
                    f.write(f"- {city}: {count} avocats ({percentage:.1f}%)\n")
                f.write(f"\nTotal villes représentées: {len(cities)}\n\n")
            
            # Spécialisations les plus courantes
            all_specializations = []
            for lawyer in self.lawyers_data:
                all_specializations.extend(lawyer['specialisations'])
            
            if all_specializations:
                spec_counts = {}
                for spec in all_specializations:
                    spec_counts[spec] = spec_counts.get(spec, 0) + 1
                
                f.write("SPÉCIALISATIONS LES PLUS REPRÉSENTÉES (TOP 20):\n")
                for spec, count in sorted(spec_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
                    percentage = count/total_lawyers*100
                    f.write(f"- {spec}: {count} mentions ({percentage:.1f}%)\n")
                f.write(f"\nTotal spécialisations différentes: {len(spec_counts)}\n\n")
            
            # Exemples d'extraction
            f.write("EXEMPLES D'AVOCATS EXTRAITS:\n")
            f.write("-" * 40 + "\n")
            for i, lawyer in enumerate(self.lawyers_data[:10]):
                f.write(f"{i+1}. {lawyer['prenom']} {lawyer['nom']}\n")
                f.write(f"   📧 Email: {lawyer['email'] or 'Non renseigné'}\n")
                f.write(f"   📞 Téléphone: {lawyer['telephone'] or 'Non renseigné'}\n")
                f.write(f"   📍 Adresse: {lawyer['adresse']} - {lawyer['ville']} ({lawyer['code_postal']})\n")
                f.write(f"   🏢 Structure: {lawyer['structure'] or 'Non renseignée'}\n")
                f.write(f"   ⚖️  Spécialisations: {', '.join(lawyer['specialisations']) or 'Non renseignées'}\n\n")
            
            # Instructions d'utilisation
            f.write("FICHIERS GÉNÉRÉS:\n")
            f.write(f"- Données complètes JSON: {json_filename}\n")
            f.write(f"- Données complètes CSV: {csv_filename}\n")  
            f.write(f"- Liste emails seuls: {emails_filename}\n")
            f.write(f"- Ce rapport: {report_filename}\n\n")
            
            f.write("UTILISATION RECOMMANDÉE:\n")
            f.write("- Import Excel/Google Sheets: utiliser le fichier CSV\n")
            f.write("- Mailing list: utiliser le fichier emails TXT\n")
            f.write("- Développement/API: utiliser le fichier JSON\n")
            f.write("- Analyse: consulter ce rapport\n")
        
        print(f"   📋 Rapport: {report_filename}")
        print(f"\n🎉 SAUVEGARDE TERMINÉE - {total_lawyers} avocats sauvegardés!")
    
    def close(self):
        """Fermer le navigateur"""
        if self.driver:
            self.driver.quit()

def main():
    print("🏛️  SCRAPER PRODUCTION - BARREAU DE GRASSE")
    print("=" * 70)
    print("⚡ Mode headless activé (pas d'interface visuelle)")
    print("📊 Extraction de TOUS les avocats avec toutes les données")
    print("🎯 Données extraites: nom, prénom, email, tél, spécialisations, adresse...")
    print()
    
    scraper = None
    
    try:
        scraper = GrasseProductionScraper()
        
        # Lancer le scraping complet
        results = scraper.scrape_all_pages()
        
        if results:
            # Sauvegarde finale
            scraper.save_results("GRASSE_PRODUCTION_FINALE")
            
            print("\n" + "="*70)
            print("✅ SUCCÈS COMPLET!")
            print(f"📊 {len(results)} avocats du barreau de Grasse extraits")
            print("📁 Tous les fichiers sont sauvegardés dans le répertoire courant")
            print("="*70)
        else:
            print("\n❌ ÉCHEC - Aucune donnée extraite")
            
    except KeyboardInterrupt:
        print("\n⏹️  Script interrompu par l'utilisateur")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        
    finally:
        if scraper:
            scraper.close()
            print("🔒 Navigateur fermé")

if __name__ == "__main__":
    main()