#!/usr/bin/env python3
"""
Scraper final pour l'annuaire des avocats d'Essonne
Site: https://www.avocats91.com/lordre-des-avocats/annuaire-des-avocats.htm
"""

import time
import json
import re
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv

class EssonneBarScraperFinal:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()
        
    def setup_driver(self):
        """Configure le driver Chrome avec les bonnes options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Désactiver les notifications et autres popups
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)
        
    def accept_cookies(self):
        """Accepte les cookies si une bannière est présente"""
        try:
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[class*='cookie']"))
            )
            cookie_button.click()
            print("✅ Cookies acceptés")
            time.sleep(3)
            return True
        except TimeoutException:
            print("ℹ️  Aucune bannière de cookies trouvée")
            return True
        except Exception as e:
            print(f"⚠️  Erreur lors de l'acceptation des cookies: {e}")
            return False
    
    def decode_email(self, encoded_email):
        """Décode un email obfusqué avec des codes hexadécimaux"""
        try:
            # Décoder les codes hexadécimaux (%XX)
            decoded = urllib.parse.unquote(encoded_email)
            return decoded
        except Exception:
            return encoded_email
    
    def wait_for_content_load(self):
        """Attend que le contenu soit chargé"""
        try:
            # Attendre les cartes d'avocats
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".annuaireFicheMini"))
            )
            time.sleep(3)  # Attendre le chargement complet
            return True
        except TimeoutException:
            print("⚠️  Timeout en attendant le chargement du contenu")
            return False
    
    def get_lawyer_cards(self):
        """Récupère toutes les cartes d'avocats"""
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".annuaireFicheMini.annuaireFicheMiniAvocat")
            print(f"✅ {len(cards)} cartes d'avocats trouvées")
            return cards
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des cartes: {e}")
            return []
    
    def extract_text_safely(self, element, selector, default=""):
        """Extrait le texte d'un élément de manière sécurisée"""
        try:
            sub_element = element.find_element(By.CSS_SELECTOR, selector)
            return sub_element.text.strip()
        except NoSuchElementException:
            return default
        except Exception:
            return default
    
    def extract_lawyer_info_from_card(self, card):
        """Extrait les informations d'un avocat depuis sa carte"""
        lawyer_info = {
            'nom_complet': '',
            'nom': '',
            'prenom': '',
            'structure': '',
            'adresse': '',
            'code_postal': '',
            'ville': '',
            'telephone': '',
            'email': '',
            'annee_inscription': '',
            'specialisations': '',
            'detail_url': '',
            'contact_url': ''
        }
        
        try:
            # Debug: sauvegarder le HTML de la carte pour inspection
            card_html = card.get_attribute('outerHTML')
            
            # Nom dans la structure - essayer plusieurs sélecteurs
            structure = ""
            structure_selectors = [".structures .structure", ".structure"]
            for selector in structure_selectors:
                structure = self.extract_text_safely(card, selector)
                if structure:
                    break
            
            if not structure:
                # Essayer d'extraire le nom du lien de détail
                try:
                    detail_link = card.find_element(By.CSS_SELECTOR, "a[href*='maitre-']")
                    href = detail_link.get_attribute('href')
                    # Extraire le nom de l'URL : maitre-nom-prenom-id.htm
                    match = re.search(r'maitre-(.+)-(\d+)\.htm', href)
                    if match:
                        name_part = match.group(1).replace('-', ' ').upper()
                        structure = name_part
                except:
                    pass
            
            lawyer_info['structure'] = structure
            lawyer_info['nom_complet'] = structure
            
            # Séparer nom et prénom si possible
            if structure:
                # Format généralement : NOM PRÉNOM ou NOM-PRÉNOM
                parts = re.split(r'[ -]', structure, 1)
                if len(parts) >= 2:
                    lawyer_info['nom'] = parts[0]
                    lawyer_info['prenom'] = parts[1]
                else:
                    lawyer_info['nom'] = structure
            
            # Adresse - essayer plusieurs approches
            adresse_parts = []
            
            # Première adresse
            adresse1 = self.extract_text_safely(card, ".coordonnees .adresse")
            if not adresse1:
                adresse1 = self.extract_text_safely(card, ".adresse")
            if adresse1:
                adresse_parts.append(adresse1)
            
            # Deuxième adresse
            adresse2 = self.extract_text_safely(card, ".coordonnees .adresse2")
            if not adresse2:
                adresse2 = self.extract_text_safely(card, ".adresse2")
            if adresse2:
                adresse_parts.append(adresse2)
            
            lawyer_info['adresse'] = " - ".join(adresse_parts)
            
            # Code postal et ville
            cpville = self.extract_text_safely(card, ".coordonnees .cpville")
            if not cpville:
                cpville = self.extract_text_safely(card, ".cpville")
            
            if cpville:
                # Format : CODE_POSTAL VILLE
                match = re.match(r'(\d{5})\s+(.+)', cpville)
                if match:
                    lawyer_info['code_postal'] = match.group(1)
                    lawyer_info['ville'] = match.group(2)
                else:
                    lawyer_info['ville'] = cpville
            
            # Téléphone
            tel_selectors = [".coordonnees .tel", ".tel", ".telephone"]
            for selector in tel_selectors:
                telephone = self.extract_text_safely(card, selector)
                if telephone:
                    # Nettoyer le téléphone
                    tel_clean = re.sub(r'Tél\s*:\s*', '', telephone)
                    lawyer_info['telephone'] = tel_clean.strip()
                    break
            
            # Année d'inscription (prestation de serment)
            date_selectors = [".dateserment", ".serment", "[class*='serment']"]
            for selector in date_selectors:
                date_serment = self.extract_text_safely(card, selector)
                if date_serment:
                    # Extraire l'année
                    match = re.search(r'(\d{4})', date_serment)
                    if match:
                        lawyer_info['annee_inscription'] = match.group(1)
                    break
            
            # URL de détail
            try:
                detail_link = card.find_element(By.CSS_SELECTOR, "a.btnAnnuaireDetail, a[href*='maitre-'], a[title*='détail']")
                lawyer_info['detail_url'] = detail_link.get_attribute('href')
            except NoSuchElementException:
                try:
                    # Chercher n'importe quel lien vers une page de détail
                    links = card.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute('href')
                        if href and 'maitre-' in href:
                            lawyer_info['detail_url'] = href
                            break
                except:
                    pass
            
            # URL de contact
            try:
                contact_link = card.find_element(By.CSS_SELECTOR, "a.btnAnnuaireContact, a[title*='contact']")
                lawyer_info['contact_url'] = contact_link.get_attribute('href')
            except NoSuchElementException:
                pass
            
            return lawyer_info
            
        except Exception as e:
            print(f"⚠️  Erreur lors de l'extraction des infos de carte: {e}")
            return lawyer_info
    
    def get_detailed_lawyer_info(self, lawyer_info):
        """Récupère les informations détaillées d'un avocat depuis sa page de détail"""
        if not lawyer_info['detail_url']:
            return lawyer_info
        
        try:
            print(f"  📄 Récupération des détails pour {lawyer_info['nom_complet']}...")
            
            # Ouvrir la page de détail dans un nouvel onglet
            self.driver.execute_script(f"window.open('{lawyer_info['detail_url']}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Attendre le chargement
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            
            # Extraire l'email si présent
            try:
                email_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
                if email_elements:
                    email_href = email_elements[0].get_attribute('href')
                    encoded_email = email_href.replace('mailto:', '')
                    decoded_email = self.decode_email(encoded_email)
                    lawyer_info['email'] = decoded_email
                    print(f"    ✉️  Email trouvé: {decoded_email}")
            except Exception as e:
                print(f"    ⚠️  Erreur extraction email: {e}")
            
            # Extraire les spécialisations
            try:
                # Chercher différents sélecteurs pour les spécialisations
                specialisation_selectors = [
                    ".specialisations",
                    ".specialites", 
                    "[class*='special']",
                    ".competences",
                    "[class*='competence']"
                ]
                
                specialisations = []
                for selector in specialisation_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and len(text) > 3 and text not in specialisations:
                            specialisations.append(text)
                
                if specialisations:
                    lawyer_info['specialisations'] = " | ".join(specialisations)
                    print(f"    🎯 Spécialisations: {len(specialisations)} trouvées")
            except Exception as e:
                print(f"    ⚠️  Erreur extraction spécialisations: {e}")
            
            # Extraire le téléphone si pas encore trouvé
            if not lawyer_info['telephone']:
                try:
                    tel_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Tél') or contains(text(), 'Tel') or contains(text(), '+33') or contains(text(), '01') or contains(text(), '06')]")
                    for elem in tel_elements:
                        text = elem.text.strip()
                        # Chercher un numéro de téléphone
                        tel_match = re.search(r'[\+\d\s\(\)\-\.]{10,}', text)
                        if tel_match:
                            lawyer_info['telephone'] = tel_match.group(0).strip()
                            print(f"    📞 Téléphone trouvé: {lawyer_info['telephone']}")
                            break
                except Exception:
                    pass
            
            # Fermer l'onglet et revenir à l'original
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return lawyer_info
            
        except Exception as e:
            print(f"  ⚠️  Erreur lors de la récupération des détails: {e}")
            # Assurer qu'on revient à l'onglet original
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return lawyer_info
    
    def scrape_all_lawyers(self):
        """Scrape tous les avocats de l'annuaire"""
        print("🚀 Début du scraping complet")
        
        try:
            # Aller à la page principale
            print("📄 Chargement de la page principale...")
            self.driver.get("https://www.avocats91.com/lordre-des-avocats/annuaire-des-avocats.htm")
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Attendre le chargement du contenu
            if not self.wait_for_content_load():
                return []
            
            # Récupérer toutes les cartes d'avocats
            cards = self.get_lawyer_cards()
            if not cards:
                return []
            
            total_lawyers = len(cards)
            lawyers_data = []
            
            print(f"📊 Extraction de {total_lawyers} avocats...")
            
            for i, card in enumerate(cards):
                print(f"\n--- Avocat {i+1}/{total_lawyers} ---")
                
                try:
                    lawyer_info = self.extract_lawyer_info_from_card(card)
                    
                    print(f"Nom: {lawyer_info['nom_complet']}")
                    print(f"Adresse: {lawyer_info['adresse']} {lawyer_info['code_postal']} {lawyer_info['ville']}")
                    
                    # Récupérer les détails (email, spécialisations)
                    lawyer_info = self.get_detailed_lawyer_info(lawyer_info)
                    
                    lawyers_data.append(lawyer_info)
                    
                    # Sauvegarder périodiquement
                    if (i + 1) % 50 == 0:
                        self.save_results(lawyers_data, f"essonne_partial_{i+1}")
                        print(f"💾 Sauvegarde intermédiaire à {i+1} avocats")
                    
                    # Pause entre les extractions pour éviter la surcharge
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"❌ Erreur pour l'avocat {i+1}: {e}")
                    continue
            
            return lawyers_data
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return []
    
    def test_improved_extraction(self, num_lawyers=3):
        """Test amélioré sur quelques avocats"""
        print("🧪 Test amélioré de l'extraction")
        
        try:
            # Aller à la page principale
            print("📄 Chargement de la page principale...")
            self.driver.get("https://www.avocats91.com/lordre-des-avocats/annuaire-des-avocats.htm")
            
            # Accepter les cookies
            self.accept_cookies()
            
            # Attendre le chargement du contenu
            if not self.wait_for_content_load():
                return []
            
            # Sauvegarder une carte pour debug
            cards = self.get_lawyer_cards()
            if cards:
                with open('/Users/paularnould/essonne_card_debug.html', 'w', encoding='utf-8') as f:
                    f.write(cards[0].get_attribute('outerHTML'))
                print("🐛 Carte debug sauvegardée")
            
            # Test sur les premiers avocats
            test_limit = min(num_lawyers, len(cards))
            lawyers_data = []
            
            for i in range(test_limit):
                print(f"\n--- Test avocat {i+1}/{test_limit} ---")
                
                card = cards[i]
                lawyer_info = self.extract_lawyer_info_from_card(card)
                lawyer_info = self.get_detailed_lawyer_info(lawyer_info)
                
                print(f"✅ Résultat:")
                for key, value in lawyer_info.items():
                    if value:
                        print(f"   {key}: {value}")
                
                lawyers_data.append(lawyer_info)
                time.sleep(2)
            
            return lawyers_data
            
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            return []
    
    def save_results(self, lawyers_data, filename_prefix="essonne_lawyers"):
        """Sauvegarde les résultats"""
        if not lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_file = f'/Users/paularnould/{filename_prefix}_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(lawyers_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde CSV
        csv_file = f'/Users/paularnould/{filename_prefix}_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if lawyers_data:
                writer = csv.DictWriter(f, fieldnames=lawyers_data[0].keys())
                writer.writeheader()
                writer.writerows(lawyers_data)
        
        # Emails seulement
        emails_file = f'/Users/paularnould/{filename_prefix}_emails_{timestamp}.txt'
        emails = [lawyer.get('email', '') for lawyer in lawyers_data if lawyer.get('email')]
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        # Rapport détaillé
        report_file = f'/Users/paularnould/{filename_prefix}_rapport_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"RAPPORT D'EXTRACTION - AVOCATS ESSONNE\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total avocats: {len(lawyers_data)}\n")
            f.write(f"Emails trouvés: {len(emails)}\n")
            f.write(f"Téléphones: {len([l for l in lawyers_data if l.get('telephone')])}\n")
            f.write(f"Spécialisations: {len([l for l in lawyers_data if l.get('specialisations')])}\n\n")
            
            f.write("DÉTAILS PAR AVOCAT:\n")
            f.write("-"*30 + "\n")
            for i, lawyer in enumerate(lawyers_data, 1):
                f.write(f"{i}. {lawyer.get('nom_complet', 'N/A')}\n")
                f.write(f"   Email: {lawyer.get('email', 'N/A')}\n")
                f.write(f"   Téléphone: {lawyer.get('telephone', 'N/A')}\n")
                f.write(f"   Ville: {lawyer.get('ville', 'N/A')}\n")
                f.write(f"   Année: {lawyer.get('annee_inscription', 'N/A')}\n")
                if lawyer.get('specialisations'):
                    f.write(f"   Spécialisations: {lawyer.get('specialisations')}\n")
                f.write("\n")
        
        print(f"✅ Résultats sauvegardés:")
        print(f"   📄 JSON: {json_file}")
        print(f"   📊 CSV: {csv_file}")
        print(f"   ✉️  Emails: {emails_file}")
        print(f"   📋 Rapport: {report_file}")
        print(f"   📈 {len(lawyers_data)} avocats, {len(emails)} emails")
    
    def close(self):
        """Ferme le driver"""
        if self.driver:
            self.driver.quit()

