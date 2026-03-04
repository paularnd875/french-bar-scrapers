#!/usr/bin/env python3
"""
🎯 SCRAPER PRODUCTION - BARREAU D'ARGENTAN
Extraction complète et optimisée de tous les avocats
Version finale avec gestion des cookies et extraction précise
"""

import time
import random
import json
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re

class ArgentanScraperProduction:
    def __init__(self, headless=True):
        self.headless = headless
        self.base_url = "http://www.barreau-argentan.fr"
        self.list_url = f"{self.base_url}/annuaire/liste-des-avocats-de-a-a-d.html"
        self.lawyers_data = []
        self.setup_driver()
    
    def setup_driver(self):
        """Configuration Chrome optimisée"""
        chrome_options = Options()
        ua = UserAgent()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Anti-détection
        chrome_options.add_argument(f'--user-agent={ua.random}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1366,768')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def human_delay(self, min_sec=1, max_sec=3):
        """Délai humain aléatoire"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def accept_cookies(self):
        """Gestion automatique des cookies"""
        cookie_selectors = [
            "//button[contains(text(), 'Accepter')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'OK')]",
            "//*[contains(@class, 'cookie')]//button"
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                cookie_btn.click()
                print("🍪 Cookies acceptés")
                self.human_delay(1, 2)
                return True
            except:
                continue
        return False
    
    def extract_all_lawyer_links(self):
        """Extrait tous les liens des avocats"""
        try:
            print("🔍 Extraction de tous les liens d'avocats...")
            
            self.driver.get(self.list_url)
            self.human_delay(3, 5)
            
            # Gérer les cookies
            self.accept_cookies()
            
            # Parser la page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Trouver tous les liens d'avocats
            lawyer_links = []
            toclinks = soup.find_all('a', class_='toclink')
            
            for link in toclinks:
                href = link.get('href')
                text = link.get_text().strip()
                
                # Filtrer seulement les liens d'avocats individuels
                if href and 'start=' in href and 'Maître' in text:
                    full_url = self.base_url + href if href.startswith('/') else href
                    
                    # Extraire le nom proprement
                    clean_name = text.replace('Maître ', '').strip()
                    
                    lawyer_links.append({
                        'name': clean_name,
                        'url': full_url,
                        'start_param': href.split('start=')[1] if 'start=' in href else '0'
                    })
            
            print(f"📋 {len(lawyer_links)} avocats trouvés:")
            for i, link in enumerate(lawyer_links[:5]):
                print(f"  {i+1}. {link['name']}")
            if len(lawyer_links) > 5:
                print(f"  ... et {len(lawyer_links)-5} autres")
            
            return lawyer_links
            
        except Exception as e:
            print(f"❌ Erreur extraction liens: {e}")
            return []
    
    def extract_lawyer_data(self, lawyer_link):
        """Extrait les données détaillées d'un avocat"""
        try:
            print(f"👤 Extraction: {lawyer_link['name']}")
            
            self.driver.get(lawyer_link['url'])
            self.human_delay(2, 4)
            
            # Parser la page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Initialiser les données
            lawyer_data = {
                'prenom': '',
                'nom': '',
                'email': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'adresse': '',
                'telephone': '',
                'fax': '',
                'site_web': '',
                'url_source': lawyer_link['url']
            }
            
            # Extraire nom et prénom du lien (plus fiable)
            name_parts = lawyer_link['name'].split()
            if len(name_parts) >= 2:
                lawyer_data['prenom'] = name_parts[0]
                lawyer_data['nom'] = ' '.join(name_parts[1:])
            
            # Extraire le contenu principal de l'article
            article_content = soup.find('div', class_='article-content')
            if not article_content:
                article_content = soup
            
            content_text = article_content.get_text()
            
            # EMAIL - Méthode précise
            # D'abord chercher les liens mailto
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            if mailto_links:
                email_href = mailto_links[0].get('href')
                lawyer_data['email'] = email_href.replace('mailto:', '').strip()
            else:
                # Sinon regex
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content_text)
                if email_match:
                    lawyer_data['email'] = email_match.group(1)
            
            # TÉLÉPHONE et FAX
            phone_patterns = [
                r'Tél[\s:]*([0-9\s\.]{10,})',
                r'Tel[\s:]*([0-9\s\.]{10,})',
                r'Téléphone[\s:]*([0-9\s\.]{10,})',
                r'(0[1-9](?:[\s\.]?\d{2}){4})'
            ]
            
            for pattern in phone_patterns:
                phone_match = re.search(pattern, content_text, re.IGNORECASE)
                if phone_match:
                    phone = re.sub(r'[^0-9]', '', phone_match.group(1))
                    if len(phone) == 10:
                        lawyer_data['telephone'] = phone
                        break
            
            # FAX
            fax_match = re.search(r'Fax[\s:]*([0-9\s\.]{10,})', content_text, re.IGNORECASE)
            if fax_match:
                fax = re.sub(r'[^0-9]', '', fax_match.group(1))
                if len(fax) == 10:
                    lawyer_data['fax'] = fax
            
            # SITE WEB
            web_patterns = [
                r'Web[\s:]*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'Site[\s:]*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'www\.([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ]
            
            for pattern in web_patterns:
                web_match = re.search(pattern, content_text, re.IGNORECASE)
                if web_match:
                    lawyer_data['site_web'] = web_match.group(1)
                    break
            
            # ADRESSE - Chercher dans les paragraphes
            paragraphs = article_content.find_all('p') if article_content else []
            for p in paragraphs:
                p_text = p.get_text().strip()
                
                # Si le paragraphe contient un code postal ou des mots-clés d'adresse
                if re.search(r'\b(\d{5}|rue|avenue|boulevard|place|chemin|allée)\b', p_text, re.IGNORECASE):
                    if len(p_text) > 10 and not 'Tél' in p_text and not '@' in p_text:
                        lawyer_data['adresse'] = p_text.strip()
                        break
            
            # ANNÉE D'INSCRIPTION
            year_patterns = [
                r'inscrit[^\d]*((?:19|20)\d{2})',
                r'inscription[^\d]*((?:19|20)\d{2})',
                r'barreau[^\d]*((?:19|20)\d{2})',
                r'((?:19|20)\d{2})[^\d]*inscrit',
                r'((?:19|20)\d{2})[^\d]*inscription'
            ]
            
            for pattern in year_patterns:
                year_match = re.search(pattern, content_text, re.IGNORECASE)
                if year_match:
                    lawyer_data['annee_inscription'] = year_match.group(1)
                    break
            
            # SPÉCIALISATIONS
            specializations_keywords = [
                'droit civil', 'droit pénal', 'droit commercial', 'droit du travail',
                'droit de la famille', 'droit immobilier', 'droit des sociétés',
                'droit fiscal', 'droit public', 'droit social', 'droit administratif',
                'droit des affaires', 'droit bancaire', 'droit de la construction',
                'droit de l\'environnement', 'droit de la santé', 'droit rural',
                'divorce', 'succession', 'contrat', 'responsabilité civile'
            ]
            
            content_lower = content_text.lower()
            found_specs = [spec for spec in specializations_keywords if spec in content_lower]
            lawyer_data['specialisations'] = found_specs
            
            # STRUCTURE (Cabinet, SCP, etc.)
            structure_patterns = [
                r'(SCP[^\n.]{0,50})',
                r'(Cabinet[^\n.]{0,50})',
                r'(Société[^\n.]{0,50})',
                r'(SELARL[^\n.]{0,50})',
                r'(SELAFA[^\n.]{0,50})'
            ]
            
            for pattern in structure_patterns:
                struct_match = re.search(pattern, content_text, re.IGNORECASE)
                if struct_match:
                    lawyer_data['structure'] = struct_match.group(1).strip()
                    break
            
            return lawyer_data
            
        except Exception as e:
            print(f"❌ Erreur extraction {lawyer_link['name']}: {e}")
            # Retourner au moins les données de base
            return {
                'prenom': lawyer_link['name'].split()[0] if lawyer_link['name'].split() else '',
                'nom': ' '.join(lawyer_link['name'].split()[1:]) if len(lawyer_link['name'].split()) > 1 else lawyer_link['name'],
                'email': '',
                'annee_inscription': '',
                'specialisations': [],
                'structure': '',
                'adresse': '',
                'telephone': '',
                'fax': '',
                'site_web': '',
                'url_source': lawyer_link['url']
            }
    
    def run_complete_extraction(self):
        """Lance l'extraction complète de tous les avocats"""
        try:
            print("🚀 === EXTRACTION COMPLÈTE BARREAU D'ARGENTAN ===")
            print(f"🕐 Démarrage: {datetime.now().strftime('%H:%M:%S')}")
            
            # Étape 1: Extraire tous les liens
            lawyer_links = self.extract_all_lawyer_links()
            
            if not lawyer_links:
                print("❌ Aucun avocat trouvé")
                return
            
            total_lawyers = len(lawyer_links)
            print(f"\n📊 {total_lawyers} avocats à traiter...")
            
            # Étape 2: Extraire les données de chaque avocat
            for i, lawyer_link in enumerate(lawyer_links):
                print(f"\n[{i+1}/{total_lawyers}] {lawyer_link['name']}")
                
                lawyer_data = self.extract_lawyer_data(lawyer_link)
                
                if lawyer_data:
                    self.lawyers_data.append(lawyer_data)
                    
                    # Affichage des infos trouvées
                    info_found = []
                    if lawyer_data['email']:
                        info_found.append(f"📧 {lawyer_data['email']}")
                    if lawyer_data['telephone']:
                        info_found.append(f"📞 {lawyer_data['telephone']}")
                    if lawyer_data['site_web']:
                        info_found.append(f"🌐 {lawyer_data['site_web']}")
                    if lawyer_data['annee_inscription']:
                        info_found.append(f"📅 {lawyer_data['annee_inscription']}")
                    
                    if info_found:
                        print(f"    {' | '.join(info_found)}")
                    else:
                        print("    ⚠️ Informations limitées")
                else:
                    print("    ❌ Échec extraction")
                
                # Délai entre les requêtes pour éviter la surcharge
                if i < total_lawyers - 1:
                    self.human_delay(1, 3)
                
                # Progression
                if (i + 1) % 5 == 0:
                    print(f"\n📈 Progression: {i+1}/{total_lawyers} ({(i+1)/total_lawyers*100:.1f}%)")
            
            # Étape 3: Sauvegarder les résultats
            self.save_complete_results()
            
        except Exception as e:
            print(f"❌ Erreur fatale: {e}")
            # Sauvegarder ce qu'on a même en cas d'erreur
            if self.lawyers_data:
                self.save_complete_results()
        
        finally:
            print("\n🔧 Fermeture du navigateur...")
            self.driver.quit()
    
    def save_complete_results(self):
        """Sauvegarde complète avec statistiques"""
        if not self.lawyers_data:
            print("⚠️ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON complet
        json_file = f'/Users/paularnould/argentan_COMPLET_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, indent=2, ensure_ascii=False)
        
        # CSV pour Excel
        csv_file = f'/Users/paularnould/argentan_COMPLET_{timestamp}.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['prenom', 'nom', 'email', 'telephone', 'fax', 'site_web', 
                         'annee_inscription', 'specialisations', 'structure', 'adresse', 'url_source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for lawyer in self.lawyers_data:
                lawyer_copy = lawyer.copy()
                lawyer_copy['specialisations'] = '; '.join(lawyer['specialisations']) if lawyer['specialisations'] else ''
                writer.writerow(lawyer_copy)
        
        # Fichier emails uniquement
        emails_file = f'/Users/paularnould/argentan_EMAILS_ONLY_{timestamp}.txt'
        with open(emails_file, 'w', encoding='utf-8') as f:
            emails = [l['email'] for l in self.lawyers_data if l['email']]
            f.write('\n'.join(emails))
        
        # Rapport détaillé
        report_file = f'/Users/paularnould/argentan_RAPPORT_COMPLET_{timestamp}.txt'
        self.generate_detailed_report(report_file, timestamp)
        
        # Affichage final
        print(f"\n🎉 ===== EXTRACTION TERMINÉE AVEC SUCCÈS =====")
        print(f"📁 Fichiers générés:")
        print(f"   • Données complètes (JSON): argentan_COMPLET_{timestamp}.json")
        print(f"   • Données complètes (CSV): argentan_COMPLET_{timestamp}.csv") 
        print(f"   • Emails uniquement: argentan_EMAILS_ONLY_{timestamp}.txt")
        print(f"   • Rapport détaillé: argentan_RAPPORT_COMPLET_{timestamp}.txt")
        print(f"\n📊 STATISTIQUES:")
        print(f"   • Total avocats extraits: {len(self.lawyers_data)}")
        
        with_email = len([l for l in self.lawyers_data if l['email']])
        with_phone = len([l for l in self.lawyers_data if l['telephone']])
        with_web = len([l for l in self.lawyers_data if l['site_web']])
        
        print(f"   • Avec email: {with_email} ({with_email/len(self.lawyers_data)*100:.1f}%)")
        print(f"   • Avec téléphone: {with_phone} ({with_phone/len(self.lawyers_data)*100:.1f}%)")
        print(f"   • Avec site web: {with_web} ({with_web/len(self.lawyers_data)*100:.1f}%)")
        print(f"\n✨ Extraction réalisée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    
    def generate_detailed_report(self, report_file, timestamp):
        """Génère un rapport détaillé"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RAPPORT D'EXTRACTION COMPLET - BARREAU D'ARGENTAN\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Date et heure d'extraction: {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
            f.write(f"Nombre total d'avocats extraits: {len(self.lawyers_data)}\n")
            f.write(f"Source: {self.base_url}\n\n")
            
            # Statistiques détaillées
            with_email = [l for l in self.lawyers_data if l['email']]
            with_phone = [l for l in self.lawyers_data if l['telephone']]
            with_web = [l for l in self.lawyers_data if l['site_web']]
            with_year = [l for l in self.lawyers_data if l['annee_inscription']]
            with_specs = [l for l in self.lawyers_data if l['specialisations']]
            
            f.write("STATISTIQUES DE QUALITÉ DES DONNÉES:\n")
            f.write("-" * 40 + "\n")
            f.write(f"• Avocats avec email: {len(with_email)} ({len(with_email)/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"• Avocats avec téléphone: {len(with_phone)} ({len(with_phone)/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"• Avocats avec site web: {len(with_web)} ({len(with_web)/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"• Avocats avec année d'inscription: {len(with_year)} ({len(with_year)/len(self.lawyers_data)*100:.1f}%)\n")
            f.write(f"• Avocats avec spécialisations: {len(with_specs)} ({len(with_specs)/len(self.lawyers_data)*100:.1f}%)\n\n")
            
            # Liste complète
            f.write("LISTE COMPLÈTE DES AVOCATS:\n")
            f.write("=" * 30 + "\n")
            
            for i, lawyer in enumerate(self.lawyers_data, 1):
                f.write(f"{i:2d}. {lawyer['prenom']} {lawyer['nom']}\n")
                if lawyer['email']:
                    f.write(f"    📧 {lawyer['email']}\n")
                if lawyer['telephone']:
                    f.write(f"    📞 {lawyer['telephone']}\n")
                if lawyer['fax']:
                    f.write(f"    📠 {lawyer['fax']}\n")
                if lawyer['site_web']:
                    f.write(f"    🌐 {lawyer['site_web']}\n")
                if lawyer['annee_inscription']:
                    f.write(f"    📅 Inscrit en {lawyer['annee_inscription']}\n")
                if lawyer['adresse']:
                    f.write(f"    📍 {lawyer['adresse']}\n")
                if lawyer['structure']:
                    f.write(f"    🏢 {lawyer['structure']}\n")
                if lawyer['specialisations']:
                    f.write(f"    🎯 {', '.join(lawyer['specialisations'])}\n")
                f.write("\n")

def main():
    """Fonction principale"""
    print("⚡ SCRAPER PRODUCTION ARGENTAN ⚡")
    print("🎯 Extraction de TOUS les avocats du barreau d'Argentan")
    print("🔒 Mode headless activé (pas de fenêtre visible)")
    print("-" * 60)
    
    scraper = ArgentanScraperProduction(headless=True)
    scraper.run_complete_extraction()

if __name__ == "__main__":
    main()