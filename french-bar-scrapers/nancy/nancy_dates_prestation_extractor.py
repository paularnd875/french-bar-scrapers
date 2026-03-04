#!/usr/bin/env python3
"""
Extracteur spécialisé pour les dates de prestation de serment
Charge les données existantes et ajoute les dates manquantes
"""

import time
import json
import re
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NancyDatesExtractor:
    def __init__(self):
        self.driver = None
        self.data = []
        self.dates_found = 0
        
    def load_existing_data(self):
        """Charge les données existantes"""
        try:
            with open('/Users/paularnould/NANCY_PORTFOLIOS_COMPLET_20260218_093535.json', 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"✅ Données chargées: {len(self.data)} avocats")
        except Exception as e:
            logger.error(f"❌ Erreur chargement: {e}")
            return False
        return True
    
    def setup_driver(self):
        """Configure un driver Chrome optimisé pour l'extraction de texte"""
        options = webdriver.ChromeOptions()
        # Mode non-headless pour assurer le chargement complet du contenu
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        # Essayer d'abord avec interface visible pour debug
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        })
    
    def extract_prestation_date_robust(self, url, nom):
        """Extraction robuste des dates de prestation de serment"""
        try:
            logger.info(f"🔍 Extraction pour {nom}: {url}")
            self.driver.get(url)
            
            # Attendre le chargement complet
            time.sleep(3)
            
            # Stratégie 1: Sélecteur CSS spécifique
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "p.has-text-align-right")
                for elem in elements:
                    text = elem.text.strip()
                    if "prestation de serment" in text.lower():
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                        if date_match:
                            date_str = date_match.group(1)
                            year = int(date_str.split('/')[-1])
                            logger.info(f"   ✅ Méthode 1: {date_str} ({year})")
                            return year, date_str
            except:
                pass
            
            # Stratégie 2: Tous les paragraphes
            try:
                paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    text = p.text.strip()
                    if "prestation de serment" in text.lower():
                        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
                        if date_match:
                            date_str = date_match.group(1)
                            year = int(date_str.split('/')[-1])
                            logger.info(f"   ✅ Méthode 2: {date_str} ({year})")
                            return year, date_str
            except:
                pass
            
            # Stratégie 3: Texte complet de la page
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Patterns multiples pour "prestation de serment"
                patterns = [
                    r'prestation\s+de\s+serment\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
                    r'serment\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})',
                    r'(\d{1,2}/\d{1,2}/\d{4})\s*.*prestation',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        year = int(date_str.split('/')[-1])
                        if 1950 <= year <= 2026:  # Validation année
                            logger.info(f"   ✅ Méthode 3: {date_str} ({year})")
                            return year, date_str
            except:
                pass
            
            # Stratégie 4: Chercher toutes les dates et prendre la plus plausible
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                all_dates = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})', page_text)
                
                for date_str in all_dates:
                    year = int(date_str.split('/')[-1])
                    # Si c'est une année plausible pour un avocat
                    if 1980 <= year <= 2025:
                        # Vérifier le contexte autour
                        context_pattern = rf'.{{0,50}}{re.escape(date_str)}.{{0,50}}'
                        context_match = re.search(context_pattern, page_text, re.IGNORECASE)
                        if context_match:
                            context = context_match.group(0)
                            if any(word in context.lower() for word in ['prestation', 'serment', 'barreau', 'avocat']):
                                logger.info(f"   ✅ Méthode 4: {date_str} ({year}) [contexte: {context[:30]}...]")
                                return year, date_str
            except:
                pass
                
            logger.warning(f"   ❌ Aucune date trouvée pour {nom}")
            return None, None
            
        except Exception as e:
            logger.error(f"   ❌ Erreur pour {nom}: {e}")
            return None, None
    
    def run(self):
        """Exécute l'extraction des dates manquantes"""
        logger.info("🚀 EXTRACTION SPÉCIALISÉE DES DATES DE PRESTATION DE SERMENT")
        logger.info("=" * 70)
        
        if not self.load_existing_data():
            return
        
        self.setup_driver()
        
        try:
            # Traiter seulement les avocats sans date de prestation
            avocats_sans_date = [a for a in self.data if not a.get('date_prestation_serment')]
            logger.info(f"📊 {len(avocats_sans_date)} avocats à traiter")
            
            for i, avocat in enumerate(avocats_sans_date, 1):
                if i % 10 == 0:
                    logger.info(f"📈 Progression: {i}/{len(avocats_sans_date)} ({self.dates_found} dates trouvées)")
                
                if avocat.get('url'):
                    year, date = self.extract_prestation_date_robust(avocat['url'], avocat['nom'])
                    
                    if year and date:
                        # Mettre à jour les données
                        avocat['annee_inscription'] = year
                        avocat['date_prestation_serment'] = date
                        self.dates_found += 1
                
                # Pause pour éviter la surcharge
                time.sleep(1)
            
            # Sauvegarder les résultats mis à jour
            self.save_updated_data()
            
        except Exception as e:
            logger.error(f"❌ Erreur générale: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_updated_data(self):
        """Sauvegarde les données mises à jour"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Statistiques
        total = len(self.data)
        with_dates = sum(1 for a in self.data if a.get('date_prestation_serment'))
        with_years = sum(1 for a in self.data if a.get('annee_inscription'))
        
        # Sauvegarder JSON mis à jour
        json_file = f"NANCY_FINAL_AVEC_DATES_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        # Sauvegarder CSV mis à jour
        csv_file = f"NANCY_FINAL_AVEC_DATES_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'index', 'nom', 'prenom', 'nom_famille', 'email', 'telephone', 'telephone_2',
                'adresse', 'adresse_complete', 'code_postal', 'ville', 'annee_inscription', 
                'date_prestation_serment', 'specialites', 'specialite', 'competences', 'langues', 
                'cabinet', 'titre', 'site_web', 'description', 'horaires', 'url'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for avocat in self.data:
                row = avocat.copy()
                # Convertir les listes en chaînes
                if row.get('specialites'):
                    row['specialites'] = '; '.join(row['specialites'])
                if row.get('competences'):
                    row['competences'] = '; '.join(row['competences'])
                if row.get('langues'):
                    row['langues'] = '; '.join(row['langues'])
                writer.writerow(row)
        
        # Rapport final
        print("\n" + "=" * 70)
        print("🎉 EXTRACTION DES DATES TERMINÉE")
        print("=" * 70)
        print(f"✅ Total avocats: {total}")
        print(f"✅ Nouvelles dates extraites: {self.dates_found}")
        print(f"✅ Total avec dates: {with_dates} ({with_dates/total*100:.1f}%)")
        print(f"✅ Total avec années: {with_years} ({with_years/total*100:.1f}%)")
        print(f"📁 Fichiers générés:")
        print(f"   - {json_file}")
        print(f"   - {csv_file}")
        print("=" * 70)

if __name__ == "__main__":
    extractor = NancyDatesExtractor()
    extractor.run()