def main():
    """Fonction principale"""
    print("🔧 Scraper Avocats Essonne - Version Finale")
    print("="*50)
    
    # Demander le mode d'exécution
    print("Modes disponibles:")
    print("1. Test rapide (3 avocats)")
    print("2. Scraping complet (tous les avocats)")
    
    choice = input("Choisir le mode (1 ou 2): ").strip()
    
    headless_choice = input("Mode headless (sans fenêtre) ? (o/n): ").strip().lower()
    headless = headless_choice == 'o'
    
    scraper = EssonneBarScraperFinal(headless=headless)
    
    try:
        if choice == "1":
            print("\n🧪 LANCEMENT DU TEST")
            lawyers_data = scraper.test_improved_extraction(3)
            scraper.save_results(lawyers_data, "essonne_test")
        elif choice == "2":
            print("\n🚀 LANCEMENT DU SCRAPING COMPLET")
            confirm = input("Confirmer le scraping de tous les avocats ? (o/n): ").strip().lower()
            if confirm == 'o':
                lawyers_data = scraper.scrape_all_lawyers()
                scraper.save_results(lawyers_data, "essonne_complet")
            else:
                print("❌ Scraping annulé")
                return
        else:
            print("❌ Choix invalide")
            return
        
        if lawyers_data:
            print(f"\n✅ Extraction terminée! {len(lawyers_data)} avocats traités")
            
            # Résumé des données extraites
            emails_count = len([l for l in lawyers_data if l.get('email')])
            phones_count = len([l for l in lawyers_data if l.get('telephone')])
            specializations_count = len([l for l in lawyers_data if l.get('specialisations')])
            
            print(f"📊 Résumé final:")
            print(f"   ✉️  Emails trouvés: {emails_count}/{len(lawyers_data)}")
            print(f"   📞 Téléphones: {phones_count}/{len(lawyers_data)}")
            print(f"   🎯 Spécialisations: {specializations_count}/{len(lawyers_data)}")
        else:
            print("\n❌ Extraction échouée")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()