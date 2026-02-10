#!/usr/bin/env python3
"""
Scraper final complet pour l'annuaire du Barreau de Nantes
Extraction complète avec toutes les informations disponibles
"""

import time
import json
import csv
import re
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('barreau_nantes_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BarreauNantesFinalScraper:
    def __init__(self, headless=True, delay=2):
        self.headless = headless
        self.delay = delay
        self.driver = None
        self.base_url = "https://www.barreaunantes.fr/annuaire/"
        self.lawyers_data = []
        self.session_start = datetime.now()
        
    def setup_driver(self):
        """Configure le driver Chrome optimisé"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
            
        # Options optimisées pour performance et discrétion
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7559.133 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            logger.info(f"Driver configuré - Mode headless: {self.headless}")
            return self.driver
            
        except Exception as e:
            logger.error(f"Erreur configuration driver: {e}")
            raise
    
    def get_all_filter_options(self):
        """Récupère toutes les options de filtre disponibles"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            options_data = {}
            form = self.driver.find_element(By.TAG_NAME, "form")
            selects = form.find_elements(By.TAG_NAME, "select")
            
            for select_elem in selects:
                name = select_elem.get_attribute('name')
                if name and name != 'nom':  # Ignorer le champ nom (liste alphabétique)
                    try:
                        select_obj = Select(select_elem)
                        options = []
                        
                        for option in select_obj.options:
                            value = option.get_attribute('value')
                            text = option.text.strip()
                            if value and value != '' and text and text not in ['Toutes', '']:
                                options.append({'value': value, 'text': text})
                        
                        if options:
                            options_data[name] = options
                            logger.info(f"Champ '{name}': {len(options)} options")
                    
                    except Exception as e:
                        logger.warning(f"Erreur avec select '{name}': {e}")
            
            return options_data
            
        except Exception as e:
            logger.error(f"Erreur récupération options: {e}")
            return {}
    
    def extract_comprehensive_info_from_page(self):
        """Extraction complète et améliorée des informations d'avocats"""
        try:
            lawyers = []
            time.sleep(self.delay)
            
            page_source = self.driver.page_source
            logger.info("Extraction complète des informations d'avocats...")
            
            # 1. Extraction des cabinets/structures
            cabinet_patterns = [
                # Patterns pour cabinets
                r'([A-Z][A-Z\s&.-]+(?:Avocats?|Conseil|Cabinet|Associés|Avocat et associés))',
                r'([A-Z]{2,}(?:\s+[A-Z]{2,})*)\s+(Avocats?|Conseil)',
                r'((?:[A-Z][a-zA-Z]+\s+){2,}(?:et\s+associés|Avocats?|Conseil))',
                # Patterns pour noms de cabinets spécifiques
                r'((?:[A-Z]{2,}\s+){1,3}(?:Avocats?|Conseil|Cabinet))',
                r'([A-Z]+\s+(?:[A-Z]+\s+)*Avocats?)'
            ]
            
            found_cabinets = set()
            for pattern in cabinet_patterns:
                matches = re.findall(pattern, page_source, re.MULTILINE)
                if matches:
                    logger.info(f"Pattern cabinet: {len(matches)} correspondances")
                    for match in matches:
                        if isinstance(match, tuple):
                            cabinet_name = match[0].strip()
                            type_cabinet = match[1].strip() if len(match) > 1 else ""
                        else:
                            cabinet_name = match.strip()
                            type_cabinet = ""
                        
                        # Filtrer et nettoyer
                        if (cabinet_name and 
                            len(cabinet_name) > 3 and 
                            cabinet_name not in found_cabinets and
                            not any(skip in cabinet_name.lower() for skip in 
                                   ['footer', 'menu', 'navigation', 'header'])):
                            
                            found_cabinets.add(cabinet_name)
                            
                            lawyer_data = {
                                'cabinet': f"{cabinet_name} {type_cabinet}".strip(),
                                'nom_cabinet': cabinet_name,
                                'type_structure': type_cabinet,
                                'source_extraction': 'pattern_cabinet'
                            }
                            lawyers.append(lawyer_data)
            
            # 2. Extraction des emails directement de la page
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_source)
            
            # 3. Extraction des téléphones
            phone_patterns = [
                r'(?:0[1-9](?:[\s\.\-]?\d{2}){4})',
                r'(?:\+33[1-9](?:[\s\.\-]?\d{2}){4})',
                r'(?:0\d[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2})'
            ]
            
            phones = set()
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_source)
                phones.update(matches)
            
            # 4. Extraction des adresses
            address_patterns = [
                r'\d+[^,\n]*(?:rue|avenue|boulevard|place|mail|allée)[^,\n]*\d{5}[^,\n]*',
                r'(?:rue|avenue|boulevard|place|mail|allée)[^,\n]*\d{5}[^,\n]*',
                r'\d+[^,\n]*(?:rue|avenue|boulevard|place|mail|allée)[^,\n]*(?:nantes|ancenis|bouguenais)[^,\n]*'
            ]
            
            addresses = set()
            for pattern in address_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                for match in matches:
                    clean_addr = re.sub(r'<[^>]*>', '', match).strip()
                    if len(clean_addr) > 10 and len(clean_addr) < 100:
                        addresses.add(clean_addr)
            
            # 5. Extraction via analyse de la structure HTML
            try:
                # Chercher dans les éléments structurés
                container_selectors = [
                    'div[class*="result"]',
                    'div[class*="avocat"]', 
                    'div[class*="lawyer"]',
                    'article',
                    'section[class*="content"]',
                    '.entry-content div'
                ]
                
                for selector in container_selectors:
                    try:
                        containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for container in containers:
                            try:
                                text = container.text.strip()
                                
                                # Filtrer les conteneurs pertinents
                                if (text and 
                                    20 <= len(text) <= 800 and  # Taille raisonnable
                                    not any(skip_word in text.lower() for skip_word in 
                                           ['copyright', 'mentions légales', 'cookies', 'navigation', 'footer'])):
                                    
                                    lines = [line.strip() for line in text.split('\\n') if line.strip()]
                                    
                                    if len(lines) >= 1:
                                        # Analyser chaque ligne pour différents types d'infos
                                        lawyer_data = {'source_extraction': 'html_structure'}
                                        
                                        for line in lines:
                                            line = line.strip()
                                            
                                            # Détecter nom/cabinet
                                            if (re.match(r'^[A-Z][A-Za-z\\s&.-]+(?:Avocats?|Conseil|Cabinet)?$', line) or
                                                re.match(r'^[A-Z]{2,}\\s+[A-Z][a-z]+', line)):
                                                if 'nom_complet' not in lawyer_data:
                                                    lawyer_data['nom_complet'] = line
                                            
                                            # Détecter email
                                            elif '@' in line and re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$', line):
                                                lawyer_data['email'] = line
                                            
                                            # Détecter téléphone
                                            elif re.match(r'^(?:Tél[^:]*:?\\s*)?(?:0[1-9](?:[\\s\\.-]?\\d{2}){4})$', line, re.IGNORECASE):
                                                lawyer_data['telephone'] = re.sub(r'^(?:Tél[^:]*:?\\s*)', '', line, flags=re.IGNORECASE)
                                            
                                            # Détecter adresse
                                            elif (('rue' in line.lower() or 'avenue' in line.lower() or 'boulevard' in line.lower()) and 
                                                  len(line) > 10):
                                                lawyer_data['adresse'] = line
                                            
                                            # Détecter ville/code postal
                                            elif re.match(r'^\\d{5}\\s+[A-Z][a-z]+', line):
                                                lawyer_data['ville'] = line
                                        
                                        # Ajouter seulement si on a des infos pertinentes
                                        if ('nom_complet' in lawyer_data and lawyer_data['nom_complet'] and
                                            len(lawyer_data['nom_complet']) > 3):
                                            lawyers.append(lawyer_data)
                            
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.warning(f"Erreur extraction HTML: {e}")
            
            # 6. Associer les emails/téléphones/adresses aux avocats trouvés
            if emails or phones or addresses:
                logger.info(f"Informations de contact trouvées - Emails: {len(emails)}, Téléphones: {len(phones)}, Adresses: {len(addresses)}")
                
                # Si on a moins d'avocats que de contacts, créer des entrées supplémentaires
                all_emails = list(emails)
                all_phones = list(phones)
                all_addresses = list(addresses)
                
                # Distribuer les contacts aux avocats existants
                for i, lawyer in enumerate(lawyers):
                    if i < len(all_emails):
                        lawyer['email'] = all_emails[i]
                    if i < len(all_phones):
                        lawyer['telephone'] = all_phones[i]
                    if i < len(all_addresses):
                        lawyer['adresse'] = all_addresses[i]
                
                # Créer des entrées pour les contacts restants
                max_contacts = max(len(all_emails), len(all_phones), len(all_addresses))
                for i in range(len(lawyers), max_contacts):
                    contact_data = {'source_extraction': 'contact_orphelin'}
                    
                    if i < len(all_emails):
                        contact_data['email'] = all_emails[i]
                    if i < len(all_phones):
                        contact_data['telephone'] = all_phones[i]
                    if i < len(all_addresses):
                        contact_data['adresse'] = all_addresses[i]
                    
                    lawyers.append(contact_data)
            
            # 7. Déduplication et nettoyage final
            unique_lawyers = []
            seen_signatures = set()
            
            for lawyer in lawyers:
                # Créer une signature unique
                signature_parts = [
                    lawyer.get('nom_complet', ''),
                    lawyer.get('cabinet', ''),
                    lawyer.get('nom_cabinet', ''),
                    lawyer.get('email', ''),
                    lawyer.get('telephone', '')
                ]
                
                signature = '|'.join(part.lower().strip() for part in signature_parts if part)
                
                if signature and signature not in seen_signatures:
                    seen_signatures.add(signature)
                    
                    # Nettoyer et enrichir les données
                    if lawyer.get('nom_complet'):
                        # Essayer de séparer nom/prénom
                        name_parts = lawyer['nom_complet'].split()
                        if len(name_parts) >= 2 and not any(word in lawyer['nom_complet'].lower() 
                                                           for word in ['avocats', 'conseil', 'cabinet']):
                            lawyer['nom'] = name_parts[0]
                            lawyer['prenom'] = ' '.join(name_parts[1:])
                    
                    unique_lawyers.append(lawyer)
            
            logger.info(f"Extraction terminée: {len(unique_lawyers)} entrées uniques trouvées")
            
            # Afficher quelques exemples pour debug
            for i, lawyer in enumerate(unique_lawyers[:3]):
                logger.info(f"Exemple {i+1}: {lawyer}")
            
            return unique_lawyers
            
        except Exception as e:
            logger.error(f"Erreur extraction complète: {e}")
            return []
    
    def submit_form_with_filters(self, filters=None):
        """Soumet le formulaire avec les filtres spécifiés"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            form = self.driver.find_element(By.TAG_NAME, "form")
            
            if filters:
                logger.info(f"Application des filtres: {filters}")
                for field_name, value in filters.items():
                    try:
                        select_elem = form.find_element(By.CSS_SELECTOR, f"select[name='{field_name}']")
                        select_obj = Select(select_elem)
                        select_obj.select_by_value(str(value))
                        time.sleep(1)
                    except Exception as e:
                        logger.warning(f"Impossible d'appliquer filtre {field_name}: {e}")
            
            # Soumettre le formulaire
            submit_btn = form.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            submit_btn.click()
            time.sleep(5)
            
            # Extraire les résultats avec la nouvelle méthode complète
            return self.extract_comprehensive_info_from_page()
            
        except Exception as e:
            logger.error(f"Erreur soumission formulaire: {e}")
            return []
    
    def scrape_all_comprehensive(self, test_mode=True, max_strategies=None):
        """Scraping complet avec toutes les stratégies et informations"""
        try:
            logger.info("=== DÉBUT SCRAPING COMPLET FINAL ===")
            
            self.setup_driver()
            
            # Récupérer les options de filtre
            filter_options = self.get_all_filter_options()
            
            if not filter_options:
                logger.error("Impossible de récupérer les options de filtre")
                return []
            
            # Définir les stratégies de scraping
            strategies = []
            
            if test_mode:
                logger.info("Mode TEST - Stratégies limitées")
                strategies = [
                    {},  # Sans filtre
                ]
                
                # Ajouter quelques villes
                if 'ville' in filter_options:
                    for ville in filter_options['ville'][:3]:
                        strategies.append({'ville': ville['value']})
                
                # Ajouter quelques spécialisations
                if 'specialite' in filter_options:
                    for spec in filter_options['specialite'][:2]:
                        strategies.append({'specialite': spec['value']})
                        
            else:
                logger.info("Mode COMPLET - Toutes les stratégies")
                strategies.append({})  # Sans filtre
                
                # Toutes les villes
                if 'ville' in filter_options:
                    for ville in filter_options['ville']:
                        strategies.append({'ville': ville['value']})
                
                # Toutes les spécialisations
                if 'specialite' in filter_options:
                    for spec in filter_options['specialite']:
                        strategies.append({'specialite': spec['value']})
                
                # Quelques langues
                if 'langue' in filter_options:
                    for langue in filter_options['langue'][:5]:
                        strategies.append({'langue': langue['value']})
                
                # Combinaisons ville + spécialisation (échantillon)
                if 'ville' in filter_options and 'specialite' in filter_options:
                    for ville in filter_options['ville'][:5]:
                        for spec in filter_options['specialite'][:3]:
                            strategies.append({
                                'ville': ville['value'],
                                'specialite': spec['value']
                            })
            
            # Limiter le nombre de stratégies si demandé
            if max_strategies:
                strategies = strategies[:max_strategies]
            
            logger.info(f"Nombre total de stratégies: {len(strategies)}")
            
            all_lawyers = []
            seen_signatures = set()
            strategy_results = []
            
            for i, strategy in enumerate(strategies):
                try:
                    logger.info(f"\\n=== Stratégie {i+1}/{len(strategies)}: {strategy} ===")
                    
                    # Appliquer la stratégie
                    lawyers = self.submit_form_with_filters(strategy)
                    
                    strategy_info = {
                        'strategy': strategy,
                        'lawyers_found': len(lawyers),
                        'new_lawyers': 0
                    }
                    
                    # Ajouter au total en évitant les doublons
                    for lawyer in lawyers:
                        # Créer une signature unique plus robuste
                        signature_parts = [
                            lawyer.get('nom_complet', ''),
                            lawyer.get('cabinet', ''),
                            lawyer.get('email', ''),
                            lawyer.get('telephone', ''),
                            lawyer.get('nom_cabinet', '')
                        ]
                        
                        signature = '|'.join(part.lower().strip() for part in signature_parts if part).replace(' ', '')
                        
                        if signature and signature not in seen_signatures:
                            seen_signatures.add(signature)
                            lawyer['strategie_extraction'] = str(strategy)
                            lawyer['timestamp_extraction'] = datetime.now().isoformat()
                            lawyer['strategy_number'] = i + 1
                            all_lawyers.append(lawyer)
                            strategy_info['new_lawyers'] += 1
                    
                    strategy_results.append(strategy_info)
                    
                    logger.info(f"Avocats trouvés: {len(lawyers)}")
                    logger.info(f"Nouveaux avocats uniques: {strategy_info['new_lawyers']}")
                    logger.info(f"Total cumulé: {len(all_lawyers)}")
                    
                    # Pause entre stratégies
                    time.sleep(self.delay)
                    
                except Exception as e:
                    logger.error(f"Erreur stratégie {i+1}: {e}")
                    continue
            
            logger.info(f"\\n=== SCRAPING TERMINÉ ===")
            logger.info(f"Total final: {len(all_lawyers)} avocats/cabinets uniques")
            logger.info(f"Stratégies exécutées: {len(strategy_results)}")
            
            # Ajouter les métadonnées de session
            session_metadata = {
                'strategies_executed': strategy_results,
                'total_strategies': len(strategies),
                'total_lawyers_found': len(all_lawyers),
                'scraping_duration': str(datetime.now() - self.session_start),
                'mode': 'test' if test_mode else 'complete'
            }
            
            self.lawyers_data = all_lawyers
            self.session_metadata = session_metadata
            
            return all_lawyers
            
        except Exception as e:
            logger.error(f"Erreur scraping global: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Driver fermé")
    
    def save_comprehensive_results(self, filename_base="barreau_nantes_complete"):
        """Sauvegarde complète des résultats avec métadonnées"""
        if not self.lawyers_data:
            logger.warning("Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON détaillé avec métadonnées
        json_filename = f"{filename_base}_{timestamp}.json"
        data_to_save = {
            'metadata': getattr(self, 'session_metadata', {}),
            'lawyers': self.lawyers_data,
            'extraction_timestamp': datetime.now().isoformat(),
            'total_records': len(self.lawyers_data)
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        
        # CSV simplifié pour analyse
        csv_filename = f"{filename_base}_{timestamp}.csv"
        if self.lawyers_data:
            all_keys = set()
            for lawyer in self.lawyers_data:
                all_keys.update(lawyer.keys())
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        # Rapport de statistiques détaillé
        stats = {
            'extraction_summary': {
                'total_avocats': len(self.lawyers_data),
                'avec_email': len([l for l in self.lawyers_data if l.get('email')]),
                'avec_telephone': len([l for l in self.lawyers_data if l.get('telephone')]),
                'avec_adresse': len([l for l in self.lawyers_data if l.get('adresse')]),
                'avec_cabinet': len([l for l in self.lawyers_data if l.get('cabinet') or l.get('nom_cabinet')]),
                'avec_nom_complet': len([l for l in self.lawyers_data if l.get('nom_complet')]),
            },
            'sources_extraction': {},
            'strategies_performance': getattr(self, 'session_metadata', {}).get('strategies_executed', []),
            'duree_scraping': str(datetime.now() - self.session_start),
            'timestamp_rapport': datetime.now().isoformat()
        }
        
        # Compter les sources d'extraction
        for lawyer in self.lawyers_data:
            source = lawyer.get('source_extraction', 'unknown')
            stats['sources_extraction'][source] = stats['sources_extraction'].get(source, 0) + 1
        
        stats_filename = f"{filename_base}_rapport_{timestamp}.json"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        # Créer aussi un fichier Excel-friendly CSV avec encoding windows
        csv_excel_filename = f"{filename_base}_excel_{timestamp}.csv"
        with open(csv_excel_filename, 'w', newline='', encoding='cp1252', errors='replace') as f:
            if self.lawyers_data:
                all_keys = sorted(set().union(*(d.keys() for d in self.lawyers_data)))
                writer = csv.DictWriter(f, fieldnames=all_keys, delimiter=';')
                writer.writeheader()
                writer.writerows(self.lawyers_data)
        
        logger.info(f"Fichiers sauvegardés:")
        logger.info(f"  - JSON complet: {json_filename}")
        logger.info(f"  - CSV UTF-8: {csv_filename}")
        logger.info(f"  - CSV Excel: {csv_excel_filename}")
        logger.info(f"  - Rapport: {stats_filename}")
        
        # Afficher les statistiques
        print(f"\\n=== RAPPORT FINAL ===")
        print(f"Total avocats/cabinets: {stats['extraction_summary']['total_avocats']}")
        print(f"Avec email: {stats['extraction_summary']['avec_email']}")
        print(f"Avec téléphone: {stats['extraction_summary']['avec_telephone']}")
        print(f"Avec adresse: {stats['extraction_summary']['avec_adresse']}")
        print(f"Avec cabinet: {stats['extraction_summary']['avec_cabinet']}")
        print(f"Avec nom complet: {stats['extraction_summary']['avec_nom_complet']}")
        print(f"\\nSources d'extraction:")
        for source, count in stats['sources_extraction'].items():
            print(f"  {source}: {count}")
        print(f"\\nDurée totale: {stats['duree_scraping']}")
        
        return json_filename, csv_filename, csv_excel_filename, stats_filename

def main():
    parser = argparse.ArgumentParser(description='Scraper Barreau de Nantes - Version finale complète')
    parser.add_argument('--test', action='store_true', help='Mode test (stratégies limitées)')
    parser.add_argument('--headless', action='store_true', help='Mode sans interface (recommandé)')
    parser.add_argument('--delay', type=int, default=3, help='Délai entre requêtes (secondes)')
    parser.add_argument('--max-strategies', type=int, help='Nombre max de stratégies à exécuter')
    
    args = parser.parse_args()
    
    print("=== SCRAPER BARREAU DE NANTES - VERSION FINALE ===")
    print(f"Mode: {'TEST' if args.test else 'COMPLET'}")
    print(f"Interface: {'Headless' if args.headless else 'Visuel'}")
    print(f"Délai: {args.delay}s")
    if args.max_strategies:
        print(f"Max stratégies: {args.max_strategies}")
    print()
    
    scraper = BarreauNantesFinalScraper(
        headless=args.headless,
        delay=args.delay
    )
    
    try:
        results = scraper.scrape_all_comprehensive(
            test_mode=args.test,
            max_strategies=args.max_strategies
        )
        
        print(f"\\n=== RÉSULTATS BRUTS ===")
        print(f"Entrées extraites: {len(results)}")
        
        # Afficher quelques exemples
        for i, lawyer in enumerate(results[:5]):
            print(f"\\n--- Entrée {i+1} ---")
            for key, value in lawyer.items():
                if isinstance(value, list):
                    print(f"{key}: {', '.join(map(str, value))}")
                else:
                    print(f"{key}: {value}")
        
        if len(results) > 5:
            print(f"\\n... et {len(results) - 5} autres entrées")
        
        # Sauvegarder avec la méthode complète
        files = scraper.save_comprehensive_results()
        
        print(f"\\nFichiers créés:")
        for file_path in files:
            print(f"- {file_path}")
        
        print(f"\\n🎉 === TERMINÉ AVEC SUCCÈS === 🎉")
        
        return results
        
    except KeyboardInterrupt:
        print("\\n=== INTERRUPTION UTILISATEUR ===")
        logger.info("Scraping interrompu par l'utilisateur")
        return []
    except Exception as e:
        print(f"\\n=== ERREUR ===")
        print(f"Erreur: {e}")
        logger.error(f"Erreur fatale: {e}")
        return []

if __name__ == "__main__":
    main()