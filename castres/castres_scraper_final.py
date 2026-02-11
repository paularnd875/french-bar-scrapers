#!/usr/bin/env python3
"""
Script final pour scraper TOUS les avocats du barreau de Castres
Version headless avec extraction complète et correction des noms
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class CastresScraperFinal:
    def __init__(self, headless=True, max_lawyers=None):
        self.headless = headless
        self.max_lawyers = max_lawyers  # Pour limiter si besoin
        self.driver = None
        self.lawyers = []
        
    def setup_driver(self):
        """Configuration du driver Chrome optimisé"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            print("🔇 Mode headless activé - pas d'interface graphique")
            
        # Options d'optimisation
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-images')  # Accélère le chargement
        chrome_options.add_argument('--disable-javascript')  # On peut le désactiver car les données sont dans le HTML
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent pour éviter la détection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Timeouts optimisés
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        
        return self.driver
        
    def accept_cookies(self):
        """Gestion de l'acceptation des cookies"""
        try:
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Rechercher et accepter les cookies si nécessaire
            cookie_selectors = [
                '[id*="cookie"] button',
                '[class*="cookie"] button',
                '[id*="consent"] button',
                '[class*="consent"] button',
                'button[class*="accept"]',
                'button[id*="accept"]',
                'a[class*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and any(word in element.text.lower() for word in ['accept', 'accepter', 'ok']):
                            element.click()
                            time.sleep(2)
                            return
                except:
                    continue
                    
        except Exception as e:
            pass  # Continue même si erreur cookies
            
        time.sleep(2)
        
    def get_lawyer_links(self):
        """Récupération de TOUS les liens vers les fiches d'avocats"""
        print("📋 Récupération des liens d'avocats...")
        
        lawyer_links = []
        
        try:
            # Attendre que les éléments soient chargés
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Récupérer tous les liens contenant "avocat"
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute('href')
                if href and '/avocat/' in href and href.count('/') >= 4:
                    # Vérifier que c'est bien une fiche individuelle
                    if not href.endswith('/avocat/') and not href.endswith('/avocats/'):
                        lawyer_links.append(href)
            
            # Nettoyer et dédupliquer
            lawyer_links = list(set([link for link in lawyer_links if link]))
            
            print(f"📊 Total de {len(lawyer_links)} liens d'avocats trouvés")
            
            # Appliquer la limitation si demandée
            if self.max_lawyers and len(lawyer_links) > self.max_lawyers:
                lawyer_links = lawyer_links[:self.max_lawyers]
                print(f"⚠️  Limitation à {self.max_lawyers} avocats pour ce test")
                
            return lawyer_links
            
        except Exception as e:
            print(f"❌ Erreur récupération liens: {e}")
            return []
    
    def extract_name_from_url_and_meta(self, url, meta_content):
        """Extraction intelligente du nom depuis l'URL et les métadonnées"""
        name_info = {'nom': '', 'prenom': ''}
        
        try:
            # Méthode 1: Depuis l'URL
            url_parts = url.split('/')
            if len(url_parts) > 4:
                name_part = url_parts[-2]  # Avant-dernier élément
                # Formats possibles: nom-prenom, prenom-nom
                if '-' in name_part:
                    parts = name_part.split('-')
                    if len(parts) == 2:
                        # Essayer de déterminer l'ordre
                        first, second = parts[0].title(), parts[1].title()
                        
                        # Vérifier dans meta content pour confirmation
                        if meta_content:
                            if first.upper() in meta_content.upper():
                                name_info['nom'] = first
                                name_info['prenom'] = second
                            elif second.upper() in meta_content.upper():
                                name_info['nom'] = second  
                                name_info['prenom'] = first
                        else:
                            # Par défaut: premier = nom, second = prénom
                            name_info['nom'] = first
                            name_info['prenom'] = second
            
            # Méthode 2: Depuis meta description si pas déjà trouvé
            if not name_info['nom'] and meta_content:
                # Rechercher pattern "Prénom NOM" au début
                name_match = re.search(r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç]+)\s+([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]{2,})', meta_content)
                if name_match:
                    name_info['prenom'] = name_match.group(1)
                    name_info['nom'] = name_match.group(2)
                else:
                    # Rechercher pattern "NOM Prénom"
                    name_match = re.search(r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]{2,})\s+([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç]+)', meta_content)
                    if name_match:
                        name_info['nom'] = name_match.group(1)
                        name_info['prenom'] = name_match.group(2)
            
            # Méthode 3: Si toujours pas trouvé, extraire depuis le titre de page
            if not name_info['nom']:
                try:
                    title_element = self.driver.find_element(By.TAG_NAME, "title")
                    title_text = title_element.get_attribute("textContent") or title_element.text
                    # Nettoyer le titre
                    clean_title = re.sub(r' - Ordre des Avocats.*', '', title_text)
                    
                    # Pattern "NOM Prénom"
                    title_match = re.search(r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]{2,})\s+([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç]+)', clean_title)
                    if title_match:
                        name_info['nom'] = title_match.group(1)
                        name_info['prenom'] = title_match.group(2)
                except:
                    pass
                    
        except Exception as e:
            print(f"   Erreur extraction nom: {e}")
        
        return name_info
    
    def extract_lawyer_info(self, url):
        """Extraction optimisée des informations d'un avocat"""
        lawyer_info = {
            'url': url,
            'nom': '',
            'prenom': '',
            'email': '',
            'annee_inscription': '',
            'date_serment': '',
            'specialisations': [],
            'structure': '',
            'adresse': '',
            'ville': '',
            'telephone': '',
            'telecopie': '',
            'mobile': ''
        }
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Obtenir tout le texte de la page et source
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source
            
            # 1. Extraction métadonnées (très riche sur ce site)
            meta_content = ""
            try:
                meta_description = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="description"]')
                if meta_description:
                    meta_content = meta_description.get_attribute("content")
                    
                    # Extraire structure depuis meta
                    structure_patterns = [
                        r'(SELARL [^0-9]{3,50})',
                        r'(SARL [^0-9]{3,50})',
                        r'(SCP [^0-9]{3,50})',
                        r'(SELAS [^0-9]{3,50})',
                        r'(SCPI [^0-9]{3,50})'
                    ]
                    
                    for pattern in structure_patterns:
                        structure_match = re.search(pattern, meta_content)
                        if structure_match:
                            # Nettoyer la structure
                            structure = structure_match.group(1).strip()
                            # Enlever les numéros à la fin
                            structure = re.sub(r'\s+\d+.*$', '', structure)
                            lawyer_info['structure'] = structure.strip()
                            break
                    
                    # Téléphones depuis meta
                    phone_match = re.search(r'Téléphone[^:]*:\s*([\d\s\.]+)', meta_content)
                    if phone_match:
                        lawyer_info['telephone'] = phone_match.group(1).strip()
                    
                    fax_match = re.search(r'Télécopie[^:]*:\s*([\d\s\.]+)', meta_content)
                    if fax_match:
                        lawyer_info['telecopie'] = fax_match.group(1).strip()
                        
                    mobile_match = re.search(r'mobile[^:]*:\s*([\d\s\.]+)', meta_content, re.IGNORECASE)
                    if mobile_match:
                        lawyer_info['mobile'] = mobile_match.group(1).strip()
                        
            except Exception as e:
                pass
            
            # 2. Extraction du nom (méthode améliorée)
            name_info = self.extract_name_from_url_and_meta(url, meta_content)
            lawyer_info.update(name_info)
            
            # 3. Extraction depuis le contenu de la page
            try:
                content_blocks = self.driver.find_elements(By.CSS_SELECTOR, '.content-block p, .content p, .single-attorney-content p')
                for block in content_blocks:
                    text = block.text.strip()
                    if not text:
                        continue
                    
                    # Email
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
                    if email_match and not lawyer_info['email']:
                        lawyer_info['email'] = email_match.group(1)
                    
                    # Date de serment
                    if 'serment' in text.lower():
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
                        if date_match:
                            lawyer_info['date_serment'] = date_match.group(1)
                            year_match = re.search(r'(\d{4})', lawyer_info['date_serment'])
                            if year_match:
                                lawyer_info['annee_inscription'] = year_match.group(1)
                    
                    # Adresse et ville
                    if re.search(r'\d+.*(?:rue|avenue|boulevard|place|allée)', text, re.IGNORECASE):
                        if not lawyer_info['adresse']:
                            lawyer_info['adresse'] = text
                    
                    # Ville (codes postaux 81xxx pour le Tarn)
                    ville_match = re.search(r'81\d{3}\s+([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ\s-]+)', text)
                    if ville_match and not lawyer_info['ville']:
                        lawyer_info['ville'] = ville_match.group(1).strip()
                        
            except Exception as e:
                pass
            
            # 4. Recherche spécialisations améliorée
            try:
                # Patterns spécifiques à ce site
                specialization_patterns = [
                    r'Practice Areas?\s*:\s*([^\.]+)',
                    r'Spécialisation[^:]*:\s*([^\.]+)',
                    r'Domaines?\s*:\s*([^\.]+)'
                ]
                
                for pattern in specialization_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        clean_spec = re.sub(r'\s+', ' ', match).strip()
                        if clean_spec and clean_spec not in lawyer_info['specialisations']:
                            lawyer_info['specialisations'].append(clean_spec)
                            
            except Exception as e:
                pass
            
            # 5. Fallback pour email si pas trouvé (email générique)
            if not lawyer_info['email']:
                # Chercher dans tout le HTML
                email_matches = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', page_source)
                if email_matches:
                    # Prendre le premier email qui n'est pas générique
                    for email in email_matches:
                        if 'secretariat' not in email and 'contact' not in email:
                            lawyer_info['email'] = email
                            break
                    if not lawyer_info['email']:
                        lawyer_info['email'] = email_matches[0]  # Prendre au moins le premier
            
        except Exception as e:
            print(f"❌ Erreur extraction {url}: {e}")
        
        return lawyer_info
    
    def run_production(self):
        """Exécution de la production complète"""
        start_time = time.time()
        
        print("🚀 DÉMARRAGE SCRAPER COMPLET BARREAU DE CASTRES")
        print("=" * 70)
        print(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"⚙️  Mode: {'Headless' if self.headless else 'Visuel'}")
        if self.max_lawyers:
            print(f"🔢 Limitation: {self.max_lawyers} avocats maximum")
        print("=" * 70)
        
        try:
            # Configuration
            self.setup_driver()
            print("✅ Driver configuré")
            
            # Accès à la page
            print("🌐 Accès à la page d'annuaire...")
            self.driver.get("https://avocats-castres.fr/annuaire-avocats/")
            time.sleep(3)
            
            # Gestion cookies
            self.accept_cookies()
            
            # Récupération des liens
            lawyer_links = self.get_lawyer_links()
            
            if not lawyer_links:
                print("❌ Aucun lien d'avocat trouvé")
                return
            
            print(f"📋 Début du traitement de {len(lawyer_links)} avocats...")
            print()
            
            # Traitement de tous les avocats
            for i, link in enumerate(lawyer_links, 1):
                print(f"👤 [{i:02d}/{len(lawyer_links):02d}] Traitement...", end=" ")
                lawyer_info = self.extract_lawyer_info(link)
                self.lawyers.append(lawyer_info)
                
                # Afficher nom si trouvé
                name_display = f"{lawyer_info.get('prenom', '')} {lawyer_info.get('nom', '')}".strip()
                if name_display:
                    print(f"✅ {name_display}")
                else:
                    print(f"✅ {link.split('/')[-2].replace('-', ' ').title()}")
                
                # Pause pour éviter la surcharge
                if i % 10 == 0:
                    print(f"   ⏸️  Pause technique (traité {i}/{len(lawyer_links)})")
                    time.sleep(3)
                else:
                    time.sleep(1)
            
            # Sauvegarde résultats
            self.save_results()
            
            # Statistiques finales
            end_time = time.time()
            duration = end_time - start_time
            
            print("\n" + "=" * 70)
            print("✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
            print("=" * 70)
            print(f"📊 {len(self.lawyers)} avocats traités")
            print(f"⏱️  Durée totale: {duration:.1f} secondes")
            print(f"⚡ Vitesse moyenne: {len(self.lawyers)/duration:.1f} avocats/seconde")
            
            # Statistiques détaillées
            self.print_statistics()
            
        except Exception as e:
            print(f"❌ Erreur durant l'extraction: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔚 Driver fermé")
    
    def print_statistics(self):
        """Affichage des statistiques détaillées"""
        if not self.lawyers:
            return
            
        print("\n📈 STATISTIQUES D'EXTRACTION:")
        print("-" * 40)
        
        emails_found = len([l for l in self.lawyers if l.get('email')])
        phones_found = len([l for l in self.lawyers if l.get('telephone')])
        structures_found = len([l for l in self.lawyers if l.get('structure')])
        specializations_found = len([l for l in self.lawyers if l.get('specialisations')])
        dates_found = len([l for l in self.lawyers if l.get('date_serment')])
        
        print(f"📧 Emails trouvés: {emails_found}/{len(self.lawyers)} ({emails_found*100/len(self.lawyers):.1f}%)")
        print(f"📞 Téléphones trouvés: {phones_found}/{len(self.lawyers)} ({phones_found*100/len(self.lawyers):.1f}%)")
        print(f"🏢 Structures trouvées: {structures_found}/{len(self.lawyers)} ({structures_found*100/len(self.lawyers):.1f}%)")
        print(f"⚖️  Spécialisations: {specializations_found}/{len(self.lawyers)} ({specializations_found*100/len(self.lawyers):.1f}%)")
        print(f"📅 Dates de serment: {dates_found}/{len(self.lawyers)} ({dates_found*100/len(self.lawyers):.1f}%)")
    
    def save_results(self):
        """Sauvegarde des résultats avec horodatage"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON détaillé
        json_file = f'castres_COMPLET_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers, f, ensure_ascii=False, indent=2)
        
        # CSV pour Excel
        csv_file = f'castres_COMPLET_{timestamp}.csv'
        if self.lawyers:
            fieldnames = self.lawyers[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in self.lawyers:
                    row = lawyer.copy()
                    row['specialisations'] = '; '.join(row['specialisations']) if row['specialisations'] else ''
                    writer.writerow(row)
        
        # Fichier emails seulement
        emails_file = f'castres_EMAILS_SEULEMENT_{timestamp}.txt'
        with open(emails_file, 'w', encoding='utf-8') as f:
            for lawyer in self.lawyers:
                if lawyer.get('email'):
                    name = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                    f.write(f"{lawyer['email']}")
                    if name:
                        f.write(f" - {name}")
                    f.write('\n')
        
        # Rapport de synthèse
        report_file = f'castres_RAPPORT_COMPLET_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION BARREAU DE CASTRES\n")
            f.write(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Nombre total d'avocats traités: {len(self.lawyers)}\n\n")
            
            f.write("STATISTIQUES:\n")
            emails_found = len([l for l in self.lawyers if l.get('email')])
            f.write(f"- Emails trouvés: {emails_found}\n")
            f.write(f"- Téléphones trouvés: {len([l for l in self.lawyers if l.get('telephone')])}\n")
            f.write(f"- Structures trouvées: {len([l for l in self.lawyers if l.get('structure')])}\n")
            f.write(f"- Spécialisations: {len([l for l in self.lawyers if l.get('specialisations')])}\n")
            f.write(f"- Dates de serment: {len([l for l in self.lawyers if l.get('date_serment')])}\n\n")
            
            f.write("EMAILS EXTRAITS:\n")
            for lawyer in self.lawyers:
                if lawyer.get('email'):
                    name = f"{lawyer.get('prenom', '')} {lawyer.get('nom', '')}".strip()
                    f.write(f"{lawyer['email']}")
                    if name:
                        f.write(f" - {name}")
                    f.write('\n')
        
        print(f"💾 Résultats sauvegardés:")
        print(f"   - Données complètes: {json_file}")
        print(f"   - CSV pour Excel: {csv_file}")
        print(f"   - Emails uniquement: {emails_file}")
        print(f"   - Rapport: {report_file}")

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper du Barreau de Castres')
    parser.add_argument('--visual', action='store_true', help='Mode visuel (avec fenêtres)')
    parser.add_argument('--limit', type=int, help='Limiter le nombre d\'avocats (pour test)')
    
    args = parser.parse_args()
    
    # Configuration
    headless = not args.visual
    max_lawyers = args.limit
    
    # Lancement
    scraper = CastresScraperFinal(headless=headless, max_lawyers=max_lawyers)
    scraper.run_production()

if __name__ == "__main__":
    main()