#!/usr/bin/env python3
"""
Scraper de production pour les avocats du barreau d'Agen
Version finale optimisée
"""

import time
import json
import csv
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

class AgenBarreauScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.results = []
        self.stats = {
            'total': 0,
            'with_email': 0,
            'with_phone': 0,
            'with_inscription_year': 0,
            'with_specializations': 0
        }
        
    def setup_driver(self):
        """Configuration optimisée du driver Chrome"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--disable-images')  # Accélérer le chargement
        options.add_argument('--disable-javascript')  # Optionnel si le JS n'est pas nécessaire
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)
        
    def extract_basic_info(self, card):
        """Extraction optimisée des informations de base"""
        lawyer_info = {
            'civilite': '',
            'prenom': '',
            'nom': '',
            'nom_complet': '',
            'type': '',
            'adresse': '',
            'code_postal': '',
            'ville': '',
            'cour_appel': '',
            'telephone': '',
            'email': '',
            'annee_inscription': '',
            'specialisations': [],
            'structure': '',
            'site_web': '',
            'detail_url': '',
            'contact_url': ''
        }
        
        try:
            # Extraction nom et prénom
            try:
                civ = card.find_element(By.CSS_SELECTOR, ".anfiche_civ").text.strip()
                prenom = card.find_element(By.CSS_SELECTOR, ".anfiche_prenom").text.strip()
                nom = card.find_element(By.CSS_SELECTOR, ".anfiche_nom").text.strip()
                
                lawyer_info['civilite'] = civ
                lawyer_info['prenom'] = prenom
                lawyer_info['nom'] = nom
                lawyer_info['nom_complet'] = f"{prenom} {nom}".strip()
            except NoSuchElementException:
                # Fallback : chercher dans le titre h4
                try:
                    h4_elem = card.find_element(By.CSS_SELECTOR, "h4")
                    h4_text = h4_elem.text.strip()
                    # Parser "Maître Prénom NOM"
                    parts = h4_text.split()
                    if len(parts) >= 3:
                        lawyer_info['civilite'] = parts[0]
                        lawyer_info['prenom'] = parts[1]
                        lawyer_info['nom'] = ' '.join(parts[2:])
                        lawyer_info['nom_complet'] = f"{lawyer_info['prenom']} {lawyer_info['nom']}"
                except:
                    pass
            
            # Type d'avocat
            try:
                type_elem = card.find_element(By.CSS_SELECTOR, ".type")
                lawyer_info['type'] = type_elem.text.strip()
            except NoSuchElementException:
                pass
            
            # Coordonnées
            try:
                coordonnees = card.find_element(By.CSS_SELECTOR, ".coordonnees")
                
                # Adresse
                try:
                    adresse = coordonnees.find_element(By.CSS_SELECTOR, ".adresse").text.strip()
                    lawyer_info['adresse'] = adresse
                except:
                    pass
                
                # Code postal et ville
                try:
                    cpville = coordonnees.find_element(By.CSS_SELECTOR, ".cpville").text.strip()
                    parts = cpville.split(' ', 1)
                    if len(parts) >= 2:
                        lawyer_info['code_postal'] = parts[0]
                        lawyer_info['ville'] = parts[1]
                    else:
                        lawyer_info['ville'] = cpville
                except:
                    pass
                
                # Cour d'appel
                try:
                    cour = coordonnees.find_element(By.CSS_SELECTOR, ".courappel .value").text.strip()
                    lawyer_info['cour_appel'] = cour
                except:
                    pass
                
                # Téléphone
                try:
                    tel_elem = coordonnees.find_element(By.CSS_SELECTOR, ".tel")
                    tel_text = tel_elem.text.strip()
                    if 'Tél :' in tel_text:
                        tel_clean = tel_text.replace('Tél :', '').strip()
                        lawyer_info['telephone'] = tel_clean
                except:
                    pass
                
            except NoSuchElementException:
                pass
            
            # URLs
            try:
                detail_link = card.find_element(By.CSS_SELECTOR, ".btnAnnuaireDetail")
                lawyer_info['detail_url'] = detail_link.get_attribute('href')
            except NoSuchElementException:
                pass
                
            try:
                contact_link = card.find_element(By.CSS_SELECTOR, ".btnAnnuaireContact")
                lawyer_info['contact_url'] = contact_link.get_attribute('href')
            except NoSuchElementException:
                pass
            
            return lawyer_info
            
        except Exception as e:
            print(f"⚠ Erreur extraction de base: {e}")
            return lawyer_info
    
    def get_detailed_info(self, detail_url):
        """Récupération des informations détaillées"""
        detailed_info = {
            'email': '',
            'annee_inscription': '',
            'specialisations': [],
            'structure': '',
            'site_web': ''
        }
        
        if not detail_url:
            return detailed_info
            
        try:
            # Ouvrir dans un nouvel onglet
            self.driver.execute_script(f"window.open('{detail_url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Attendre le chargement avec timeout court
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Récupérer l'email
            try:
                email_elem = self.driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
                email_encoded = email_elem.get_attribute('href').replace('mailto:', '')
                # Décoder l'email URL-encodé
                email_decoded = urllib.parse.unquote(email_encoded)
                detailed_info['email'] = email_decoded
            except NoSuchElementException:
                # Fallback: chercher dans le texte
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, page_text)
                    if emails:
                        detailed_info['email'] = emails[0]
                except:
                    pass
            
            # Année d'inscription au barreau
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                year_patterns = [
                    r'(?:inscrit|inscription).*?(\d{4})',
                    r'barreau.*?(\d{4})',
                    r'depuis\s+(\d{4})',
                    r'admis.*?(\d{4})'
                ]
                for pattern in year_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        for year in matches:
                            year_int = int(year)
                            if 1950 <= year_int <= 2025:
                                detailed_info['annee_inscription'] = year
                                break
                        if detailed_info['annee_inscription']:
                            break
            except:
                pass
            
            # Spécialisations
            try:
                specializations = []
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                # Liste des spécialisations courantes
                spec_list = [
                    'droit civil', 'droit pénal', 'droit du travail', 'droit commercial',
                    'droit de la famille', 'droit immobilier', 'droit fiscal', 'droit des affaires',
                    'droit public', 'droit administratif', 'droit de la construction',
                    'droit de la santé', 'droit de l\'environnement', 'droit bancaire',
                    'droit des assurances', 'droit social', 'droit routier', 'droit pénal des affaires'
                ]
                
                for spec in spec_list:
                    if spec in page_text:
                        specializations.append(spec.title())
                
                detailed_info['specialisations'] = list(set(specializations))  # Supprimer doublons
                
            except:
                pass
            
            # Structure (cabinet, société)
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                structure_patterns = [
                    r'cabinet\s+([^\n\r.]+)',
                    r'société\s+([^\n\r.]+)',
                    r'secp\s+([^\n\r.]+)',
                    r'scp\s+([^\n\r.]+)'
                ]
                for pattern in structure_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        structure = matches[0].strip()
                        if len(structure) < 100:  # Éviter les textes trop longs
                            detailed_info['structure'] = structure
                            break
            except:
                pass
            
            # Site web
            try:
                site_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='http']:not([href*='mailto:'])")
                for link in site_links:
                    href = link.get_attribute('href')
                    if 'barreau-agen.fr' not in href and 'javascript:' not in href:
                        detailed_info['site_web'] = href
                        break
            except:
                pass
            
            # Fermer l'onglet et revenir
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return detailed_info
            
        except Exception as e:
            print(f"⚠ Erreur détails: {e}")
            # S'assurer de revenir à la fenêtre principale
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return detailed_info
    
    def scrape_all_lawyers(self):
        """Scraper tous les avocats du barreau d'Agen"""
        print("🚀 SCRAPING COMPLET DU BARREAU D'AGEN")
        print("=" * 50)
        
        try:
            # Configuration
            self.setup_driver()
            
            print("📄 Accès à la page d'annuaire...")
            self.driver.get("https://www.barreau-agen.fr/annuaire-des-avocats/liste-et-recherche.htm")
            
            # Attendre le chargement
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".annuaireFicheMini"))
            )
            
            print("✓ Page chargée")
            
            # Récupérer toutes les cartes
            lawyer_cards = self.driver.find_elements(By.CSS_SELECTOR, ".annuaireFicheMini.annuaireFicheMiniAvocat")
            total_lawyers = len(lawyer_cards)
            self.stats['total'] = total_lawyers
            
            print(f"📋 {total_lawyers} avocats trouvés")
            print("🏃‍♂️ Début du traitement...\n")
            
            # Traiter chaque avocat
            for i, card in enumerate(lawyer_cards, 1):
                print(f"👤 [{i:3d}/{total_lawyers}] ", end="")
                
                # Informations de base
                lawyer_info = self.extract_basic_info(card)
                
                if lawyer_info.get('nom_complet'):
                    print(f"{lawyer_info['nom_complet']:<35}", end=" ")
                else:
                    print("Nom non trouvé".ljust(35), end=" ")
                
                # Informations détaillées
                if lawyer_info.get('detail_url'):
                    detailed_info = self.get_detailed_info(lawyer_info['detail_url'])
                    lawyer_info.update(detailed_info)
                
                # Mise à jour des stats
                if lawyer_info.get('email'):
                    self.stats['with_email'] += 1
                    print("📧", end=" ")
                else:
                    print("  ", end=" ")
                    
                if lawyer_info.get('telephone'):
                    self.stats['with_phone'] += 1
                    print("📞", end=" ")
                else:
                    print("  ", end=" ")
                    
                if lawyer_info.get('annee_inscription'):
                    self.stats['with_inscription_year'] += 1
                    print("📅", end=" ")
                else:
                    print("  ", end=" ")
                    
                if lawyer_info.get('specialisations'):
                    self.stats['with_specializations'] += 1
                    print("🎯", end=" ")
                else:
                    print("  ", end=" ")
                
                print()  # Nouvelle ligne
                
                self.results.append(lawyer_info)
                
                # Pause légère pour éviter la surcharge
                time.sleep(0.5)
                
                # Sauvegarde intermédiaire tous les 20 avocats
                if i % 20 == 0:
                    self.save_intermediate_results(i)
            
            print("\n✅ Scraping terminé!")
            self.save_results()
            self.print_final_stats()
            
        except Exception as e:
            print(f"\n❌ Erreur lors du scraping: {e}")
            if self.results:
                print("💾 Sauvegarde des données partielles...")
                self.save_results()
        
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Navigateur fermé")
    
    def save_intermediate_results(self, progress):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agen_avocats_partiel_{progress}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"    💾 Sauvegarde intermédiaire: {filename}")
    
    def save_results(self):
        """Sauvegarde finale des résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_filename = f"agen_avocats_complet_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'source': 'https://www.barreau-agen.fr/annuaire-des-avocats/liste-et-recherche.htm',
                    'date_extraction': timestamp,
                    'total_avocats': len(self.results),
                    'statistiques': self.stats
                },
                'avocats': self.results
            }, f, ensure_ascii=False, indent=2)
        
        # CSV pour Excel
        if self.results:
            csv_filename = f"agen_avocats_complet_{timestamp}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'nom_complet', 'prenom', 'nom', 'civilite', 'type',
                    'adresse', 'code_postal', 'ville', 'cour_appel',
                    'telephone', 'email', 'annee_inscription',
                    'specialisations', 'structure', 'site_web',
                    'detail_url', 'contact_url'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.results:
                    # Convertir la liste des spécialisations en string
                    row = lawyer.copy()
                    if isinstance(row.get('specialisations'), list):
                        row['specialisations'] = '; '.join(row['specialisations'])
                    writer.writerow(row)
        
        print(f"\n💾 Fichiers sauvegardés:")
        print(f"   📄 JSON: {json_filename}")
        print(f"   📊 CSV:  {csv_filename}")
    
    def print_final_stats(self):
        """Afficher les statistiques finales"""
        print("\n📊 STATISTIQUES FINALES")
        print("=" * 30)
        print(f"Total avocats traités:     {self.stats['total']}")
        print(f"Avec email:               {self.stats['with_email']:3d} ({self.stats['with_email']/self.stats['total']*100:.1f}%)")
        print(f"Avec téléphone:           {self.stats['with_phone']:3d} ({self.stats['with_phone']/self.stats['total']*100:.1f}%)")
        print(f"Avec année d'inscription: {self.stats['with_inscription_year']:3d} ({self.stats['with_inscription_year']/self.stats['total']*100:.1f}%)")
        print(f"Avec spécialisations:     {self.stats['with_specializations']:3d} ({self.stats['with_specializations']/self.stats['total']*100:.1f}%)")

def main():
    """Fonction principale"""
    scraper = AgenBarreauScraper(headless=True)  # Mode headless pour éviter les fenêtres
    scraper.scrape_all_lawyers()

if __name__ == "__main__":
    main()