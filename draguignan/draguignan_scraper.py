#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper FINAL CORRIGÉ pour le Barreau de Draguignan
Corrections: parsing noms/prénoms, vraies spécialisations, sources
"""

import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

class DraguignanFinalScraper:
    def __init__(self, headless=False):
        """Initialise le scraper"""
        self.options = Options()
        if headless:
            self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        self.driver = None
        self.base_url = "https://www.avocazur.com/fr/annuaire/"
        self.letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                       'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Z']
        
    def start_driver(self):
        """Démarre le navigateur"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            print("✓ Navigateur démarré")
            return True
        except Exception as e:
            print(f"✗ Erreur: {e}")
            return False
    
    def close_driver(self):
        """Ferme le navigateur"""
        if self.driver:
            self.driver.quit()
            print("✓ Navigateur fermé")
    
    def parse_name_advanced(self, raw_name_text):
        """Parse avancé pour séparer correctement nom et prénom"""
        if not raw_name_text:
            return None, None
        
        # Nettoyer le texte
        text = raw_name_text.strip()
        
        # Supprimer les préfixes/suffixes d'entreprise
        text = re.sub(r'^(SELARL|AARPI|SCP|SELAS|SELASU|Cabinet)\s+', '', text, flags=re.I)
        text = re.sub(r'\s+(SELARL|AARPI|SCP|SELAS|SELASU|Cabinet)\s+.*$', '', text, flags=re.I)
        text = re.sub(r'\s+(AVOCAT|AVOCATS?|ASSOCIES?|ET|&).*$', '', text, flags=re.I)
        
        # Patterns améliorés avec plus de flexibilité
        patterns = [
            # Pattern 1: NOM TRES COMPOSE AVEC TIRETS + Prénom (ex: BARRY MARTIN-DELONGCHAMPS FRANCOIS)
            r'^([A-ZÀ-ŸŒ]+(?:[\s\-][A-ZÀ-ŸŒ]+){2,})\s+([A-ZÀ-ŸŒ]+)\s*$',
            # Pattern 2: NOM COMPOSE Prénom-composé avec minuscule (ex: BERNARDI Jean-louis)
            r'^([A-ZÀ-ŸŒ]+(?:[\s\-][A-ZÀ-ŸŒ]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+[\-][a-zà-ÿ]+)\s*$',
            # Pattern 3: NOM COMPOSE Prénom-composé majuscule (ex: MARTIN-DELONGCHAMPS Jean-Claude)  
            r'^([A-ZÀ-ŸŒ]+(?:[\s\-][A-ZÀ-ŸŒ]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:[\-][A-ZÀ-Ÿ][a-zà-ÿ]*)+)\s*$',
            # Pattern 4: NOM COMPOSE Prénom simple (ex: MARTIN-DELONGCHAMPS François)
            r'^([A-ZÀ-ŸŒ]+(?:[\s\-][A-ZÀ-ŸŒ]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)\s*$',
            # Pattern 5: NOM DE/DU Prénom
            r'^([A-ZÀ-ŸŒ]+(?:\s(?:DE|DU|VAN|VON|LA|LE|DES)\s[A-ZÀ-ŸŒ]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:[\s\-][A-ZÀ-Ÿ][a-zà-ÿ]*)*)\s*$',
            # Pattern 6: Standard NOM Prénom (garde en dernier)
            r'^([A-ZÀ-ŸŒ]+(?:[\s][A-ZÀ-ŸŒ]+)*)\s+([A-ZÀ-Ÿ][a-zà-ÿ]+(?:[\s\-][A-ZÀ-Ÿ][a-zà-ÿ]*)*)\s*$'
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.match(pattern, text.strip())
            if match:
                nom = match.group(1).strip()
                prenom = match.group(2).strip()
                
                # Validation adaptée selon le pattern
                if i == 0:  # Pattern très composé - moins strict
                    # Pour les noms très composés, accepter même si prénom est en majuscules
                    if len(nom) >= 3 and len(prenom) >= 2:
                        return nom, prenom
                else:
                    # Validation normale améliorée
                    valid_nom = nom.replace(' ', '').replace('-', '').isalpha()
                    valid_prenom = prenom.replace(' ', '').replace('-', '').isalpha()
                    
                    # Mots interdits plus spécifiques (éviter faux positifs sur "Gaetan" contenant "et")
                    forbidden_words_exact = ['AVOCAT', 'CABINET', 'SOCIETE', 'AVOCATS', 'ASSOCIES']
                    no_company_nom = not any(word == nom.upper() or f' {word} ' in f' {nom.upper()} ' for word in forbidden_words_exact)
                    no_company_prenom = not any(word == prenom.upper() or f' {word} ' in f' {prenom.upper()} ' for word in forbidden_words_exact)
                    
                    if (len(nom) >= 2 and len(prenom) >= 2 and 
                        valid_nom and valid_prenom and
                        no_company_nom and no_company_prenom):
                        return nom, prenom
        
        return None, None
    
    def extract_avocat_from_row(self, row, row_index=0):
        """Extrait les infos d'un avocat depuis une ligne de tableau"""
        avocat = {
            'nom': '',
            'prenom': '',
            'nom_complet': '',
            'cabinet': '',
            'email': '',
            'telephone': '',
            'fax': '',
            'adresse': '',
            'ville': '',
            'code_postal': '',
            'annee_inscription': '',
            'specialisation': '',
            'competences': '',
            'source': ''
        }
        
        try:
            # Extraire le nom principal
            th = row.find('th')
            if th:
                # Récupérer le texte principal (hors <small>)
                main_text = ''
                
                # Méthode simplifiée - récupérer tout le texte puis nettoyer
                full_text = th.get_text('\n', strip=True)
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                
                # Prendre la première ligne qui ne contient pas de mots-clés de structure
                for line in lines:
                    if not any(kw in line.upper() for kw in ['SELARL', 'AARPI', 'SCP', 'SELAS', 'CABINET']):
                        main_text = line
                        break
                
                if not main_text and lines:
                    main_text = lines[0]
                
                # Parser le nom
                nom, prenom = self.parse_name_advanced(main_text)
                
                if nom and prenom:
                    avocat['nom'] = nom
                    avocat['prenom'] = prenom
                    avocat['nom_complet'] = f"{nom} {prenom}"
                else:
                    avocat['nom_complet'] = main_text.strip()
                
                # Cabinet depuis <small>
                small = th.find('small')
                if small:
                    cabinet = small.get_text(strip=True)
                    if cabinet:
                        avocat['cabinet'] = cabinet
            
            # Ville depuis la colonne de droite
            td = row.find('td', class_='text-right')
            if td:
                ville_text = td.get_text(strip=True).replace('+ Plus de détails', '').strip()
                ville_match = re.match(r'^(.+?)\s+\((\d{5})\)$', ville_text)
                if ville_match:
                    avocat['ville'] = ville_match.group(1).strip()
                    avocat['code_postal'] = ville_match.group(2).strip()
                else:
                    avocat['ville'] = ville_text
            
            # Source - URL de la fiche (basée sur l'ID de la ligne)
            row_id = row.get('id', '')
            if row_id:
                # La source serait l'URL actuelle avec un lien vers la fiche
                letter = ''
                if avocat['nom']:
                    letter = avocat['nom'][0].upper()
                elif avocat['nom_complet']:
                    letter = avocat['nom_complet'][0].upper()
                
                if letter:
                    avocat['source'] = f"https://www.avocazur.com/fr/annuaire/?lettre={letter}#{row_id}"
        
        except Exception as e:
            print(f"    ⚠ Erreur parsing row {row_index}: {e}")
        
        return avocat
    
    def click_and_get_details(self, avocat, row_id):
        """Clique sur une ligne et récupère les détails complets"""
        try:
            # Trouver et cliquer sur la ligne
            row_element = self.driver.find_element(By.ID, row_id)
            self.driver.execute_script("arguments[0].click();", row_element)
            time.sleep(1.5)  # Attendre l'animation
            
            # Parser la page mise à jour
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Trouver la section de détails dépliée
            detail_id = row_id.replace('t', 's')
            detail_section = soup.find('div', id=detail_id)
            
            if detail_section:
                detail_text = detail_section.get_text()
                
                # Email
                email_link = detail_section.find('a', href=re.compile(r'mailto:'))
                if email_link:
                    href = email_link.get('href', '')
                    if href.startswith('mailto:'):
                        email = href.replace('mailto:', '').strip()
                        if email and '@' in email:
                            avocat['email'] = email
                
                # Téléphone
                tel_match = re.search(r'Tél\s*:\s*([0-9\s\.\-\(\)]+)', detail_text)
                if tel_match:
                    tel = re.sub(r'[^\d\.\-\+\s]', '', tel_match.group(1)).strip()
                    if len(tel) >= 10:
                        avocat['telephone'] = tel
                
                # Fax
                fax_match = re.search(r'Fax\s*:\s*([0-9\s\.\-\(\)]+)', detail_text)
                if fax_match:
                    fax = re.sub(r'[^\d\.\-\+\s]', '', fax_match.group(1)).strip()
                    if len(fax) >= 10:
                        avocat['fax'] = fax
                
                # Compétences/Spécialisations VRAIES
                comp_section = detail_section.find('h5', string=re.compile(r'Compétences'))
                if comp_section:
                    comp_p = comp_section.find_next_sibling('p')
                    if comp_p:
                        comp_text = comp_p.get_text(strip=True)
                        # Nettoyer du lien Google Maps et autres éléments parasites
                        comp_clean = re.sub(r'Localiser avec Google Maps.*$', '', comp_text, flags=re.DOTALL).strip()
                        comp_clean = re.sub(r'\s+', ' ', comp_clean).strip()
                        
                        if comp_clean and comp_clean.lower() != 'généraliste':
                            avocat['competences'] = comp_clean
                            avocat['specialisation'] = comp_clean
                        else:
                            avocat['competences'] = 'Généraliste'
                            avocat['specialisation'] = 'Généraliste'
                
                # Adresse complète
                cabinet_section = detail_section.find('h5', string=re.compile(r'Cabinet principal'))
                if cabinet_section:
                    addr_elements = []
                    current = cabinet_section.next_sibling
                    
                    while current:
                        if hasattr(current, 'get_text'):
                            text = current.get_text(strip=True)
                            if (text and not any(prefix in text for prefix in ['Tél:', 'Fax:', 'Email:', 'Localiser']) 
                                and len(text) > 3):
                                addr_elements.append(text)
                        elif hasattr(current, 'strip') and current.strip():
                            text = current.strip()
                            if len(text) > 3:
                                addr_elements.append(text)
                        
                        current = current.next_sibling
                        if hasattr(current, 'name') and current.name in ['strong', 'h5']:
                            break
                    
                    if addr_elements:
                        avocat['adresse'] = ', '.join(addr_elements[:3])  # Limiter à 3 éléments
                
                # Année d'inscription (si présente)
                year_match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', detail_text)
                if year_match:
                    avocat['annee_inscription'] = year_match.group(0)
            
            # Replier la section
            self.driver.execute_script("arguments[0].click();", row_element)
            time.sleep(0.5)
            
        except Exception as e:
            print(f"    ⚠ Erreur détails {avocat.get('nom_complet', '')}: {e}")
        
        return avocat
    
    def scrape_letter_complete(self, letter):
        """Scrape complet d'une lettre avec détails"""
        print(f"🔤 Lettre {letter}...")
        
        url = f"{self.base_url}?lettre={letter}"
        avocats = []
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Attendre le tableau
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.liste tbody"))
            )
            
            # Parser la page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Trouver le tableau
            table = soup.find('table', class_='liste')
            if not table:
                return []
            
            tbody = table.find('tbody')
            if not tbody:
                return []
            
            # Traiter chaque ligne d'avocat
            avocat_rows = tbody.find_all('tr', class_='t')
            print(f"  → {len(avocat_rows)} avocat(s) trouvé(s)")
            
            for i, row in enumerate(avocat_rows):
                try:
                    # Extraction de base
                    avocat = self.extract_avocat_from_row(row, i)
                    
                    if avocat['nom_complet']:
                        # Extraction des détails en cliquant
                        row_id = row.get('id', '')
                        if row_id:
                            avocat = self.click_and_get_details(avocat, row_id)
                        
                        avocats.append(avocat)
                        
                        # Afficher le résultat
                        name_display = f"{avocat.get('nom', '')} {avocat.get('prenom', '')}".strip()
                        if not name_display:
                            name_display = avocat['nom_complet']
                        
                        spec_display = avocat.get('specialisation', 'Généraliste')[:30]
                        print(f"    ✓ {name_display} - {spec_display}")
                
                except Exception as e:
                    print(f"    ✗ Erreur ligne {i}: {e}")
                    continue
            
            return avocats
            
        except Exception as e:
            print(f"  ✗ Erreur {letter}: {e}")
            return []
    
    def scrape_all_corrected(self, mode='test'):
        """Scrape avec toutes les corrections"""
        print(f"\n📊 Scraping CORRIGÉ mode {mode.upper()}")
        print("Corrections: parsing noms, vraies spécialisations, sources")
        print("="*70)
        
        letters = ['A', 'B'] if mode == 'test' else self.letters
        all_avocats = []
        
        for letter in letters:
            letter_avocats = self.scrape_letter_complete(letter)
            all_avocats.extend(letter_avocats)
            time.sleep(2)
        
        # Déduplication par nom complet
        unique_avocats = []
        seen = set()
        
        for avocat in all_avocats:
            key = avocat['nom_complet'].upper().strip()
            if key not in seen and avocat['nom_complet']:
                seen.add(key)
                unique_avocats.append(avocat)
        
        print(f"\n✓ {len(unique_avocats)} avocats uniques extraits")
        return unique_avocats
    
    def save_results_corrected(self, data, mode='test'):
        """Sauvegarde avec toutes les corrections"""
        if not data:
            print("⚠ Aucune donnée")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"DRAGUIGNAN_{mode.upper()}_CORRECTED"
        
        # JSON
        json_file = f"/Users/paularnould/{prefix}_{len(data)}avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ JSON: {json_file}")
        
        # CSV avec colonnes réorganisées
        csv_file = f"/Users/paularnould/{prefix}_{len(data)}avocats_{timestamp}.csv"
        df = pd.DataFrame(data)
        
        # Réorganiser les colonnes selon vos besoins
        columns_order = ['nom', 'prenom', 'nom_complet', 'cabinet', 'email', 'telephone', 'fax',
                        'adresse', 'ville', 'code_postal', 'annee_inscription', 
                        'specialisation', 'competences', 'source']
        
        # S'assurer que toutes les colonnes existent
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[columns_order]
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"✓ CSV: {csv_file}")
        
        # Emails uniques
        emails = [a['email'] for a in data if a.get('email') and a['email'].strip()]
        unique_emails = list(set(emails))
        
        if unique_emails:
            email_file = f"/Users/paularnould/{prefix}_EMAILS_{len(unique_emails)}emails_{timestamp}.txt"
            with open(email_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sorted(unique_emails)))
            print(f"✓ {len(unique_emails)} emails uniques: {email_file}")
        
        # Rapport amélioré
        report_file = f"/Users/paularnould/{prefix}_RAPPORT_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("RAPPORT FINAL CORRIGÉ - BARREAU DE DRAGUIGNAN\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Site: {self.base_url}\n")
            f.write(f"Mode: {mode.upper()}\n\n")
            
            # Statistiques détaillées
            with_names = sum(1 for a in data if a.get('nom') and a.get('prenom'))
            with_emails = len(unique_emails)
            with_phones = sum(1 for a in data if a.get('telephone'))
            with_specs = sum(1 for a in data if a.get('specialisation') and a['specialisation'] != 'Généraliste')
            with_sources = sum(1 for a in data if a.get('source'))
            
            f.write("STATISTIQUES QUALITÉ:\n")
            f.write("-"*40 + "\n")
            f.write(f"Total avocats: {len(data)}\n")
            f.write(f"Noms/prénoms séparés: {with_names}/{len(data)} ({with_names/len(data)*100:.1f}%)\n")
            f.write(f"Emails uniques: {with_emails}/{len(data)} ({with_emails/len(data)*100:.1f}%)\n")
            f.write(f"Téléphones: {with_phones}/{len(data)} ({with_phones/len(data)*100:.1f}%)\n")
            f.write(f"Spécialisations réelles: {with_specs}/{len(data)} ({with_specs/len(data)*100:.1f}%)\n")
            f.write(f"Sources URL: {with_sources}/{len(data)} ({with_sources/len(data)*100:.1f}%)\n")
            
            # Spécialisations trouvées
            specialisations = {}
            for avocat in data:
                spec = avocat.get('specialisation', 'Non précisé')
                specialisations[spec] = specialisations.get(spec, 0) + 1
            
            f.write(f"\n\nSPÉCIALISATIONS IDENTIFIÉES:\n")
            f.write("-"*40 + "\n")
            for spec, count in sorted(specialisations.items(), key=lambda x: x[1], reverse=True):
                f.write(f"  {spec}: {count} avocat(s)\n")
            
            # Échantillon avec toutes les infos
            f.write(f"\n\nÉCHANTILLON DÉTAILLÉ (10 premiers):\n")
            f.write("-"*40 + "\n")
            for i, avocat in enumerate(data[:10], 1):
                f.write(f"{i:2d}. {avocat.get('nom', '')} {avocat.get('prenom', '')}\n")
                if avocat.get('email'):
                    f.write(f"    Email: {avocat['email']}\n")
                if avocat.get('specialisation') and avocat['specialisation'] != 'Généraliste':
                    f.write(f"    Spécialisation: {avocat['specialisation']}\n")
                if avocat.get('cabinet'):
                    f.write(f"    Cabinet: {avocat['cabinet']}\n")
                if avocat.get('source'):
                    f.write(f"    Source: {avocat['source']}\n")
                f.write("\n")
        
        print(f"✓ Rapport: {report_file}")
        
        # Statistiques finales
        print(f"\n📊 Statistiques de qualité:")
        print(f"   • Noms séparés: {with_names}/{len(data)} ({with_names/len(data)*100:.1f}%)")
        print(f"   • Emails uniques: {with_emails}")
        print(f"   • Spécialisations réelles: {with_specs}")
        print(f"   • Sources ajoutées: {with_sources}")
        
        return json_file, csv_file

def main():
    """Fonction principale"""
    import sys
    
    print("="*80)
    print("SCRAPER DRAGUIGNAN - VERSION FINALE CORRIGÉE")
    print("="*80)
    print("Corrections: parsing noms/prénoms + vraies spécialisations + sources")
    
    mode = 'test' if 'test' in sys.argv else 'production'
    headless = '--headless' in sys.argv
    
    scraper = DraguignanFinalScraper(headless=headless)
    
    try:
        if not scraper.start_driver():
            return 1
        
        # Extraction corrigée
        avocats = scraper.scrape_all_corrected(mode)
        
        if not avocats:
            print("⚠ Aucun résultat")
            return 1
        
        # Sauvegarde corrigée
        scraper.save_results_corrected(avocats, mode)
        
        print(f"\n🎉 EXTRACTION CORRIGÉE TERMINÉE - {len(avocats)} avocats")
        return 0
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    exit(main())