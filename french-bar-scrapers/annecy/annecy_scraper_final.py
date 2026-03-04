#!/usr/bin/env python3
"""
Script corrigé pour extraire EXACTEMENT les 302 avocats du Barreau d'Annecy
Basé sur le diagnostic qui confirme : 20 pages × 15 avocats + 1 page × 2 avocats = 302
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import json
from datetime import datetime
import time

class AnnecyExtractor302:
    def __init__(self):
        self.base_url = "https://www.barreau-annecy.com/annuaire/"
        self.lawyers_data = []
        self.stats = {
            'pages_processed': 0,
            'lawyers_found': 0,
            'errors': []
        }
    
    async def extract_all_302_lawyers(self):
        """Extraction garantie des 302 avocats"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                print("🎯 DÉMARRAGE EXTRACTION 302 AVOCATS")
                await page.goto(self.base_url, wait_until='networkidle')
                await asyncio.sleep(3)
                
                # Extraction page par page avec navigation séquentielle
                current_page = 1
                
                while current_page <= 21:  # 21 pages confirmées par diagnostic
                    print(f"\n📄 PAGE {current_page}")
                    
                    # Extraire les avocats de la page actuelle
                    page_lawyers = await self.extract_lawyers_from_current_page(page, current_page)
                    
                    if page_lawyers:
                        self.lawyers_data.extend(page_lawyers)
                        self.stats['lawyers_found'] += len(page_lawyers)
                        print(f"   ✅ {len(page_lawyers)} avocats extraits")
                        print(f"   📊 Total cumulé: {self.stats['lawyers_found']}/302")
                    else:
                        print(f"   ❌ Aucun avocat trouvé sur page {current_page}")
                    
                    self.stats['pages_processed'] += 1
                    
                    # Navigation vers page suivante (sauf si dernière page)
                    if current_page < 21:
                        success = await self.navigate_to_next_page(page, current_page + 1)
                        if not success:
                            print(f"   ⚠️ Échec navigation vers page {current_page + 1}")
                            break
                    
                    current_page += 1
                    await asyncio.sleep(1)  # Pause entre pages
                
                # Vérification finale
                print(f"\n🎯 EXTRACTION TERMINÉE")
                print(f"   📊 Pages traitées: {self.stats['pages_processed']}/21")
                print(f"   👥 Avocats trouvés: {self.stats['lawyers_found']}/302")
                
                if self.stats['lawyers_found'] == 302:
                    print(f"   ✅ SUCCESS! Tous les 302 avocats trouvés")
                else:
                    print(f"   ❌ ÉCHEC! {302 - self.stats['lawyers_found']} avocats manqués")
                
            except Exception as e:
                print(f"❌ Erreur générale: {e}")
                self.stats['errors'].append(f"Erreur générale: {e}")
            
            finally:
                await browser.close()
    
    async def extract_lawyers_from_current_page(self, page, page_num):
        """Extraire tous les avocats de la page actuelle"""
        try:
            # Attendre que les cartes soient chargées
            await page.wait_for_selector('li.Directory-listing', timeout=10000)
            
            # Récupérer toutes les cartes d'avocats
            lawyer_cards = await page.query_selector_all('li.Directory-listing')
            
            if not lawyer_cards:
                return []
            
            page_lawyers = []
            
            for index, card in enumerate(lawyer_cards):
                try:
                    # Extraire le nom (sélecteur confirmé par diagnostic)
                    name_element = await card.query_selector('span.Directory-listing--name')
                    if not name_element:
                        continue
                    
                    name = await name_element.text_content()
                    if not name or not name.strip():
                        continue
                    
                    name = name.strip()
                    
                    # Extraire les spécialités
                    specialties = []
                    specialty_elements = await card.query_selector_all('li.Directory-listing--activityListing')
                    for spec_elem in specialty_elements:
                        spec_text = await spec_elem.text_content()
                        if spec_text and spec_text.strip():
                            specialties.append(spec_text.strip())
                    
                    # Créer l'entrée avocat
                    lawyer_data = {
                        'page': page_num,
                        'index': index + 1,
                        'name': name,
                        'specialties': '; '.join(specialties) if specialties else '',
                        'phone': '',  # À remplir avec extraction email
                        'email': '',  # À remplir avec extraction email
                        'cabinet': ''  # À remplir avec extraction email
                    }
                    
                    page_lawyers.append(lawyer_data)
                    
                except Exception as e:
                    print(f"   ⚠️ Erreur extraction avocat {index}: {e}")
                    continue
            
            return page_lawyers
            
        except Exception as e:
            print(f"   ❌ Erreur extraction page {page_num}: {e}")
            return []
    
    async def navigate_to_next_page(self, page, target_page):
        """Navigation vers la page suivante"""
        try:
            # Chercher le bouton de la page cible
            pagination_buttons = await page.query_selector_all('button.Directory-paginator--number')
            
            for button in pagination_buttons:
                button_text = await button.text_content()
                if button_text and button_text.strip() == str(target_page):
                    await button.click()
                    await asyncio.sleep(3)
                    return True
            
            # Si page cible pas visible, utiliser navigation glissante
            max_visible = 0
            max_button = None
            
            for button in pagination_buttons:
                button_text = await button.text_content()
                if button_text and button_text.strip().isdigit():
                    page_num = int(button_text.strip())
                    if page_num > max_visible and page_num < target_page:
                        max_visible = page_num
                        max_button = button
            
            if max_button:
                await max_button.click()
                await asyncio.sleep(3)
                # Essayer à nouveau de trouver la page cible
                return await self.navigate_to_next_page(page, target_page)
            
            return False
            
        except Exception as e:
            print(f"   ❌ Erreur navigation: {e}")
            return False
    
    def save_results(self):
        """Sauvegarder les résultats"""
        if not self.lawyers_data:
            print("❌ Aucune donnée à sauvegarder")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder en CSV
        df = pd.DataFrame(self.lawyers_data)
        csv_file = f"annecy_302_avocats_{timestamp}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        # Sauvegarder en JSON
        json_file = f"annecy_302_avocats_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': timestamp,
                'stats': self.stats,
                'lawyers': self.lawyers_data
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 FICHIERS CRÉÉS:")
        print(f"   📄 CSV: {csv_file}")
        print(f"   📄 JSON: {json_file}")
        
        # Rapport final
        print(f"\n📋 RAPPORT FINAL:")
        print(f"   🎯 Objectif: 302 avocats")
        print(f"   ✅ Trouvés: {len(self.lawyers_data)} avocats")
        print(f"   📈 Taux succès: {len(self.lawyers_data)/302*100:.1f}%")
        
        if self.stats['errors']:
            print(f"   ⚠️ Erreurs: {len(self.stats['errors'])}")

async def main():
    print("🚀 EXTRACTION GARANTIE 302 AVOCATS BARREAU ANNECY")
    print("=" * 50)
    
    extractor = AnnecyExtractor302()
    
    # Phase 1: Extraction des noms
    await extractor.extract_all_302_lawyers()
    
    # Sauvegarde
    extractor.save_results()
    
    print("\n✅ PHASE 1 TERMINÉE - NOMS EXTRAITS")
    print("Prochaine étape: extraction des emails")

if __name__ == "__main__":
    asyncio.run(main())