#!/usr/bin/env python3
"""
Script de scraping pour l'annuaire des avocats du barreau du Havre
https://avocatslehavre.fr/choisir-son-avocat/trouver-son-avocat/annuaire-des-avocats/

Analyse de la structure:
- Les avocats sont listés dans des divs avec la classe 'bloc_profil_avocat'
- Chaque avocat a un bouton "Voir le profil" avec un attribut 'id-user'
- Les profils sont chargés via AJAX en appelant 'ajax_profil_avocat'
- L'endpoint AJAX est : https://avocatslehavre.fr/wp-admin/admin-ajax.php
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from typing import Dict, List, Optional
import re
from datetime import datetime

class AvocatsHavreScraper:
    """Scraper pour l'annuaire des avocats du barreau du Havre"""
    
    def __init__(self):
        self.base_url = "https://avocatslehavre.fr/choisir-son-avocat/trouver-son-avocat/annuaire-des-avocats/"
        self.ajax_url = "https://avocatslehavre.fr/wp-admin/admin-ajax.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.avocats_data = []
        
    def get_avocat_list(self) -> List[Dict]:
        """
        Récupère la liste des avocats depuis la page principale
        
        Returns:
            Liste des avocats avec leurs informations de base
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Récupération de la page principale...")
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Erreur lors de la récupération de la page: {e}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        avocats = []
        
        # Recherche de tous les blocs d'avocats
        blocs_avocats = soup.find_all('div', class_='bloc_profil_avocat')
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(blocs_avocats)} avocats trouvés sur la page")
        
        for bloc in blocs_avocats:
            avocat_info = {}
            
            # Extraction du nom
            nom_elem = bloc.find('div', class_='nom_avocat')
            if nom_elem:
                avocat_info['nom'] = nom_elem.get_text(strip=True)
            
            # Extraction de la société/cabinet
            societe_elem = bloc.find('div', class_='societe_avocat')
            if societe_elem:
                avocat_info['cabinet'] = societe_elem.get_text(strip=True)
            
            # Extraction de l'ID utilisateur pour le profil
            button = bloc.find('button', class_='voir_profil_avocat')
            if button and button.has_attr('id-user'):
                avocat_info['id_user'] = button['id-user']
            
            # Extraction de l'image si disponible
            img_wrapper = bloc.find('div', class_='visuel_avocat')
            if img_wrapper and img_wrapper.has_attr('data-img'):
                avocat_info['photo_url'] = img_wrapper['data-img']
            
            # Extraction de la lettre initiale (pour le filtre alphabétique)
            classes = bloc.get('class', [])
            for classe in classes:
                if len(classe) == 1 and classe.isalpha():
                    avocat_info['lettre'] = classe
                    break
            
            if avocat_info:
                avocats.append(avocat_info)
                
        return avocats
    
    def get_avocat_profile(self, id_user: str) -> Optional[Dict]:
        """
        Récupère le profil détaillé d'un avocat via AJAX
        
        Args:
            id_user: L'ID utilisateur de l'avocat
            
        Returns:
            Dictionnaire avec les informations détaillées du profil
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Récupération du profil ID {id_user}...")
        
        # Préparation des données pour la requête AJAX
        data = {
            'action': 'ajax_profil_avocat',
            'function': 'get_profile',
            'id_user': id_user
        }
        
        # Headers spécifiques pour la requête AJAX
        ajax_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.base_url,
            'Origin': 'https://avocatslehavre.fr'
        }
        
        try:
            response = self.session.post(
                self.ajax_url, 
                data=data, 
                headers=ajax_headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Le contenu retourné est du HTML dans la réponse AJAX
            profile_html = response.text
            
            # Parser le HTML du profil
            profile_data = self.parse_profile_html(profile_html, id_user)
            
            return profile_data
            
        except requests.RequestException as e:
            print(f"  Erreur lors de la récupération du profil {id_user}: {e}")
            return None
    
    def parse_profile_html(self, html_content: str, id_user: str) -> Dict:
        """
        Parse le HTML du profil retourné par AJAX
        
        Args:
            html_content: Le HTML du profil
            id_user: L'ID de l'utilisateur
            
        Returns:
            Dictionnaire avec les informations extraites
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        profile = {'id_user': id_user}
        
        # Extraction du nom complet
        nom_elem = soup.find('h1', class_='modal_nom_avocat')
        if not nom_elem:
            nom_elem = soup.find('div', class_='modal_nom_avocat')
        if nom_elem:
            profile['nom_complet'] = nom_elem.get_text(strip=True)
        
        # Extraction du cabinet
        cabinet_elem = soup.find('div', class_='modal_societe')
        if not cabinet_elem:
            cabinet_elem = soup.find('div', class_='societe_avocat')
        if cabinet_elem:
            profile['cabinet'] = cabinet_elem.get_text(strip=True)
        
        # Extraction de l'adresse
        adresse_elem = soup.find('div', class_='modal_adresse')
        if not adresse_elem:
            adresse_elem = soup.find('div', class_='adresse')
        if adresse_elem:
            adresse_lines = []
            for line in adresse_elem.stripped_strings:
                adresse_lines.append(line)
            profile['adresse'] = ', '.join(adresse_lines)
        
        # Extraction du téléphone
        tel_elem = soup.find('div', class_='modal_tel')
        if not tel_elem:
            tel_elem = soup.find('a', href=re.compile(r'tel:'))
        if tel_elem:
            if tel_elem.name == 'a':
                profile['telephone'] = tel_elem.get_text(strip=True)
            else:
                tel_text = tel_elem.get_text(strip=True)
                # Nettoyer le numéro
                tel_match = re.search(r'[\d\s\.\-\+]+', tel_text)
                if tel_match:
                    profile['telephone'] = tel_match.group().strip()
        
        # Extraction du fax
        fax_elem = soup.find('div', class_='modal_fax')
        if fax_elem:
            fax_text = fax_elem.get_text(strip=True)
            fax_match = re.search(r'[\d\s\.\-\+]+', fax_text)
            if fax_match:
                profile['fax'] = fax_match.group().strip()
        
        # Extraction de l'email
        email_elem = soup.find('a', href=re.compile(r'mailto:'))
        if email_elem:
            email = email_elem.get('href', '').replace('mailto:', '')
            if email:
                profile['email'] = email
        
        # Extraction du site web
        site_elem = soup.find('a', class_='modal_site')
        if not site_elem:
            site_elem = soup.find('a', href=re.compile(r'^https?://(?!.*avocatslehavre)'))
        if site_elem:
            profile['site_web'] = site_elem.get('href', '')
        
        # Extraction des spécialisations
        specialisations = []
        spec_container = soup.find('div', class_='modal_specialisations')
        if not spec_container:
            spec_container = soup.find('div', class_='bloc_mentions_spec')
        if spec_container:
            for spec in spec_container.find_all(['li', 'div', 'span']):
                spec_text = spec.get_text(strip=True)
                if spec_text and spec_text not in specialisations:
                    specialisations.append(spec_text)
        if specialisations:
            profile['specialisations'] = ' | '.join(specialisations)
        
        # Extraction des langues parlées
        langues_elem = soup.find('div', class_='modal_langues')
        if langues_elem:
            profile['langues'] = langues_elem.get_text(strip=True)
        
        # Extraction de la date de prestation de serment
        serment_elem = soup.find('div', class_='modal_serment')
        if serment_elem:
            serment_text = serment_elem.get_text(strip=True)
            # Extraire la date
            date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', serment_text)
            if date_match:
                profile['date_serment'] = date_match.group()
        
        return profile
    
    def scrape_all(self, delay: float = 1.0, save_csv: bool = True) -> List[Dict]:
        """
        Scrape tous les avocats de l'annuaire
        
        Args:
            delay: Délai entre chaque requête AJAX (en secondes)
            save_csv: Si True, sauvegarde les résultats dans un CSV
            
        Returns:
            Liste de tous les profils d'avocats
        """
        print(f"\n{'='*60}")
        print(f"Début du scraping de l'annuaire des avocats du Havre")
        print(f"{'='*60}\n")
        
        # Étape 1: Récupérer la liste des avocats
        avocats_liste = self.get_avocat_list()
        
        if not avocats_liste:
            print("Aucun avocat trouvé sur la page")
            return []
        
        print(f"\n{len(avocats_liste)} avocats à traiter")
        print(f"Délai entre les requêtes: {delay} secondes\n")
        
        # Étape 2: Récupérer les profils détaillés
        profils_complets = []
        errors_count = 0
        
        for i, avocat in enumerate(avocats_liste, 1):
            print(f"\n[{i}/{len(avocats_liste)}] Traitement de {avocat.get('nom', 'Avocat inconnu')}")
            
            if 'id_user' not in avocat:
                print("  ⚠ Pas d'ID utilisateur, profil ignoré")
                errors_count += 1
                continue
            
            # Récupération du profil détaillé
            profile = self.get_avocat_profile(avocat['id_user'])
            
            if profile:
                # Fusionner les informations de base avec le profil détaillé
                avocat_complet = {**avocat, **profile}
                profils_complets.append(avocat_complet)
                print(f"  ✓ Profil récupéré avec succès")
            else:
                # Garder au moins les informations de base
                profils_complets.append(avocat)
                errors_count += 1
                print(f"  ✗ Erreur lors de la récupération du profil")
            
            # Pause entre les requêtes
            if i < len(avocats_liste):
                time.sleep(delay)
        
        print(f"\n{'='*60}")
        print(f"Scraping terminé!")
        print(f"Profils récupérés: {len(profils_complets)}")
        print(f"Erreurs: {errors_count}")
        print(f"{'='*60}\n")
        
        # Sauvegarde en CSV si demandé
        if save_csv and profils_complets:
            self.save_to_csv(profils_complets)
        
        return profils_complets
    
    def save_to_csv(self, data: List[Dict], filename: str = None):
        """
        Sauvegarde les données dans un fichier CSV
        
        Args:
            data: Liste des profils d'avocats
            filename: Nom du fichier CSV (par défaut: avocats_havre_YYYYMMDD_HHMMSS.csv)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"avocats_havre_{timestamp}.csv"
        
        if not data:
            print("Aucune donnée à sauvegarder")
            return
        
        # Déterminer toutes les colonnes possibles
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        # Ordre préféré des colonnes
        preferred_order = [
            'nom', 'nom_complet', 'cabinet', 'adresse', 
            'telephone', 'fax', 'email', 'site_web',
            'specialisations', 'langues', 'date_serment',
            'lettre', 'id_user', 'photo_url'
        ]
        
        # Organiser les colonnes
        fieldnames = []
        for key in preferred_order:
            if key in all_keys:
                fieldnames.append(key)
        
        # Ajouter les colonnes restantes
        for key in all_keys:
            if key not in fieldnames:
                fieldnames.append(key)
        
        # Écriture du CSV
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            print(f"✓ Données sauvegardées dans: {filename}")
            print(f"  {len(data)} lignes écrites")
            
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde: {e}")
    
    def scrape_with_selenium(self) -> List[Dict]:
        """
        Alternative avec Selenium pour gérer le JavaScript si nécessaire
        Cette méthode utilise Selenium pour automatiser le navigateur
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            
            print("Utilisation de Selenium pour le scraping...")
            
            # Configuration du navigateur
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Mode sans interface graphique
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            wait = WebDriverWait(driver, 10)
            
            profils = []
            
            try:
                # Charger la page
                driver.get(self.base_url)
                
                # Attendre que les boutons soient chargés
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'voir_profil_avocat')))
                
                # Récupérer tous les boutons de profil
                buttons = driver.find_elements(By.CLASS_NAME, 'voir_profil_avocat')
                total_avocats = len(buttons)
                print(f"{total_avocats} avocats trouvés")
                
                # Pour chaque avocat
                for i in range(total_avocats):
                    # Re-récupérer les boutons car la page peut avoir changé
                    buttons = driver.find_elements(By.CLASS_NAME, 'voir_profil_avocat')
                    
                    if i >= len(buttons):
                        break
                    
                    button = buttons[i]
                    
                    # Récupérer les infos de base avant de cliquer
                    bloc = button.find_element(By.XPATH, './ancestor::div[@class="bloc_profil_avocat"]')
                    
                    try:
                        nom = bloc.find_element(By.CLASS_NAME, 'nom_avocat').text
                    except:
                        nom = "Nom inconnu"
                    
                    print(f"[{i+1}/{total_avocats}] Traitement de {nom}")
                    
                    # Cliquer sur le bouton
                    driver.execute_script("arguments[0].click();", button)
                    
                    # Attendre que le modal s'ouvre
                    time.sleep(1)
                    
                    try:
                        # Attendre et récupérer le modal
                        modal = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'modal_avocat')))
                        
                        # Extraire les informations du modal
                        profile = {'nom': nom}
                        
                        # Extraction des différents éléments
                        try:
                            profile['nom_complet'] = modal.find_element(By.CLASS_NAME, 'modal_nom_avocat').text
                        except: pass
                        
                        try:
                            profile['cabinet'] = modal.find_element(By.CLASS_NAME, 'modal_societe').text
                        except: pass
                        
                        try:
                            profile['adresse'] = modal.find_element(By.CLASS_NAME, 'modal_adresse').text
                        except: pass
                        
                        try:
                            profile['telephone'] = modal.find_element(By.CLASS_NAME, 'modal_tel').text
                        except: pass
                        
                        try:
                            profile['email'] = modal.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]').get_attribute('href').replace('mailto:', '')
                        except: pass
                        
                        profils.append(profile)
                        
                        # Fermer le modal
                        try:
                            close_button = modal.find_element(By.CLASS_NAME, 'close_modal')
                            close_button.click()
                        except:
                            # Si pas de bouton fermer, rafraîchir la page
                            driver.refresh()
                            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'voir_profil_avocat')))
                        
                        time.sleep(0.5)
                        
                    except Exception as e:
                        print(f"  Erreur lors de l'extraction du profil: {e}")
                        # Rafraîchir en cas d'erreur
                        driver.refresh()
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'voir_profil_avocat')))
                
            finally:
                driver.quit()
                
            return profils
            
        except ImportError:
            print("Selenium n'est pas installé. Installez-le avec: pip install selenium")
            print("Vous aurez aussi besoin de ChromeDriver: https://chromedriver.chromium.org/")
            return []


def main():
    """Fonction principale"""
    
    print("\n" + "="*60)
    print(" SCRAPER - Annuaire des Avocats du Barreau du Havre")
    print("="*60)
    print("\nOptions disponibles:")
    print("1. Scraping avec requests/BeautifulSoup (recommandé)")
    print("2. Scraping avec Selenium (plus lent mais plus robuste)")
    print("3. Test rapide (premiers 5 profils seulement)")
    
    import sys
    if "--test" in sys.argv:
        choice = "3"
        print("Mode test activé automatiquement")
    else:
        choice = input("\nVotre choix (1/2/3) [défaut: 1]: ").strip() or "1"
    
    scraper = AvocatsHavreScraper()
    
    if choice == "1":
        # Scraping normal avec requests
        if "--test" in sys.argv:
            delay = 1.0
        else:
            delay_input = input("Délai entre les requêtes en secondes [défaut: 1.0]: ").strip()
            delay = float(delay_input) if delay_input else 1.0
        
        results = scraper.scrape_all(delay=delay, save_csv=True)
        
    elif choice == "2":
        # Scraping avec Selenium
        results = scraper.scrape_with_selenium()
        if results:
            scraper.save_to_csv(results)
            
    elif choice == "3":
        # Test rapide
        print("\nMode test: récupération des 5 premiers profils...")
        avocats_liste = scraper.get_avocat_list()[:5]
        results = []
        
        for avocat in avocats_liste:
            if 'id_user' in avocat:
                profile = scraper.get_avocat_profile(avocat['id_user'])
                if profile:
                    results.append({**avocat, **profile})
                time.sleep(0.5)
        
        # Affichage des résultats du test
        print("\n" + "="*60)
        print("Résultats du test:")
        print("="*60)
        for i, avocat in enumerate(results, 1):
            print(f"\n{i}. {avocat.get('nom', 'N/A')}")
            print(f"   Cabinet: {avocat.get('cabinet', 'N/A')}")
            print(f"   Téléphone: {avocat.get('telephone', 'N/A')}")
            print(f"   Email: {avocat.get('email', 'N/A')}")
    
    else:
        print("Choix invalide")
        return
    
    print("\n✓ Script terminé")


if __name__ == "__main__":
    main()