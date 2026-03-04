#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper pour le Barreau de Saint-Denis (La Réunion)
Extrait les informations complètes des avocats avec noms/prénoms corrigés et domaines d'intervention

Auteur: Claude Code
Date: 2026-02-19
Version: 1.0
"""

import time
import csv
import json
import logging
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SaintDenisScraper:
    """Scraper pour extraire tous les avocats du Barreau de Saint-Denis"""
    
    def __init__(self):
        self.driver = None
        self.base_url = "https://barreau-saint-denis.re"
        self.annuaire_url = f"{self.base_url}/annuaire-des-avocats/"
        self.avocats_extraits = []

    def setup_driver(self):
        """Configure Chrome en mode headless pour l'extraction"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("🚀 Driver Chrome configuré")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur configuration Chrome: {e}")
            return False

    def reconnect_driver(self):
        """Reconnecte le driver Chrome en cas de problème"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        return self.setup_driver()

    def collect_all_urls(self):
        """Collecte toutes les URLs d'avocats depuis l'annuaire paginé"""
        logger.info("🔍 Collecte des URLs d'avocats...")
        
        self.driver.get(self.annuaire_url)
        time.sleep(3)
        
        all_urls = []
        page_num = 1
        
        while True:
            # Extraire les URLs de la page courante
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/listing/']")
            page_urls = []
            
            for link in links:
                href = link.get_attribute('href')
                if href and '/listing/' in href and href not in all_urls:
                    page_urls.append(href)
            
            logger.info(f"📋 Page {page_num}: {len(page_urls)} nouvelles URLs")
            all_urls.extend(page_urls)
            
            # Chercher le bouton "Charger plus" ou pagination suivante
            try:
                load_more_button = self.driver.find_element(By.CSS_SELECTOR, "[class*='load']")
                if load_more_button.is_displayed():
                    self.driver.execute_script("arguments[0].click();", load_more_button)
                    time.sleep(3)
                    page_num += 1
                else:
                    break
            except:
                break
        
        logger.info(f"🎯 Total URLs collectées: {len(all_urls)}")
        return all_urls

    def parse_name_corrected(self, full_name):
        """
        Parse correctement les noms du site Saint-Denis en format "NOM Prénom"
        Retourne (prénom, nom) dans le bon ordre
        """
        if not full_name or full_name.strip() == "":
            return "", ""
            
        # Nettoyer le nom complet
        full_name = re.sub(r'\b\d[\d\s\-\.]{7,}\b', '', full_name)
        full_name = full_name.strip()
        
        if not full_name:
            return "", ""
        
        # Particules françaises courantes
        particules = ['de', 'du', 'des', 'le', 'la', 'van', 'von', 'da', 'di', 'del']
        
        parts = full_name.split()
        
        if len(parts) == 1:
            return parts[0], ""
        elif len(parts) == 2:
            # Format "NOM Prénom" → on inverse pour avoir "Prénom NOM"
            return parts[1], parts[0]
        else:
            # Pour les noms multiples
            
            # Cas 1: "MOUSSA-CARPENTIER Sanaze" → nom composé + prénom
            if '-' in parts[0]:
                return parts[-1], ' '.join(parts[:-1])
            
            # Cas 2: "DE MALET Vimala" → particule + nom + prénom
            if parts[0].lower() in particules:
                return parts[-1], ' '.join(parts[:-1])
            
            # Cas 3: nom composé sans trait d'union
            # Le dernier mot est généralement le prénom
            last_word = parts[-1]
            
            # Heuristique: si le dernier mot ressemble à un prénom
            if (len(last_word) >= 3 and 
                len([c for c in last_word if c.isupper()]) <= 2):
                return last_word, ' '.join(parts[:-1])
            
            # Fallback: dernier mot = prénom
            return parts[-1], ' '.join(parts[:-1])

    def extract_domaines_intervention(self, soup):
        """
        Extrait les domaines d'intervention depuis le bloc HTML spécifique
        """
        domaines = []
        
        # Chercher tous les blocs avec class="element"
        elements = soup.find_all('div', class_='element')
        for element in elements:
            # Vérifier le titre h5
            h5 = element.find('h5')
            if h5 and 'Domaines d\'intervention' in h5.text:
                # Extraire tous les spans dans ce bloc
                spans = element.find_all('span')
                for span in spans:
                    if span.text.strip():
                        domaines.append(span.text.strip())
                break  # On a trouvé le bon bloc, sortir de la boucle
        
        return '; '.join(domaines) if domaines else ""

    def extract_avocat_info_robust(self, url, index, total):
        """
        Extrait les informations d'un avocat avec reconnexion automatique
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Vérifier que le driver est actif
                try:
                    self.driver.current_url
                except (WebDriverException, AttributeError):
                    if not self.reconnect_driver():
                        return None

                logger.info(f"🔍 [{index}/{total}] (tentative {attempt + 1}) {url}")
                
                self.driver.get(url)
                time.sleep(2)
                
                # Parser le HTML avec BeautifulSoup
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Extraction du nom complet depuis plusieurs sources
                nom_element = soup.find('h1', class_='case27-primary-text')
                full_name = nom_element.text.strip() if nom_element else ""
                
                # Si pas trouvé, essayer depuis JSON-LD
                if not full_name:
                    json_scripts = soup.find_all('script', type='application/ld+json')
                    for script in json_scripts:
                        try:
                            data = json.loads(script.string)
                            if isinstance(data, dict) and 'name' in data:
                                full_name = data['name']
                                break
                        except:
                            continue
                
                # Parser correctement prénom et nom
                prenom, nom = self.parse_name_corrected(full_name)
                
                # Extraction email depuis JSON-LD
                email = ""
                json_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'email' in data:
                            email = data['email']
                            break
                    except:
                        continue
                
                # Extraction téléphone depuis JSON-LD
                telephone = ""
                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'telephone' in data:
                            telephone = data['telephone']
                            break
                    except:
                        continue
                
                # Extraction des domaines d'intervention
                domaines = self.extract_domaines_intervention(soup)
                
                # Extraction année d'inscription (si disponible)
                annee = ""
                annee_pattern = r'Inscrit.*?(\d{4})'
                annee_match = re.search(annee_pattern, soup.text)
                if annee_match:
                    annee = annee_match.group(1)
                
                # Extraction adresse
                adresse = ""
                adresse_element = soup.find('div', class_='address')
                if adresse_element:
                    adresse = adresse_element.get_text(separator=' ', strip=True)
                
                avocat_info = {
                    'prenom': prenom,
                    'nom': nom,
                    'annee_inscription': annee,
                    'domaines_intervention': domaines,
                    'structure': "",  # Peut être ajouté si nécessaire
                    'source_url': url,
                    'adresse': adresse,
                    'telephone': telephone,
                    'email': email,
                    'autres_infos': ""
                }
                
                # Log du résultat
                email_status = "✓" if email else "✗"
                tel_status = "✓" if telephone else "✗"
                domaines_status = "✓" if domaines else "✗"
                
                logger.info(f"✅ {prenom} {nom} | Email: {email_status} | Tel: {tel_status} | Domaines: {domaines_status}")
                
                return avocat_info
                
            except Exception as e:
                logger.error(f"❌ Erreur [{index}/{total}] (tentative {attempt + 1}) {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    return None
        
        return None

    def save_backup(self, filename_prefix, avocats_extraits):
        """Sauvegarde intermédiaire"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_file = f"{filename_prefix}_{len(avocats_extraits)}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(avocats_extraits, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Sauvegarde créée: {json_file}")

    def save_final_results(self, avocats_extraits):
        """Sauvegarde les résultats finaux"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"SAINT_DENIS_FINAL_{len(avocats_extraits)}_avocats_{timestamp}"
        
        # Fichier CSV
        csv_file = f"{base_filename}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if avocats_extraits:
                writer = csv.DictWriter(f, fieldnames=avocats_extraits[0].keys())
                writer.writeheader()
                writer.writerows(avocats_extraits)
        
        # Fichier JSON
        json_file = f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(avocats_extraits, f, ensure_ascii=False, indent=2)
        
        # Fichier emails uniquement
        emails = [av['email'] for av in avocats_extraits if av['email']]
        emails_file = f"SAINT_DENIS_EMAILS_{timestamp}.txt"
        with open(emails_file, 'w', encoding='utf-8') as f:
            for i, email in enumerate(emails, 1):
                f.write(f"{i:>6}→{email}\n")
        
        # Rapport détaillé
        rapport_file = f"SAINT_DENIS_RAPPORT_{timestamp}.txt"
        with open(rapport_file, 'w', encoding='utf-8') as f:
            f.write("=== RAPPORT FINAL - BARREAU SAINT-DENIS ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {len(avocats_extraits)} avocats\n\n")
            
            emails_count = sum(1 for av in avocats_extraits if av['email'])
            tels_count = sum(1 for av in avocats_extraits if av['telephone'])
            domaines_count = sum(1 for av in avocats_extraits if av['domaines_intervention'])
            annees_count = sum(1 for av in avocats_extraits if av['annee_inscription'])
            
            f.write("STATISTIQUES:\n")
            f.write(f"- Avec email: {emails_count}\n")
            f.write(f"- Avec téléphone: {tels_count}\n")
            f.write(f"- Avec domaines: {domaines_count}\n")
            f.write(f"- Avec année: {annees_count}\n\n")
            
            f.write("LISTE DÉTAILLÉE:\n")
            f.write("=" * 50 + "\n\n")
            
            for i, avocat in enumerate(avocats_extraits, 1):
                f.write(f" {i:>2}. {avocat['prenom']} {avocat['nom']}\n")
                if avocat['email']:
                    f.write(f"    📧 {avocat['email']}\n")
                if avocat['telephone']:
                    f.write(f"    📞 {avocat['telephone']}\n")
                if avocat['domaines_intervention']:
                    f.write(f"    ⚖️  {avocat['domaines_intervention']}\n")
                if avocat['annee_inscription']:
                    f.write(f"    📅 Inscrit: {avocat['annee_inscription']}\n")
                f.write(f"    🔗 {avocat['source_url']}\n\n")
        
        logger.info("✅ EXTRACTION COMPLÈTE RÉUSSIE !")
        logger.info(f"📊 {len(avocats_extraits)} avocats extraits au total")
        logger.info(f"📧 {emails_count} emails récupérés")
        logger.info(f"⚖️ {domaines_count} profils avec domaines d'intervention")
        logger.info("📁 Consultez les fichiers générés pour les résultats complets")
        
        return csv_file, json_file, emails_file, rapport_file

    def run_extraction(self, collect_urls=True):
        """
        Lance l'extraction complète des avocats
        
        Args:
            collect_urls (bool): Si True, collecte les URLs depuis l'annuaire.
                                Si False, utilise les URLs hardcodées (plus rapide pour les tests)
        """
        logger.info("🚀============================================================")
        logger.info("🚀 EXTRACTION COMPLÈTE - BARREAU SAINT-DENIS")
        logger.info("🚀============================================================")
        
        if not self.setup_driver():
            logger.error("❌ Impossible de configurer Chrome")
            return None
        
        try:
            # Collecte des URLs
            if collect_urls:
                all_urls = self.collect_all_urls()
            else:
                # URLs hardcodées pour les tests rapides
                all_urls = [
                    "https://barreau-saint-denis.re/listing/blameble-ingrid/",
                    "https://barreau-saint-denis.re/listing/moussa-carpentier-sanaze/",
                    "https://barreau-saint-denis.re/listing/simon-lebon-isabelle/",
                    # Ajouter d'autres URLs de test si nécessaire
                ]
            
            if not all_urls:
                logger.error("❌ Aucune URL collectée")
                return None
            
            logger.info(f"📋 {len(all_urls)} URLs à traiter")
            
            # Extraction des informations
            avocats_extraits = []
            
            for index, url in enumerate(all_urls, 1):
                avocat_info = self.extract_avocat_info_robust(url, index, len(all_urls))
                
                if avocat_info:
                    avocats_extraits.append(avocat_info)
                    
                    # Sauvegardes automatiques toutes les 15 extractions
                    if index % 15 == 0:
                        self.save_backup("SAINT_DENIS_BACKUP", avocats_extraits)
                        logger.info(f"💾 Sauvegarde automatique ({index}/{len(all_urls)})")
                    
                    # Statistiques intermédiaires
                    if index % 10 == 0:
                        emails_count = sum(1 for av in avocats_extraits if av['email'])
                        domaines_count = sum(1 for av in avocats_extraits if av['domaines_intervention'])
                        progression = (index / len(all_urls)) * 100
                        logger.info(f"📈 Progression: {progression:.1f}% | Avocats: {len(avocats_extraits)} | Emails: {emails_count} | Domaines: {domaines_count}")
            
            # Sauvegarde finale
            if avocats_extraits:
                files = self.save_final_results(avocats_extraits)
                return files
            else:
                logger.error("❌ Aucun avocat extrait")
                return None
                
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Fonction principale pour lancer l'extraction"""
    scraper = SaintDenisScraper()
    
    # Lancer l'extraction complète
    # collect_urls=True pour une extraction complète depuis l'annuaire
    # collect_urls=False pour utiliser les URLs de test
    files = scraper.run_extraction(collect_urls=True)
    
    if files:
        csv_file, json_file, emails_file, rapport_file = files
        print(f"\n🎉 Extraction terminée avec succès !")
        print(f"📁 Fichiers générés :")
        print(f"   - CSV : {csv_file}")
        print(f"   - JSON: {json_file}")
        print(f"   - Emails: {emails_file}")
        print(f"   - Rapport: {rapport_file}")
    else:
        print("❌ Extraction échouée")

if __name__ == "__main__":
    main()