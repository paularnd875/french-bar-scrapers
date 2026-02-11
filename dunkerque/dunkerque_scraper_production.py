#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DunkerqueBarScraperProduction:
    def __init__(self, headless=True):
        self.base_url = "https://barreau-dunkerque.fr"
        self.search_url = "https://barreau-dunkerque.fr/search-result/?directory_type=general"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Configuration Selenium
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')  # Mode headless pour la production
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None
        self.lawyers_data = []
        self.processed_urls = set()  # Pour éviter les doublons
        self.total_expected = 79  # Nombre total d'avocats selon le site
    
    def start_browser(self):
        """Démarre le navigateur Chrome"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Navigateur Chrome démarré avec succès en mode production")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du navigateur: {e}")
            return False
    
    def accept_cookies(self):
        """Gère l'acceptation des cookies si nécessaire"""
        try:
            # Recherche du bouton d'acceptation des cookies
            cookie_selectors = [
                "button[id*='accept']",
                "button[class*='accept']",
                "button[id*='cookie']",
                "button[class*='cookie']",
                ".cookie-accept",
                "#cookie-accept",
                ".accept-cookies",
                "#accept-cookies"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    cookie_button.click()
                    logger.info(f"Cookies acceptés via le sélecteur: {selector}")
                    time.sleep(1)
                    return True
                except TimeoutException:
                    continue
            
            logger.info("Aucun bouton de cookies trouvé - continuons")
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'acceptation des cookies: {e}")
            return True
    
    def scroll_page_to_load_all(self):
        """Fait défiler la page pour charger tous les avocats (pagination dynamique)"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            attempts = 0
            max_attempts = 10
            
            while attempts < max_attempts:
                # Faire défiler vers le bas
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Calculer la nouvelle hauteur de scroll et comparer avec la dernière
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    # Essayer de cliquer sur un bouton "Voir plus" ou "Charger plus"
                    try:
                        load_more_buttons = [
                            "button[class*='load-more']",
                            "button[class*='voir-plus']",
                            "a[class*='load-more']",
                            ".load-more",
                            ".voir-plus",
                            "button:contains('Voir plus')",
                            "button:contains('Load more')"
                        ]
                        
                        for selector in load_more_buttons:
                            try:
                                load_more = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if load_more.is_displayed() and load_more.is_enabled():
                                    load_more.click()
                                    logger.info(f"Bouton 'Charger plus' cliqué: {selector}")
                                    time.sleep(3)
                                    break
                            except:
                                continue
                        else:
                            # Aucun bouton trouvé, on a probablement tout chargé
                            break
                    except:
                        # Pas de bouton, on a tout chargé
                        break
                
                last_height = new_height
                attempts += 1
            
            # Vérifier le nombre de fiches chargées
            lawyer_cards = self.driver.find_elements(By.CSS_SELECTOR, ".directorist-listing-single")
            logger.info(f"Total de fiches chargées après scroll: {len(lawyer_cards)}")
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors du scroll: {e}")
            return False
    
    def get_all_lawyers_list(self):
        """Récupère la liste complète des avocats"""
        try:
            logger.info(f"Accès à la page principale: {self.search_url}")
            self.driver.get(self.search_url)
            time.sleep(4)
            
            # Accepter les cookies
            self.accept_cookies()
            time.sleep(2)
            
            # Attendre que la page soit complètement chargée
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".directorist-listing-single"))
            )
            
            # Charger tous les avocats en scrollant
            self.scroll_page_to_load_all()
            time.sleep(2)
            
            # Récupérer tous les liens vers les fiches d'avocats
            lawyer_cards = self.driver.find_elements(By.CSS_SELECTOR, ".directorist-listing-single")
            logger.info(f"Nombre de fiches d'avocats trouvées: {len(lawyer_cards)}")
            
            lawyers_urls = []
            
            for i, card in enumerate(lawyer_cards, 1):
                try:
                    # Chercher le lien vers la fiche détaillée
                    link_element = card.find_element(By.CSS_SELECTOR, "a[href*='/directory/']")
                    lawyer_url = link_element.get_attribute('href')
                    
                    # Éviter les doublons
                    if lawyer_url in self.processed_urls:
                        continue
                    
                    # Récupérer le nom depuis le titre ou l'alt de l'image
                    try:
                        name_element = card.find_element(By.CSS_SELECTOR, ".directorist-listing-title a")
                        lawyer_name = name_element.text.strip()
                    except:
                        try:
                            img_element = card.find_element(By.CSS_SELECTOR, "img")
                            lawyer_name = img_element.get_attribute('alt')
                        except:
                            lawyer_name = f"Avocat #{i}"
                    
                    lawyers_urls.append({
                        'name': lawyer_name,
                        'url': lawyer_url
                    })
                    
                    self.processed_urls.add(lawyer_url)
                    
                    logger.info(f"[{i}/{len(lawyer_cards)}] Avocat trouvé: {lawyer_name}")
                    
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction de la fiche #{i}: {e}")
                    continue
            
            logger.info(f"Total d'avocats uniques collectés: {len(lawyers_urls)}")
            return lawyers_urls
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la liste des avocats: {e}")
            return []
    
    def extract_lawyer_details(self, lawyer_info, index, total):
        """Extrait les détails d'un avocat depuis sa fiche individuelle"""
        try:
            logger.info(f"[{index}/{total}] Extraction des détails pour: {lawyer_info['name']}")
            self.driver.get(lawyer_info['url'])
            time.sleep(2)
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # Initialiser les données de l'avocat
            lawyer_data = {
                'nom_complet': lawyer_info['name'],
                'url_fiche': lawyer_info['url'],
                'prenom': '',
                'nom': '',
                'email': '',
                'telephone': '',
                'adresse': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'autres_infos': {}
            }
            
            # Extraction du nom et prénom
            try:
                name_parts = lawyer_info['name'].replace('Maître ', '').strip().split()
                if len(name_parts) >= 2:
                    lawyer_data['prenom'] = name_parts[0]
                    lawyer_data['nom'] = ' '.join(name_parts[1:])
            except:
                pass
            
            # Recherche de l'email
            try:
                email_selectors = [
                    "a[href^='mailto:']",
                    ".email",
                    ".directorist-contact-email",
                    ".contact-email"
                ]
                
                for selector in email_selectors:
                    try:
                        email_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector == "a[href^='mailto:']":
                            lawyer_data['email'] = email_element.get_attribute('href').replace('mailto:', '')
                        else:
                            lawyer_data['email'] = email_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche du téléphone
            try:
                phone_selectors = [
                    "a[href^='tel:']",
                    ".phone",
                    ".telephone",
                    ".directorist-contact-phone"
                ]
                
                for selector in phone_selectors:
                    try:
                        phone_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if selector == "a[href^='tel:']":
                            lawyer_data['telephone'] = phone_element.get_attribute('href').replace('tel:', '')
                        else:
                            lawyer_data['telephone'] = phone_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche de l'adresse
            try:
                address_selectors = [
                    ".directorist-contact-address",
                    ".address",
                    ".adresse",
                    ".contact-address"
                ]
                
                for selector in address_selectors:
                    try:
                        address_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        lawyer_data['adresse'] = address_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche des spécialisations/domaines de compétences
            try:
                # Méthode 1: Chercher les checkbox cochées pour les domaines de compétences
                speciality_selectors = [
                    "input[type='checkbox']:checked",
                    ".custom-checkbox input:checked",
                    ".directorist-checkbox-field input:checked",
                    "input[field_key='custom-checkbox']:checked"
                ]
                
                for selector in speciality_selectors:
                    try:
                        checkbox_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in checkbox_elements:
                            # Récupérer la valeur ou le texte associé
                            spec_value = elem.get_attribute('value')
                            if spec_value and spec_value not in lawyer_data['specialisations']:
                                lawyer_data['specialisations'].append(spec_value)
                            
                            # Essayer aussi le label associé
                            try:
                                label = elem.find_element(By.XPATH, "../label")
                                label_text = label.text.strip()
                                if label_text and label_text not in lawyer_data['specialisations']:
                                    lawyer_data['specialisations'].append(label_text)
                            except:
                                pass
                    except:
                        continue
                
                # Méthode 2: Chercher dans les div de spécialisations
                if not lawyer_data['specialisations']:
                    other_selectors = [
                        ".directorist-listing-category",
                        ".specialisation", 
                        ".category",
                        ".speciality",
                        ".domaines-competence",
                        ".competences",
                        "[class*='competence']",
                        "[class*='specialisation']"
                    ]
                    
                    for selector in other_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                spec_text = elem.text.strip()
                                if spec_text and len(spec_text) > 3 and spec_text not in lawyer_data['specialisations']:
                                    lawyer_data['specialisations'].append(spec_text)
                        except:
                            continue
                
                # Méthode 3: Recherche dans les données JavaScript de Directorist
                if not lawyer_data['specialisations']:
                    try:
                        js_script = """
                        var specialisations = [];
                        
                        // Récupérer les données depuis le JavaScript de Directorist
                        if (typeof directorist !== 'undefined' && 
                            directorist.directory_type_term_data && 
                            directorist.directory_type_term_data.submission_form_fields &&
                            directorist.directory_type_term_data.submission_form_fields.fields &&
                            directorist.directory_type_term_data.submission_form_fields.fields.checkbox) {
                            
                            var checkboxData = directorist.directory_type_term_data.submission_form_fields.fields.checkbox;
                            if (checkboxData.options) {
                                // Récupérer le nom de l'avocat depuis le titre de la page
                                var lawyerName = document.title.replace('Maître ', '').replace(' - LES AVOCATS DE DUNKERQUE', '').trim();
                                
                                // Chercher dans le contenu de la page les spécialisations mentionnées
                                var pageContent = document.body.innerText.toLowerCase();
                                
                                for (var i = 0; i < checkboxData.options.length; i++) {
                                    var option = checkboxData.options[i];
                                    var optionValue = option.option_value.toLowerCase();
                                    var optionLabel = option.option_label.toLowerCase();
                                    
                                    // Vérifier si cette spécialisation est mentionnée sur la page
                                    if (pageContent.includes(optionValue) || 
                                        pageContent.includes(optionLabel) ||
                                        pageContent.includes(optionLabel.replace('droit ', '')) ||
                                        pageContent.includes(optionValue.replace('droit ', ''))) {
                                        specialisations.push(option.option_label);
                                    }
                                }
                            }
                        }
                        
                        // Méthode alternative: chercher des mots-clés directement
                        var keywordSpecialisations = [
                            'famille', 'pénal', 'travail', 'immobilier', 'construction', 
                            'fiscal', 'douanier', 'commercial', 'affaires', 'public',
                            'assurance', 'société', 'santé', 'rural', 'crédit', 'consommation',
                            'mineurs', 'étrangers', 'nationalité', 'corporel', 'garanties',
                            'fonction publique', 'sécurité sociale', 'bancaire', 'boursier'
                        ];
                        
                        for (var j = 0; j < keywordSpecialisations.length; j++) {
                            if (pageContent.includes(keywordSpecialisations[j])) {
                                var foundKeyword = keywordSpecialisations[j];
                                if (foundKeyword === 'famille') specialisations.push('Droit de la famille, des personnes et de leur patrimoine');
                                else if (foundKeyword === 'pénal') specialisations.push('Droit pénal');
                                else if (foundKeyword === 'travail') specialisations.push('Droit du travail');
                                else if (foundKeyword === 'immobilier' || foundKeyword === 'construction') specialisations.push('Droit immobilier et de la construction');
                                else if (foundKeyword === 'fiscal' || foundKeyword === 'douanier') specialisations.push('Droit fiscal et douanier');
                                else if (foundKeyword === 'commercial' || foundKeyword === 'affaires') specialisations.push('Droit commercial, des affaires et de la concurrence');
                                else if (foundKeyword === 'public') specialisations.push('Droit public');
                                else if (foundKeyword === 'assurance') specialisations.push('Droit des assurances');
                                else if (foundKeyword === 'société') specialisations.push('Droit des sociétés');
                                else if (foundKeyword === 'santé') specialisations.push('Droit de la santé');
                                else if (foundKeyword === 'rural') specialisations.push('Droit rural');
                                else if (foundKeyword === 'crédit' || foundKeyword === 'consommation') specialisations.push('Droit du crédit et de la consommation');
                                else if (foundKeyword === 'mineurs') specialisations.push('Droit des mineurs');
                                else if (foundKeyword === 'étrangers' || foundKeyword === 'nationalité') specialisations.push('Droit des étrangers et de la Nationalité');
                                else if (foundKeyword === 'corporel') specialisations.push('Droit du dommage corporel');
                                else if (foundKeyword === 'garanties') specialisations.push('Droit des garanties, des sûretés, et des mesures d\\'exécution');
                                else if (foundKeyword === 'fonction publique') specialisations.push('Droit de la fonction publique');
                                else if (foundKeyword === 'sécurité sociale') specialisations.push('Droit de la sécurité sociale et de la protection sociale');
                                else if (foundKeyword === 'bancaire' || foundKeyword === 'boursier') specialisations.push('Droit bancaire et boursier');
                            }
                        }
                        
                        // Supprimer les doublons
                        specialisations = [...new Set(specialisations)];
                        
                        return specialisations;
                        """
                        js_specialisations = self.driver.execute_script(js_script)
                        if js_specialisations:
                            lawyer_data['specialisations'].extend(js_specialisations)
                    except Exception as e:
                        logger.warning(f"Erreur JavaScript pour les spécialisations: {e}")
                        pass
                        
                # Nettoyer les spécialisations (enlever les doublons et textes trop courts)
                lawyer_data['specialisations'] = list(set([
                    spec.strip() for spec in lawyer_data['specialisations'] 
                    if spec.strip() and len(spec.strip()) > 3
                ]))
                
            except Exception as e:
                logger.warning(f"Erreur lors de l'extraction des spécialisations: {e}")
                pass
            
            # Recherche de la structure/cabinet
            try:
                structure_selectors = [
                    ".directorist-contact-company",
                    ".cabinet",
                    ".structure",
                    ".company"
                ]
                
                for selector in structure_selectors:
                    try:
                        structure_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        lawyer_data['structure'] = structure_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Recherche de l'année d'inscription
            try:
                page_text = self.driver.find_element(By.CSS_SELECTOR, "body").text
                
                # Chercher l'année d'inscription (pattern: année entre 1950-2024)
                import re
                year_pattern = r'\b(19[5-9]\d|20[0-2]\d)\b'
                years = re.findall(year_pattern, page_text)
                if years:
                    lawyer_data['annee_inscription'] = years[0]
            except:
                pass
            
            # Log du résultat
            status_email = "✓" if lawyer_data['email'] else "✗"
            status_phone = "✓" if lawyer_data['telephone'] else "✗"
            logger.info(f"[{index}/{total}] {lawyer_data['nom_complet']} - Email:{status_email} Tél:{status_phone}")
            
            return lawyer_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des détails pour {lawyer_info['name']}: {e}")
            return None
    
    def save_results(self, filename_prefix="dunkerque_production"):
        """Sauvegarde les résultats en JSON et CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarde JSON
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if self.lawyers_data:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['nom_complet', 'prenom', 'nom', 'email', 'telephone', 'adresse', 
                            'annee_inscription', 'specialisations', 'structure', 'url_fiche']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for lawyer in self.lawyers_data:
                    lawyer_copy = lawyer.copy()
                    lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations'])
                    # Enlever autres_infos du CSV
                    lawyer_copy.pop('autres_infos', None)
                    writer.writerow(lawyer_copy)
        
        # Fichier emails seulement
        emails_filename = f"{filename_prefix}_EMAILS_SEULEMENT_{timestamp}.txt"
        with open(emails_filename, 'w', encoding='utf-8') as f:
            emails = [lawyer['email'] for lawyer in self.lawyers_data if lawyer['email']]
            f.write('\n'.join(sorted(set(emails))))
        
        # Rapport détaillé
        report_filename = f"{filename_prefix}_RAPPORT_COMPLET_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            emails_count = len([l for l in self.lawyers_data if l['email']])
            phones_count = len([l for l in self.lawyers_data if l['telephone']])
            addresses_count = len([l for l in self.lawyers_data if l['adresse']])
            
            f.write(f"=== RAPPORT D'EXTRACTION BARREAU DE DUNKERQUE ===\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre total d'avocats extraits: {len(self.lawyers_data)}\n")
            f.write(f"Avocats avec email: {emails_count} ({emails_count/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"Avocats avec téléphone: {phones_count} ({phones_count/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"Avocats avec adresse: {addresses_count} ({addresses_count/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"Taux de réussite global: {len(self.lawyers_data)}/{self.total_expected} ({len(self.lawyers_data)/self.total_expected*100:.1f}%)\n\n")
            
            f.write("=== DÉTAIL DES AVOCATS ===\n")
            for i, lawyer in enumerate(self.lawyers_data, 1):
                f.write(f"\n{i}. {lawyer['nom_complet']}\n")
                f.write(f"   Email: {lawyer['email'] or 'N/A'}\n")
                f.write(f"   Téléphone: {lawyer['telephone'] or 'N/A'}\n")
                f.write(f"   Adresse: {lawyer['adresse'] or 'N/A'}\n")
                f.write(f"   Année d'inscription: {lawyer['annee_inscription'] or 'N/A'}\n")
                f.write(f"   Spécialisations: {', '.join(lawyer['specialisations']) or 'N/A'}\n")
                f.write(f"   Structure: {lawyer['structure'] or 'N/A'}\n")
        
        logger.info(f"Résultats sauvegardés:")
        logger.info(f"- JSON: {json_filename}")
        logger.info(f"- CSV: {csv_filename}")
        logger.info(f"- Emails: {emails_filename}")
        logger.info(f"- Rapport: {report_filename}")
        
        return json_filename, csv_filename, emails_filename, report_filename
    
    def run_production_scraping(self):
        """Lance le scraping complet en production"""
        try:
            logger.info("=== DÉBUT DU SCRAPING PRODUCTION DUNKERQUE ===")
            start_time = time.time()
            
            if not self.start_browser():
                return False
            
            # Étape 1: Récupérer la liste complète des avocats
            lawyers_urls = self.get_all_lawyers_list()
            
            if not lawyers_urls:
                logger.error("Aucun avocat trouvé")
                return False
            
            logger.info(f"Scraping de {len(lawyers_urls)} avocats en cours...")
            
            # Étape 2: Extraire les détails de chaque avocat
            for i, lawyer_info in enumerate(lawyers_urls, 1):
                try:
                    lawyer_data = self.extract_lawyer_details(lawyer_info, i, len(lawyers_urls))
                    if lawyer_data:
                        self.lawyers_data.append(lawyer_data)
                    
                    # Pause entre les requêtes pour éviter la surcharge
                    time.sleep(1.5)
                    
                    # Sauvegarde intermédiaire tous les 10 avocats
                    if i % 10 == 0:
                        logger.info(f"Sauvegarde intermédiaire - {i}/{len(lawyers_urls)} traités")
                        
                except KeyboardInterrupt:
                    logger.warning("Interruption détectée - sauvegarde des données partielles...")
                    break
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de l'avocat #{i}: {e}")
                    continue
            
            # Étape 3: Sauvegarder les résultats finaux
            json_file, csv_file, emails_file, report_file = self.save_results()
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"=== SCRAPING TERMINÉ ===")
            logger.info(f"Durée totale: {duration/60:.1f} minutes")
            logger.info(f"Avocats traités avec succès: {len(self.lawyers_data)}")
            logger.info(f"Emails récupérés: {len([l for l in self.lawyers_data if l['email']])}")
            logger.info(f"Téléphones récupérés: {len([l for l in self.lawyers_data if l['telephone']])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur durant le scraping de production: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Navigateur fermé")

def main():
    print("🚀 Lancement du scraping COMPLET du Barreau de Dunkerque")
    print("⚡ Mode headless activé - aucune fenêtre ne s'ouvrira")
    print("⏱️  Durée estimée: 3-5 minutes pour ~79 avocats")
    print("-" * 60)
    
    scraper = DunkerqueBarScraperProduction(headless=True)
    success = scraper.run_production_scraping()
    
    print("-" * 60)
    if success:
        print("✅ Scraping terminé avec succès!")
        print("📊 Vérifiez les fichiers générés pour voir les résultats complets.")
    else:
        print("❌ Échec du scraping - consultez les logs pour plus d'informations")

if __name__ == "__main__":
    main()