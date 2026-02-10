#!/usr/bin/env python3
"""
Scraper ultime pour le Barreau de Thonon
Utilise la bonne URL avec pagination correcte
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv
from datetime import datetime
import re

class ThononUltimateScraper:
    def __init__(self):
        self.base_url = "https://public.barreau-thonon.fr/lannuaire/"
        self.lawyers = {}
        self.setup_driver()
    
    def setup_driver(self):
        """Configuration du driver Selenium"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        options.add_experimental_option('useAutomationExtension', False)
        # Mode visible pour debug
        # options.add_argument('--headless')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def extract_lawyer_from_listing(self, listing):
        """Extrait les infos d'un avocat depuis un élément listing"""
        try:
            lawyer = {
                'name': '',
                'address': '',
                'phone': '',
                'fax': '',
                'email': '',
                'specialities': []
            }
            
            # Nom - dans le titre
            title = listing.find_elements(By.CSS_SELECTOR, '.wpbdp-field-name, .listing-title, h2')
            if title:
                lawyer['name'] = title[0].text.strip()
            
            # Adresse
            address_elem = listing.find_elements(By.CSS_SELECTOR, '.wpbdp-field-adresse, .address, .wpbdp-field-address')
            if address_elem:
                lawyer['address'] = address_elem[0].text.strip()
            
            # Téléphone
            phone_elem = listing.find_elements(By.CSS_SELECTOR, '.wpbdp-field-tel, .wpbdp-field-telephone, .phone')
            if phone_elem:
                lawyer['phone'] = phone_elem[0].text.replace('Tel:', '').strip()
            
            # Fax
            fax_elem = listing.find_elements(By.CSS_SELECTOR, '.wpbdp-field-fax')
            if fax_elem:
                lawyer['fax'] = fax_elem[0].text.replace('Fax:', '').strip()
            
            # Email - chercher les liens mailto
            email_links = listing.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
            if email_links:
                lawyer['email'] = email_links[0].get_attribute('href').replace('mailto:', '')
            
            # Spécialités
            spec_elem = listing.find_elements(By.CSS_SELECTOR, '.wpbdp-field-specialites, .specialities, .wpbdp-field-specialite')
            if spec_elem:
                lawyer['specialities'] = [s.strip() for s in spec_elem[0].text.split(',')]
            
            # Si pas de nom trouvé, utiliser le texte complet
            if not lawyer['name']:
                full_text = listing.text.strip()
                lines = full_text.split('\n')
                if lines:
                    # Première ligne non vide est probablement le nom
                    for line in lines:
                        if line.strip() and not line.startswith('Tel:') and not line.startswith('Fax:'):
                            lawyer['name'] = line.strip()
                            break
            
            return lawyer
            
        except Exception as e:
            print(f"    [!] Erreur extraction: {e}")
            return None
    
    def extract_page(self, page_num):
        """Extrait les avocats d'une page spécifique"""
        url = f"https://public.barreau-thonon.fr/lannuaire/page/{page_num}/?wpbdp_view=all_listings"
        
        print(f"\n📄 Page {page_num}")
        print(f"   URL: {url}")
        
        self.driver.get(url)
        time.sleep(2)  # Attendre le chargement
        
        # Chercher les listings
        listings = self.driver.find_elements(By.CSS_SELECTOR, '.wpbdp-listing')
        
        if not listings:
            print(f"   [x] Aucun avocat trouvé")
            return 0
        
        print(f"   [✓] {len(listings)} avocats trouvés")
        
        new_count = 0
        for listing in listings:
            lawyer = self.extract_lawyer_from_listing(listing)
            if lawyer and lawyer['name']:
                # Clé unique basée sur le nom
                key = lawyer['name'].lower().replace(' ', '_')
                if key not in self.lawyers:
                    self.lawyers[key] = lawyer
                    new_count += 1
                    print(f"      + {lawyer['name']}")
        
        print(f"   → {new_count} nouveaux avocats ajoutés")
        return new_count
    
    def find_total_pages(self):
        """Trouve le nombre total de pages"""
        print("\n🔍 Recherche du nombre total de pages...")
        
        # Aller à la première page avec all_listings
        self.driver.get("https://public.barreau-thonon.fr/lannuaire/?wpbdp_view=all_listings")
        time.sleep(2)
        
        # Chercher la pagination
        pagination = self.driver.find_elements(By.CSS_SELECTOR, '.wpbdp-pagination')
        if not pagination:
            print("   [!] Pas de pagination trouvée, une seule page ?")
            return 1
        
        # Chercher le nombre max de pages
        page_links = self.driver.find_elements(By.CSS_SELECTOR, '.wpbdp-pagination a')
        max_page = 1
        
        for link in page_links:
            href = link.get_attribute('href') or ''
            # Extraire le numéro de page de l'URL
            match = re.search(r'/page/(\d+)/', href)
            if match:
                page_num = int(match.group(1))
                if page_num > max_page:
                    max_page = page_num
            
            # Ou depuis le texte du lien
            text = link.text.strip()
            if text.isdigit():
                page_num = int(text)
                if page_num > max_page:
                    max_page = page_num
        
        # Vérifier s'il y a un lien "Dernier" ou ">>"
        last_link = self.driver.find_elements(By.CSS_SELECTOR, '.wpbdp-pagination a.last, .wpbdp-pagination a:last-child')
        if last_link:
            href = last_link[-1].get_attribute('href') or ''
            match = re.search(r'/page/(\d+)/', href)
            if match:
                max_page = int(match.group(1))
        
        print(f"   [✓] {max_page} pages détectées")
        return max_page
    
    def extract_all(self):
        """Extraction complète de tous les avocats"""
        print("=" * 60)
        print("🚀 EXTRACTION ULTIME - BARREAU DE THONON")
        print("=" * 60)
        print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Trouver le nombre total de pages
        total_pages = self.find_total_pages()
        
        # 2. Limiter à un maximum raisonnable
        max_pages_to_check = min(total_pages + 5, 30)  # Check quelques pages de plus au cas où
        
        print(f"\n📚 Extraction de {max_pages_to_check} pages...")
        
        # 3. Extraire chaque page
        pages_with_content = 0
        consecutive_empty = 0
        
        for page in range(1, max_pages_to_check + 1):
            count = self.extract_page(page)
            
            if count > 0:
                pages_with_content += 1
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                
                # Arrêter après 3 pages vides consécutives
                if consecutive_empty >= 3:
                    print(f"\n[!] Arrêt après 3 pages vides consécutives")
                    break
            
            # Petit délai pour ne pas surcharger le serveur
            time.sleep(1)
            
            # Status toutes les 5 pages
            if page % 5 == 0:
                print(f"\n📊 Status: {len(self.lawyers)} avocats uniques trouvés jusqu'à présent")
        
        # 4. Essayer aussi sans le paramètre wpbdp_view pour voir
        print("\n🔍 Test de pages alternatives...")
        
        # Pages simples
        for page in range(1, 6):
            url = f"https://public.barreau-thonon.fr/lannuaire/page/{page}/"
            print(f"\n📄 Test page simple {page}")
            print(f"   URL: {url}")
            
            self.driver.get(url)
            time.sleep(2)
            
            listings = self.driver.find_elements(By.CSS_SELECTOR, '.wpbdp-listing, article.listing, .lawyer-item')
            if listings:
                print(f"   [✓] {len(listings)} éléments trouvés")
                for listing in listings:
                    lawyer = self.extract_lawyer_from_listing(listing)
                    if lawyer and lawyer['name']:
                        key = lawyer['name'].lower().replace(' ', '_')
                        if key not in self.lawyers:
                            self.lawyers[key] = lawyer
                            print(f"      + {lawyer['name']}")
        
        print("\n" + "=" * 60)
        print("✅ EXTRACTION TERMINÉE")
        print(f"📊 TOTAL: {len(self.lawyers)} avocats uniques extraits")
        print(f"📄 Pages avec contenu: {pages_with_content}")
        print(f"⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def save_results(self):
        """Sauvegarde les résultats dans différents formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f"thonon_final_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.lawyers.values()), f, indent=2, ensure_ascii=False)
        print(f"\n📁 JSON: {json_file}")
        
        # CSV
        csv_file = f"thonon_final_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.lawyers:
                fieldnames = ['name', 'address', 'phone', 'fax', 'email', 'specialities']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in self.lawyers.values():
                    row = {k: lawyer.get(k, '') for k in fieldnames}
                    if isinstance(row['specialities'], list):
                        row['specialities'] = ', '.join(row['specialities'])
                    writer.writerow(row)
        print(f"📁 CSV: {csv_file}")
        
        # Rapport détaillé
        report_file = f"thonon_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("RAPPORT FINAL - BARREAU DE THONON\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total avocats: {len(self.lawyers)}\n")
            f.write(f"Objectif: ~160 avocats\n")
            
            if len(self.lawyers) >= 150:
                f.write("✅ OBJECTIF ATTEINT!\n\n")
            else:
                f.write(f"❌ Objectif manqué de {160 - len(self.lawyers)} avocats\n\n")
            
            # Statistiques
            with_email = sum(1 for l in self.lawyers.values() if l.get('email'))
            with_phone = sum(1 for l in self.lawyers.values() if l.get('phone'))
            with_address = sum(1 for l in self.lawyers.values() if l.get('address'))
            
            f.write("STATISTIQUES:\n")
            f.write(f"  - Avec email: {with_email} ({with_email*100//len(self.lawyers)}%)\n")
            f.write(f"  - Avec téléphone: {with_phone} ({with_phone*100//len(self.lawyers)}%)\n")
            f.write(f"  - Avec adresse: {with_address} ({with_address*100//len(self.lawyers)}%)\n\n")
            
            # Liste complète
            f.write("=" * 60 + "\n")
            f.write("LISTE COMPLÈTE DES AVOCATS:\n")
            f.write("=" * 60 + "\n\n")
            
            for i, (key, lawyer) in enumerate(self.lawyers.items(), 1):
                f.write(f"{i}. {lawyer.get('name', 'Sans nom')}\n")
                if lawyer.get('address'):
                    f.write(f"   📍 {lawyer['address']}\n")
                if lawyer.get('phone'):
                    f.write(f"   ☎️  {lawyer['phone']}\n")
                if lawyer.get('email'):
                    f.write(f"   ✉️  {lawyer['email']}\n")
                if lawyer.get('specialities'):
                    specs = ', '.join(lawyer['specialities']) if isinstance(lawyer['specialities'], list) else lawyer['specialities']
                    f.write(f"   📚 {specs}\n")
                f.write("\n")
        
        print(f"📁 Rapport: {report_file}")
    
    def close(self):
        """Ferme le navigateur"""
        self.driver.quit()

def main():
    """Fonction principale"""
    scraper = ThononUltimateScraper()
    
    try:
        # Extraction
        scraper.extract_all()
        
        # Sauvegarde
        scraper.save_results()
        
        # Résumé final
        print("\n" + "🎯" * 30)
        print(f"\n🏆 RÉSULTAT FINAL: {len(scraper.lawyers)} avocats")
        
        if len(scraper.lawyers) >= 150:
            print("✅ SUCCÈS! Objectif de ~160 avocats atteint!")
        elif len(scraper.lawyers) >= 100:
            print("⚠️ Résultat partiel - Plus de 100 avocats trouvés")
        else:
            print("❌ Résultat insuffisant - Moins de 100 avocats")
            
        print("\n💡 ANALYSE DU PROBLÈME:")
        if len(scraper.lawyers) < 160:
            print("Le site semble avoir des limitations:")
            print("1. Pagination limitée ou non fonctionnelle")
            print("2. Filtres géographiques non accessibles via URL")
            print("3. Possible nécessité d'authentification")
            print("4. Les zones Léman et Genevois peuvent être sur d'autres sites")
        
        print("\n" + "🎯" * 30)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()