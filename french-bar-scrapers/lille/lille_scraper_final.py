#!/usr/bin/env python3
"""
Script de scraping pour l'annuaire des avocats du barreau de Lille
Version finale avec gestion des filtres pour contourner la limite de 30 résultats
"""

import asyncio
import csv
import json
from playwright.async_api import async_playwright
import time
from urllib.parse import urljoin

class LilleLawyersScraper:
    def __init__(self):
        self.base_url = "https://www.avocats-lille.com/fr/annuaire/tableau/"
        self.all_lawyers = []
        
    async def get_available_filters(self, page):
        """Récupérer tous les filtres disponibles"""
        filters = {
            'specializations': [],
            'languages': [],
            'cities': []
        }
        
        try:
            # Attendre que la page soit chargée
            await page.wait_for_selector('select[name="competences"]', timeout=10000)
            
            # Récupérer les spécialisations
            specializations = await page.query_selector_all('select[name="competences"] option')
            for spec in specializations:
                value = await spec.get_attribute('value')
                text = await spec.text_content()
                if value and value.strip():
                    filters['specializations'].append({'value': value.strip(), 'text': text.strip()})
            
            # Récupérer les langues
            languages = await page.query_selector_all('select[name="langue"] option')
            for lang in languages:
                value = await lang.get_attribute('value')
                text = await lang.text_content()
                if value and value.strip():
                    filters['languages'].append({'value': value.strip(), 'text': text.strip()})
            
            # Récupérer les villes
            cities = await page.query_selector_all('select[name="ville"] option')
            for city in cities:
                value = await city.get_attribute('value')
                text = await city.text_content()
                if value and value.strip():
                    filters['cities'].append({'value': value.strip(), 'text': text.strip()})
                    
            print(f"✅ Filtres récupérés: {len(filters['specializations'])} spécialisations, {len(filters['languages'])} langues, {len(filters['cities'])} villes")
            return filters
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des filtres: {e}")
            return filters
    
    async def extract_lawyer_data(self, page):
        """Extraire les données des avocats de la page actuelle"""
        lawyers = []
        
        try:
            # Attendre que les résultats se chargent
            await page.wait_for_selector('.annuaire-header', timeout=10000)
            
            # Récupérer toutes les fiches d'avocats
            lawyer_cards = await page.query_selector_all('.annuaire-header')
            
            print(f"📊 {len(lawyer_cards)} avocats trouvés sur cette page")
            
            for card in lawyer_cards:
                lawyer_info = {}
                
                try:
                    # Nom complet depuis le titre
                    name_element = await card.query_selector('.annuaire-header__title h2')
                    if name_element:
                        full_name = await name_element.text_content()
                        lawyer_info['nom_complet'] = full_name.strip() if full_name else ""
                        
                        # Séparer nom et prénom
                        if full_name and full_name.strip():
                            parts = full_name.strip().split()
                            if len(parts) >= 2:
                                lawyer_info['nom'] = parts[0]  # Le nom de famille est généralement en premier (MAJUSCULES)
                                lawyer_info['prenom'] = ' '.join(parts[1:])  # Le prénom suit
                            else:
                                lawyer_info['nom'] = full_name.strip()
                                lawyer_info['prenom'] = ""
                    
                    # Date d'inscription au barreau (serment)
                    contact_div = await card.query_selector('.annuaire-header__contact')
                    if contact_div:
                        spans = await contact_div.query_selector_all('span')
                        for span in spans:
                            text = await span.text_content()
                            if text and 'Serment' in text:
                                lawyer_info['date_serment'] = text.strip()
                                break
                    
                    # Email
                    email_element = await card.query_selector('a[href^="mailto:"]')
                    if email_element:
                        email = await email_element.text_content()
                        if email and ':' in email:
                            lawyer_info['email'] = email.split(':')[-1].strip()
                    
                    # Téléphone
                    phone_element = await card.query_selector('a[href^="tel:"]')
                    if phone_element:
                        phone_text = await phone_element.text_content()
                        if phone_text and ':' in phone_text:
                            lawyer_info['telephone'] = phone_text.split(':')[-1].strip()
                    
                    # Spécialisations
                    competences_ul = await card.query_selector('.annuaire-header__competences ul')
                    if competences_ul:
                        competence_items = await competences_ul.query_selector_all('li h3')
                        competences = []
                        for item in competence_items:
                            text = await item.text_content()
                            if text:
                                competences.append(text.strip())
                        lawyer_info['specialisations'] = '; '.join(competences)
                    
                    # Récupérer les détails complémentaires (adresse, site web, etc.)
                    # Il faut cliquer sur le bouton "+" pour voir plus de détails
                    try:
                        plus_button = await card.query_selector('.see-more')
                        if plus_button:
                            await plus_button.click()
                            await page.wait_for_timeout(500)
                            
                            # Chercher dans la zone de détails qui s'ouvre
                            detail_id = await plus_button.get_attribute('data-target')
                            if detail_id:
                                detail_div = await page.query_selector(f'#{detail_id}')
                                if detail_div:
                                    # Adresse
                                    address_parts = []
                                    address_elements = await detail_div.query_selector_all('p, div')
                                    for elem in address_elements:
                                        text = await elem.text_content()
                                        if text and text.strip():
                                            clean_text = text.strip()
                                            # Filtrer les emails, téléphones et sites web déjà récupérés
                                            if not any(keyword in clean_text.lower() for keyword in ['email', 'tel', 'fax', 'site web', 'http']):
                                                if len(clean_text) > 3 and not clean_text.startswith('0'):
                                                    address_parts.append(clean_text)
                                    
                                    if address_parts:
                                        lawyer_info['adresse'] = address_parts[0]
                                    
                                    # Site web
                                    site_link = await detail_div.query_selector('a[href^="http"]')
                                    if site_link:
                                        site_url = await site_link.get_attribute('href')
                                        lawyer_info['site_web'] = site_url
                                    
                                    # Fermer les détails
                                    await plus_button.click()
                                    await page.wait_for_timeout(300)
                    except:
                        pass  # En cas d'erreur, on continue sans les détails
                    
                    # Ne garder que les avocats avec au moins un nom
                    if lawyer_info.get('nom_complet'):
                        lawyers.append(lawyer_info)
                    
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'extraction d'un avocat: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction des avocats: {e}")
        
        return lawyers
    
    async def check_for_too_many_results(self, page):
        """Vérifier s'il y a plus de 30 résultats"""
        try:
            # Chercher le message "Plus de 30 résultats"
            too_many_elements = await page.query_selector_all('text="Plus de 30 résultats"')
            if too_many_elements:
                return True
            
            # Alternative: chercher dans le contenu de la page
            content = await page.content()
            if "Plus de 30 résultats" in content:
                return True
                
            return False
        except:
            return False
    
    async def scrape_with_filter(self, page, filter_type, filter_value, filter_text):
        """Scraper avec un filtre spécifique"""
        try:
            print(f"🔍 Recherche avec filtre {filter_type}: {filter_text}")
            
            # Aller à la page de base
            await page.goto(self.base_url)
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)
            
            # Appliquer le filtre
            await page.select_option(f'select[name="{filter_type}"]', filter_value)
            await page.wait_for_timeout(1000)
            
            # Soumettre le formulaire (chercher le bouton de recherche)
            submit_button = await page.query_selector('input[type="submit"], button[type="submit"]')
            if submit_button:
                await submit_button.click()
            else:
                # Si pas de bouton, soumettre le formulaire
                form = await page.query_selector('form')
                if form:
                    await form.evaluate('form => form.submit()')
            
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
            
            # Vérifier s'il y a trop de résultats
            too_many = await self.check_for_too_many_results(page)
            if too_many:
                print(f"⚠️ Plus de 30 résultats pour le filtre {filter_text}, nécessite subdivision")
                return []
            
            # Extraire les avocats
            lawyers = await self.extract_lawyer_data(page)
            print(f"✅ {len(lawyers)} avocats extraits avec le filtre {filter_text}")
            
            return lawyers
            
        except Exception as e:
            print(f"❌ Erreur avec le filtre {filter_text}: {e}")
            return []
    
    async def scrape_all_lawyers(self):
        """Scraper tous les avocats en utilisant les filtres"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                print("🌐 Accès à la page...")
                await page.goto(self.base_url)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(3000)
                
                # Récupérer tous les filtres disponibles
                print("🔍 Récupération des filtres...")
                filters = await self.get_available_filters(page)
                
                # Sauvegarder les filtres
                with open('/Users/paularnould/lille_filters.json', 'w', encoding='utf-8') as f:
                    json.dump(filters, f, ensure_ascii=False, indent=2)
                
                # Tester d'abord sans filtre pour voir la limite
                print("📋 Test initial sans filtre...")
                initial_lawyers = await self.extract_lawyer_data(page)
                too_many_initial = await self.check_for_too_many_results(page)
                
                if too_many_initial:
                    print("⚠️ Limite de 30 résultats atteinte, utilisation des filtres...")
                    
                    # Utiliser les filtres par ville d'abord (plus spécifiques)
                    all_lawyers = []
                    processed_lawyers = set()  # Pour éviter les doublons
                    
                    # Essayer chaque ville
                    for city in filters['cities']:
                        if city['value']:  # Ignorer les valeurs vides
                            city_lawyers = await self.scrape_with_filter(page, 'ville', city['value'], city['text'])
                            
                            # Ajouter les nouveaux avocats (éviter les doublons)
                            for lawyer in city_lawyers:
                                lawyer_id = lawyer.get('nom_complet', '') + lawyer.get('email', '')
                                if lawyer_id not in processed_lawyers:
                                    processed_lawyers.add(lawyer_id)
                                    all_lawyers.append(lawyer)
                    
                    # Si certaines villes ont encore trop de résultats, les subdiviser par spécialisation
                    print(f"📊 Total après filtrage par ville: {len(all_lawyers)} avocats")
                    
                    self.all_lawyers = all_lawyers
                else:
                    print("✅ Tous les résultats récupérés sans filtres")
                    self.all_lawyers = initial_lawyers
                
                # Sauvegarder le résultat
                if self.all_lawyers:
                    self.save_to_csv(self.all_lawyers, '/Users/paularnould/lille_avocats_complet.csv')
                    print(f"🎉 Scraping terminé! {len(self.all_lawyers)} avocats extraits et sauvegardés")
                    
                    # Afficher quelques statistiques
                    emails = sum(1 for lawyer in self.all_lawyers if lawyer.get('email'))
                    telephones = sum(1 for lawyer in self.all_lawyers if lawyer.get('telephone'))
                    specialisations = sum(1 for lawyer in self.all_lawyers if lawyer.get('specialisations'))
                    
                    print(f"📊 Statistiques:")
                    print(f"   - {emails} avocats avec email")
                    print(f"   - {telephones} avocats avec téléphone")
                    print(f"   - {specialisations} avocats avec spécialisations")
                else:
                    print("❌ Aucun avocat extrait")
                
            except Exception as e:
                print(f"❌ Erreur générale: {e}")
            
            finally:
                await browser.close()
    
    def save_to_csv(self, lawyers_data, filename):
        """Sauvegarder les données en CSV"""
        if not lawyers_data:
            return
        
        # Récupérer toutes les clés possibles
        all_keys = set()
        for lawyer in lawyers_data:
            all_keys.update(lawyer.keys())
        
        # Ordre préféré des colonnes
        preferred_order = ['prenom', 'nom', 'nom_complet', 'date_serment', 'email', 'telephone', 'adresse', 'specialisations', 'site_web']
        ordered_keys = []
        
        for key in preferred_order:
            if key in all_keys:
                ordered_keys.append(key)
                all_keys.remove(key)
        
        # Ajouter les clés restantes
        ordered_keys.extend(sorted(all_keys))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=ordered_keys)
            writer.writeheader()
            for lawyer in lawyers_data:
                writer.writerow(lawyer)
        
        print(f"💾 Données sauvegardées dans {filename}")

async def main():
    scraper = LilleLawyersScraper()
    await scraper.scrape_all_lawyers()

if __name__ == "__main__":
    asyncio.run(main())