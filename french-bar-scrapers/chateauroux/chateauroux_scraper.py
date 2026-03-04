#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRAPER DU BARREAU DE CHÂTEAUROUX - AVEC FICHES DÉTAILLÉES
Site web : https://www.avocats-chateauroux.fr/annuaire-des-avocats/
Extraction complète avec consultation des fiches individuelles
"""

import json
import csv
import time
from datetime import datetime
import re
from urllib.parse import urljoin
import unicodedata

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options

class ChateaurouxBarreauScraperAvecFichesDetails:
    def __init__(self, mode_test=True, limite_test=10):
        """
        Initialise le scraper avec fiches détaillées
        """
        self.mode_test = mode_test
        self.limite_test = limite_test
        self.base_url = "https://www.avocats-chateauroux.fr"
        self.annuaire_url = f"{self.base_url}/annuaire-des-avocats/"
        self.avocats = []
        self.driver = None
        
        # Statistiques
        self.stats = {
            'total_avocats': 0,
            'avocats_avec_email': 0,
            'avocats_avec_telephone': 0,
            'avocats_avec_adresse': 0,
            'avocats_avec_structure': 0,
            'avocats_avec_date_serment': 0,
            'avocats_avec_specialites': 0,
            'lettres_traitees': [],
            'erreurs': []
        }
        
    def setup_driver(self, headless=False):
        """Configure et initialise le driver Chrome"""
        options = Options()
        
        # Options pour éviter la détection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Options de performance
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        if headless:
            options.add_argument('--headless')
            
        # User agent réaliste
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✓ Driver Chrome initialisé avec succès")
        except Exception as e:
            print(f"✗ Erreur lors de l'initialisation du driver : {e}")
            raise
            
    def accepter_cookies(self):
        """Accepte les cookies si présents"""
        try:
            time.sleep(2)
            
            selectors = [
                "button[data-accept]",
                "button.cmplz-accept",
                ".cmplz-accept",
                "#accept-cookies",
                ".accept-cookies"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            print("✓ Cookies acceptés")
                            time.sleep(1)
                            return
                except:
                    continue
                    
        except Exception as e:
            pass
            
        print("✓ Cookies acceptés")
        
    def decoder_rot13(self, texte_encode):
        """Décode un texte ROT13"""
        if not texte_encode:
            return ""
        try:
            return ''.join([chr((ord(char) - 97 + 13) % 26 + 97) if 'a' <= char <= 'z' 
                          else chr((ord(char) - 65 + 13) % 26 + 65) if 'A' <= char <= 'Z' 
                          else char for char in texte_encode])
        except:
            return texte_encode
    
    def nettoyer_texte(self, texte):
        """Nettoie et normalise le texte"""
        if not texte:
            return ""
        texte = re.sub(r'\s+', ' ', texte.strip())
        return unicodedata.normalize('NFKD', texte)
    
    def separer_nom_prenom(self, nom_complet):
        """Sépare intelligemment prénom et nom de famille"""
        if not nom_complet:
            return "", ""
            
        nom_complet = self.nettoyer_texte(nom_complet)
        
        # Supprimer les titres courants
        titres = ['Me', 'Maître', 'Dr', 'Docteur', 'Avocat', 'Avocate']
        for titre in titres:
            nom_complet = re.sub(rf'\b{titre}\.?\s+', '', nom_complet, flags=re.IGNORECASE)
        
        # Séparer par espaces
        parties = nom_complet.strip().split()
        
        if len(parties) == 1:
            return "", parties[0]
        elif len(parties) == 2:
            return parties[0], parties[1]
        elif len(parties) == 3:
            # 3 parties : souvent prénom nom1 nom2 ou prénom1 prénom2 nom
            # On prend le premier comme prénom et le reste comme nom
            return parties[0], ' '.join(parties[1:])
        elif len(parties) == 4:
            # 4 parties : souvent prénom1 prénom2 nom1 nom2 ou prénom nom1 nom2 nom3
            # Pour "marie laure briziou henneron", on prend "marie laure" comme prénom
            return ' '.join(parties[:2]), ' '.join(parties[2:])
        else:
            # 5+ parties, prendre les 2 premiers comme prénom
            return ' '.join(parties[:2]), ' '.join(parties[2:])
    
    def obtenir_lettres_disponibles(self):
        """Récupère la liste des lettres disponibles dans l'annuaire"""
        lettres = []
        
        try:
            self.driver.get(self.annuaire_url)
            time.sleep(3)
            
            # Chercher les liens alphabétiques
            links = self.driver.find_elements(By.CSS_SELECTOR, "a.cn-char")
            
            for link in links:
                href = link.get_attribute('href')
                if href and '/char/' in href:
                    lettre = href.split('/char/')[-1].rstrip('/')
                    if lettre and lettre.isalpha() and len(lettre) == 1:
                        lettres.append(lettre.upper())
                        
            # Si aucune lettre trouvée, utiliser une liste par défaut
            if not lettres:
                print("→ Utilisation de la liste de lettres par défaut")
                lettres = ['A', 'B', 'C', 'D', 'F', 'G', 'H', 'J', 'L', 'M', 'O', 'P', 'R', 'S', 'T']
                
            print(f"✓ {len(lettres)} lettres trouvées : {', '.join(sorted(set(lettres)))}")
            
        except Exception as e:
            print(f"✗ Erreur lors de la récupération des lettres : {e}")
            lettres = ['A', 'B', 'C', 'D', 'F', 'G', 'H', 'J', 'L', 'M', 'O', 'P', 'R', 'S', 'T']
            
        return sorted(set(lettres))
        
    def extraire_avocats_lettre(self, lettre):
        """Extrait les avocats pour une lettre donnée"""
        url = f"{self.annuaire_url}char/{lettre}/"
        print(f"\n→ Traitement de la lettre {lettre}...")
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Attendre que la liste soit chargée
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".cn-list-body, .cn-list"))
            )
            
            # Chercher tous les avocats de cette page
            avocats_elements = self.driver.find_elements(By.CSS_SELECTOR, ".cn-list-item.vcard")
            
            if not avocats_elements:
                print(f"  → Aucun avocat trouvé pour la lettre {lettre}")
                return []
                
            print(f"  → {len(avocats_elements)} avocat(s) trouvé(s) pour la lettre {lettre}")
            
            avocats_lettre = []
            
            for element in avocats_elements:
                try:
                    # Vérifier la limite de test
                    if self.mode_test and self.stats['total_avocats'] >= self.limite_test:
                        print(f"\n→ Limite de test atteinte ({self.limite_test} avocats)")
                        return avocats_lettre
                    
                    # Extraire le lien vers la fiche détaillée
                    try:
                        link_element = element.find_element(By.CSS_SELECTOR, "a[href*='/name/'], h4 a")
                        lien_fiche = link_element.get_attribute('href')
                    except:
                        lien_fiche = None
                    
                    if lien_fiche:
                        # Extraire les informations depuis la fiche détaillée
                        avocat = self.extraire_fiche_detaillee(lien_fiche)
                        
                        if avocat and (avocat.get('nom') or avocat.get('prenom')):
                            avocats_lettre.append(avocat)
                            self.stats['total_avocats'] += 1
                            
                            # Mise à jour des statistiques
                            if avocat.get('email'):
                                self.stats['avocats_avec_email'] += 1
                            if avocat.get('telephone'):
                                self.stats['avocats_avec_telephone'] += 1
                            if avocat.get('adresse'):
                                self.stats['avocats_avec_adresse'] += 1
                            if avocat.get('structure'):
                                self.stats['avocats_avec_structure'] += 1
                            if avocat.get('date_serment'):
                                self.stats['avocats_avec_date_serment'] += 1
                            if avocat.get('specialites'):
                                self.stats['avocats_avec_specialites'] += 1
                                
                            nom_complet = f"{avocat.get('prenom', '')} {avocat.get('nom', '')}".strip()
                            print(f"    ✓ {nom_complet}")
                        
                except Exception as e:
                    print(f"    ✗ Erreur pour un avocat : {e}")
                    continue
                    
            self.stats['lettres_traitees'].append(lettre)
            print(f"  → {len(avocats_lettre)} avocat(s) extraits pour la lettre {lettre}")
            return avocats_lettre
            
        except Exception as e:
            print(f"  ✗ Erreur pour la lettre {lettre} : {e}")
            self.stats['erreurs'].append(f"Lettre {lettre}: {str(e)}")
            return []
            
    def extraire_fiche_detaillee(self, url):
        """Extrait toutes les informations depuis la fiche détaillée d'un avocat"""
        try:
            print(f"      → Consultation de : {url}")
            
            # Ouvrir dans un nouvel onglet
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Forcer le rechargement et éviter le cache
            self.driver.get(url)
            time.sleep(2)
            
            # Vérifier qu'on est bien sur la bonne page
            current_url = self.driver.current_url
            if current_url != url:
                print(f"      ⚠️  Redirection détectée : {current_url}")
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            avocat = {
                'url': url,
                'nom': '',
                'prenom': '',
                'structure': '',
                'titre': '',
                'adresse': '',
                'code_postal': '',
                'ville': '',
                'telephone': '',
                'fax': '',
                'email': '',
                'site_web': '',
                'date_serment': '',
                'specialites': '',
                'date_extraction': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Nom et prénom - Extraction depuis l'URL (plus fiable)
            try:
                # Extraire depuis l'URL en premier (plus fiable)
                url_name = url.split('/name/')[-1].replace('/', '').replace('-', ' ')
                prenom, nom = self.separer_nom_prenom(url_name)
                avocat['prenom'] = prenom.title()  # Capitaliser
                avocat['nom'] = nom.upper()  # Nom de famille en majuscules
                print(f"      ✓ Nom extrait depuis URL : {avocat['prenom']} {avocat['nom']}")
                
                # L'URL est plus fiable que le parsing de page, on la conserve
                print(f"      → Utilisation du nom depuis URL (plus fiable que le parsing DOM)")
                    
            except Exception as e:
                print(f"      ✗ Erreur extraction nom : {e}")
                avocat['prenom'] = "INCONNU"
                avocat['nom'] = "INCONNU"
                
            # Titre
            try:
                titre_elem = self.driver.find_element(By.CSS_SELECTOR, ".title")
                avocat['titre'] = self.nettoyer_texte(titre_elem.text)
            except:
                avocat['titre'] = 'Avocat'
                
            # Structure - Recherche améliorée
            try:
                # Method 1: Lien vers organization avec title
                structure_elem = self.driver.find_element(By.CSS_SELECTOR, "a[title*='S.E.L.A.R.L'], a[title*='S.C.P'], a[title*='Cabinet'], a[title*='FIDAL'], a[href*='/organization/']")
                title_attr = structure_elem.get_attribute('title')
                if title_attr:
                    avocat['structure'] = self.nettoyer_texte(title_attr)
                else:
                    avocat['structure'] = self.nettoyer_texte(structure_elem.text)
            except:
                try:
                    # Method 2: Recherche dans le texte de la page
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    structure_patterns = [
                        r'S\.E\.L\.A\.R\.L\.? ([^–]+(?:–[^–\n]+)*)',
                        r'S\.C\.P\.? ([^–]+(?:–[^–\n]+)*)',
                        r'Cabinet ([^–\n]+)',
                        r'FIDAL[^–\n]*'
                    ]
                    
                    for pattern in structure_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            avocat['structure'] = self.nettoyer_texte(match.group(0))
                            break
                except:
                    pass
                
            # Adresse
            try:
                adresse_elem = self.driver.find_element(By.CSS_SELECTOR, ".street-address")
                avocat['adresse'] = self.nettoyer_texte(adresse_elem.text)
            except:
                pass
                
            try:
                cp_elem = self.driver.find_element(By.CSS_SELECTOR, ".postal-code")
                avocat['code_postal'] = self.nettoyer_texte(cp_elem.text)
            except:
                pass
                
            try:
                ville_elem = self.driver.find_element(By.CSS_SELECTOR, ".locality")
                avocat['ville'] = self.nettoyer_texte(ville_elem.text)
            except:
                pass
                
            # Téléphone
            try:
                tel_elem = self.driver.find_element(By.CSS_SELECTOR, ".tel a, .tel")
                tel_text = tel_elem.get_attribute('href') or tel_elem.text
                avocat['telephone'] = self.nettoyer_texte(tel_text.replace('tel:', ''))
            except:
                pass
                
            # Email (ROT13) - amélioration anti-doublons
            try:
                email_elem = self.driver.find_element(By.CSS_SELECTOR, ".qrpelcg")
                email_encode = email_elem.get_attribute('data-ea') or email_elem.text
                if email_encode:
                    email_decode = self.decoder_rot13(email_encode)
                    # Nettoyer et valider l'email
                    email_clean = email_decode.strip().lower()
                    if '@' in email_clean and '.' in email_clean.split('@')[-1]:
                        avocat['email'] = email_clean
            except:
                try:
                    email_elem = self.driver.find_element(By.CSS_SELECTOR, ".email a")
                    email_href = email_elem.get_attribute('href')
                    if email_href and email_href.startswith('mailto:'):
                        email_clean = email_href.replace('mailto:', '').strip().lower()
                        if '@' in email_clean and '.' in email_clean.split('@')[-1]:
                            avocat['email'] = email_clean
                except:
                    pass
                
            # Date de serment - extraire seulement l'année
            try:
                serment_elem = self.driver.find_element(By.CSS_SELECTOR, ".dtstart")
                date_texte = self.nettoyer_texte(serment_elem.text)
                # Extraire l'année avec regex
                annee_match = re.search(r'\b(19|20)\d{2}\b', date_texte)
                if annee_match:
                    avocat['date_serment'] = annee_match.group()
                else:
                    avocat['date_serment'] = date_texte
            except:
                pass
                
            # Site web
            try:
                site_elem = self.driver.find_element(By.CSS_SELECTOR, ".url a")
                avocat['site_web'] = site_elem.get_attribute('href')
            except:
                pass
                
            # Spécialisations - Recherche dans les éléments <strong>
            try:
                specialites_elems = self.driver.find_elements(By.CSS_SELECTOR, "strong")
                specialites_list = []
                
                for elem in specialites_elems:
                    text = self.nettoyer_texte(elem.text)
                    # Vérifier si le texte contient des domaines de droit
                    if text and any(keyword in text.lower() for keyword in ['droit', 'pénal', 'civil', 'famille', 'travail', 'commercial', 'immobilier', 'fiscal', 'public', 'international', 'social', 'administratif', 'pénitentiaire', 'contentieux', 'conseil']) and '–' in text:
                        specialites_list.append(text)
                
                if specialites_list:
                    avocat['specialites'] = '; '.join(specialites_list)
                    
                # Si pas trouvé, chercher d'autres patterns
                if not avocat['specialites']:
                    try:
                        # Chercher dans le contenu de la page
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text
                        # Pattern pour capturer les domaines de droit séparés par des tirets
                        droit_pattern = r'(Droit [^–\n]+(?: – Droit [^–\n]+)*)'
                        match = re.search(droit_pattern, body_text, re.IGNORECASE)
                        if match:
                            avocat['specialites'] = self.nettoyer_texte(match.group(1))
                    except:
                        pass
            except:
                pass
            
            # Fermer l'onglet et revenir au principal
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return avocat
            
        except Exception as e:
            # En cas d'erreur, fermer l'onglet et revenir au principal
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            print(f"      ✗ Erreur fiche détaillée {url} : {e}")
            return None
    
    def sauvegarder_donnees(self):
        """Sauvegarde les données extraites"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        total = len(self.avocats)
        
        prefix = "CHATEAUROUX_AVEC_DETAILS_TEST" if self.mode_test else "CHATEAUROUX_AVEC_DETAILS_PRODUCTION"
        
        # Fichier JSON
        fichier_json = f"{prefix}_{total}_avocats_{timestamp}.json"
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(self.avocats, f, indent=2, ensure_ascii=False)
        print(f"✓ Données JSON sauvegardées : {fichier_json}")
        
        # Fichier CSV
        fichier_csv = f"{prefix}_{total}_avocats_{timestamp}.csv"
        if self.avocats:
            fieldnames = ['nom', 'prenom', 'structure', 'titre', 'adresse', 'code_postal', 'ville', 
                         'telephone', 'fax', 'email', 'site_web', 'date_serment', 'specialites', 'url', 'date_extraction']
            
            with open(fichier_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.avocats)
        print(f"✓ Données CSV sauvegardées : {fichier_csv}")
        
        # Liste des emails uniquement - nettoyage amélioré
        emails = []
        for a in self.avocats:
            if a.get('email') and a['email'].strip():
                email = a['email'].strip().lower()
                # Vérifier que c'est un vrai email
                if '@' in email and '.' in email.split('@')[-1]:
                    emails.append(email)
        
        emails_uniques = sorted(set(emails))
        fichier_emails = f"{prefix}_EMAILS_{len(emails_uniques)}emails_{timestamp}.txt"
        with open(fichier_emails, 'w', encoding='utf-8') as f:
            for email in emails_uniques:
                f.write(f"{email}\n")
        print(f"✓ Liste des emails sauvegardée : {fichier_emails}")
        
        # Rapport détaillé
        fichier_rapport = f"{prefix}_RAPPORT_COMPLET_{timestamp}.txt"
        with open(fichier_rapport, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("RAPPORT D'EXTRACTION - BARREAU DE CHÂTEAUROUX\n")
            f.write("="*60 + "\n\n")
            f.write(f"Date d'extraction : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Mode : {'TEST' if self.mode_test else 'PRODUCTION'}\n")
            f.write(f"URL source : {self.annuaire_url}\n\n")
            
            f.write("STATISTIQUES GÉNÉRALES\n")
            f.write("-"*30 + "\n")
            f.write(f"Total d'avocats extraits : {self.stats['total_avocats']}\n")
            f.write(f"Lettres traitées : {', '.join(self.stats['lettres_traitees'])}\n")
            f.write(f"Avocats avec email : {self.stats['avocats_avec_email']}\n")
            f.write(f"Avocats avec téléphone : {self.stats['avocats_avec_telephone']}\n")
            f.write(f"Avocats avec adresse : {self.stats['avocats_avec_adresse']}\n")
            f.write(f"Avocats avec structure : {self.stats['avocats_avec_structure']}\n")
            f.write(f"Avocats avec date de serment : {self.stats['avocats_avec_date_serment']}\n")
            f.write(f"Avocats avec spécialités : {self.stats['avocats_avec_specialites']}\n")
            f.write(f"Emails uniques trouvés : {len(emails_uniques)}\n\n")
            
            f.write("TAUX DE COMPLÉTUDE\n")
            f.write("-"*30 + "\n")
            if self.stats['total_avocats'] > 0:
                f.write(f"Emails : {(self.stats['avocats_avec_email']/self.stats['total_avocats']*100):.1f}%\n")
                f.write(f"Téléphones : {(self.stats['avocats_avec_telephone']/self.stats['total_avocats']*100):.1f}%\n")
                f.write(f"Adresses : {(self.stats['avocats_avec_adresse']/self.stats['total_avocats']*100):.1f}%\n")
                f.write(f"Structures : {(self.stats['avocats_avec_structure']/self.stats['total_avocats']*100):.1f}%\n")
                f.write(f"Spécialités : {(self.stats['avocats_avec_specialites']/self.stats['total_avocats']*100):.1f}%\n\n")
            
            if self.stats['erreurs']:
                f.write("ERREURS RENCONTRÉES\n")
                f.write("-"*30 + "\n")
                for erreur in self.stats['erreurs']:
                    f.write(f"- {erreur}\n")
                f.write("\n")
            
            f.write("LISTE DÉTAILLÉE DES AVOCATS\n")
            f.write("-"*30 + "\n\n")
            
            for i, avocat in enumerate(self.avocats, 1):
                f.write(f"{i}.  {avocat.get('prenom', '')} {avocat.get('nom', '')}\n")
                if avocat.get('structure'):
                    f.write(f"   Structure : {avocat['structure']}\n")
                if avocat.get('email'):
                    f.write(f"   Email : {avocat['email']}\n")
                if avocat.get('telephone'):
                    f.write(f"   Téléphone : {avocat['telephone']}\n")
                if avocat.get('adresse'):
                    f.write(f"   Adresse : {avocat['adresse']}")
                    if avocat.get('code_postal'):
                        f.write(f", {avocat['code_postal']}")
                    if avocat.get('ville'):
                        f.write(f" {avocat['ville']}")
                    f.write("\n")
                if avocat.get('date_serment'):
                    f.write(f"   Date de serment : {avocat['date_serment']}\n")
                if avocat.get('specialites'):
                    f.write(f"   Spécialités : {avocat['specialites']}\n")
                f.write("\n")
                
        print(f"✓ Rapport généré : {fichier_rapport}")
        
    def scraper(self):
        """Fonction principale de scraping"""
        print("="*60)
        print("DÉMARRAGE DU SCRAPER - BARREAU DE CHÂTEAUROUX")
        print("AVEC EXTRACTION DES FICHES DÉTAILLÉES")
        print("="*60)
        
        try:
            # Initialisation
            self.setup_driver(headless=False)  # Mode visible pour debug
            
            # Accepter les cookies
            self.driver.get(self.annuaire_url)
            self.accepter_cookies()
            
            # Obtenir les lettres disponibles
            lettres = self.obtenir_lettres_disponibles()
            
            if self.mode_test:
                print(f"\nMode test : traitement de {min(2, len(lettres))} lettres")
                lettres = lettres[:2]  # Limiter à 2 lettres pour le test
            else:
                print(f"\nMode production : traitement de toutes les {len(lettres)} lettres")
            
            # Extraire les avocats pour chaque lettre
            for lettre in lettres:
                avocats_lettre = self.extraire_avocats_lettre(lettre)
                self.avocats.extend(avocats_lettre)
                
                # Vérifier la limite de test
                if self.mode_test and self.stats['total_avocats'] >= self.limite_test:
                    break
                    
                # Petit délai entre les lettres
                time.sleep(1)
            
            print("\n" + "="*60)
            print("EXTRACTION TERMINÉE")
            print("="*60)
            
            # Sauvegarder les données
            self.sauvegarder_donnees()
            
            print(f"\n{'='*60}")
            print("EXTRACTION TERMINÉE AVEC SUCCÈS")
            print(f"Total : {len(self.avocats)} avocat(s) extrait(s)")
            emails_valides = [a['email'] for a in self.avocats if a.get('email') and a['email'].strip()]
            emails_uniques_final = len(set(emails_valides))
            print(f"Emails uniques : {emails_uniques_final} emails (sur {len(emails_valides)} emails extraits)")
            print(f"Structures : {len([a for a in self.avocats if a.get('structure')])} structures")
            print(f"Spécialités : {len([a for a in self.avocats if a.get('specialites')])} avec spécialités")
            print("="*60)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  INTERRUPTION PAR L'UTILISATEUR")
            print("Sauvegarde des données partielles...")
            if self.avocats:
                self.sauvegarder_donnees()
            
        except Exception as e:
            print(f"\n✗ ERREUR CRITIQUE : {e}")
            if self.avocats:
                print("Sauvegarde des données partielles...")
                self.sauvegarder_donnees()
                
        finally:
            if self.driver:
                self.driver.quit()
                print("✓ Driver fermé")

def main():
    print("="*60)
    print("SCRAPER DU BARREAU DE CHÂTEAUROUX")
    print("AVEC CONSULTATION DES FICHES DÉTAILLÉES")
    print("="*60)
    print("Mode : PRODUCTION")
    print("Extraction : TOUS LES AVOCATS")
    print("URL : https://www.avocats-chateauroux.fr/annuaire-des-avocats/")
    print("="*60)
    
    scraper = ChateaurouxBarreauScraperAvecFichesDetails(mode_test=False, limite_test=None)
    scraper.scraper()

if __name__ == "__main__":
    main()