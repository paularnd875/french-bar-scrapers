#!/usr/bin/env python3
"""
Script de scraping pour extraire les informations des avocats du barreau de Besançon
Utilise Playwright pour gérer le JavaScript et la navigation dynamique
"""

import asyncio
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, TimeoutError


class BesanconLawyerScraper:
    """Scraper pour les avocats du barreau de Besançon"""
    
    BASE_URL = "https://www.barreau-besancon-avocat.com"
    SEARCH_URL = f"{BASE_URL}/trouver-un-avocat/lannuaire-des-avocats.htm"
    
    def __init__(self):
        self.lawyers_data: List[Dict] = []
        self.visited_urls = set()
        
    async def accept_cookies(self, page: Page) -> None:
        """Accepte les cookies si la bannière est présente"""
        print("Vérification de la bannière de cookies...")
        cookie_selectors = [
            'text="Tout accepter"',
            'text="Accepter tous les cookies"', 
            'text="Accepter"',
            '.bandeauCookies__btn[onclick*="acceptAll(true)"]',
            'a[onclick*="acceptAll(true)"]',
            '#bandeauCookies-v2 a[onclick*="acceptAll(true)"]',
            'a[title*="Accepter"]',
            'button:has-text("Accepter")',
            '.cookie-accept',
            '.accept-cookies'
        ]
        
        for selector in cookie_selectors:
            try:
                cookie_button = await page.wait_for_selector(selector, timeout=2000)
                if cookie_button:
                    print(f"Acceptation des cookies avec: {selector}")
                    await cookie_button.click()
                    await page.wait_for_timeout(2000)
                    return
            except:
                continue
        
        # Dernière tentative: suppression forcée de la bannière
        try:
            print("Suppression forcée de la bannière cookies...")
            await page.evaluate('document.getElementById("bandeauCookies-v2")?.remove()')
            await page.wait_for_timeout(1000)
        except:
            pass
    
    async def select_besancon(self, page: Page) -> None:
        """Sélectionne Besançon dans le dropdown de ville"""
        print("Sélection de Besançon...")
        
        try:
            # Attendre que le select2 soit initialisé
            await page.wait_for_selector('.select2-container', timeout=10000)
            print("Select2 détecté")
            
            # Cliquer sur le conteneur Select2 pour l'ouvrir
            select2_selector = '.select2-container'
            await page.click(select2_selector)
            await page.wait_for_timeout(500)
            print("Select2 ouvert")
            
            # Attendre que les options soient visibles et chercher Besançon
            try:
                # Attendre les résultats Select2
                await page.wait_for_selector('.select2-results', timeout=5000)
                
                # Chercher l'option Besançon
                besancon_option = await page.wait_for_selector('text=Besançon', timeout=3000)
                await besancon_option.click()
                print("Besançon sélectionné via Select2")
            except:
                # Alternative : chercher dans toutes les options disponibles
                options = await page.query_selector_all('.select2-results li')
                for option in options:
                    text = await option.text_content()
                    if 'besançon' in text.lower():
                        await option.click()
                        print(f"Besançon sélectionné: {text}")
                        break
        except:
            print("Erreur avec Select2, tentative avec select classique...")
            # Fallback : essayer avec un select standard
            try:
                await page.select_option('#frmAnnuaire_ville_content1649', label='Besançon')
                print("Besançon sélectionné via select standard")
            except:
                print("Impossible de sélectionner Besançon, continuons sans...")
        
        await page.wait_for_timeout(1000)
    
    async def submit_search(self, page: Page) -> None:
        """Soumet le formulaire de recherche"""
        print("Recherche en cours...")
        
        # D'abord, essayer de trouver et cliquer sur le bouton de recherche
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]', 
            'input[value*="Rechercher"]',
            'input[value*="Valider"]',
            'button:has-text("Rechercher")',
            'button:has-text("Valider")',
            '.btn-submit',
            '.btn-rechercher',
            '.submit-btn',
            'form button',
            'form input[type="submit"]'
        ]
        
        button_found = False
        for selector in submit_selectors:
            try:
                submit_btn = await page.wait_for_selector(selector, timeout=3000)
                if submit_btn:
                    print(f"Bouton trouvé avec sélecteur: {selector}")
                    # Vérifier que le bouton est visible et cliquable
                    is_visible = await submit_btn.is_visible()
                    if is_visible:
                        await submit_btn.click()
                        print(f"Formulaire soumis avec: {selector}")
                        button_found = True
                        break
            except Exception as e:
                print(f"Erreur avec {selector}: {e}")
                continue
        
        if not button_found:
            print("Aucun bouton de soumission trouvé, tentative d'envoi par Enter...")
            try:
                # Essayer d'envoyer Enter sur le formulaire
                await page.keyboard.press('Enter')
                button_found = True
            except:
                pass
        
        if not button_found:
            print("⚠️  Impossible de soumettre le formulaire, continuons...")
        
        # Attendre le chargement des résultats
        print("Attente du chargement des résultats...")
        await page.wait_for_timeout(5000)
        
        # Vérifier si on a des résultats ou si on doit attendre un chargement AJAX
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
        
        # Debug: afficher l'URL actuelle
        current_url = page.url
        print(f"URL après soumission: {current_url}")
        
        # Prendre une capture d'écran pour debug
        await page.screenshot(path='after_submit.png')
        print("Capture d'écran sauvée: after_submit.png")
    
    async def extract_lawyer_cards(self, page: Page) -> List[Dict]:
        """Extrait les cartes d'avocats de la page actuelle"""
        lawyers = []
        
        # Sélecteurs possibles pour les cartes d'avocats
        card_selectors = [
            '.avocat-card',
            '.lawyer-item',
            '.fiche-avocat',
            '.result-item',
            '.annuaire-item',
            '[class*="avocat"]',
            '[class*="lawyer"]',
            '.list-group-item',
            '.card',
            'article'
        ]
        
        cards = None
        used_selector = None
        
        for selector in card_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    # Vérifier que ce sont bien des cartes d'avocats
                    first_text = await elements[0].text_content()
                    if first_text and len(first_text) > 20:  # Contient probablement des infos
                        cards = elements
                        used_selector = selector
                        print(f"Trouvé {len(cards)} cartes avec le sélecteur: {selector}")
                        break
            except:
                continue
        
        if not cards:
            print("Aucune carte d'avocat trouvée, analyse de la structure de la page...")
            # Tentative alternative: chercher des patterns de texte
            all_links = await page.query_selector_all('a[href*="avocat"]')
            print(f"Trouvé {len(all_links)} liens contenant 'avocat'")
            
            # Debug: afficher les premiers liens trouvés
            for i, link in enumerate(all_links[:5]):
                href = await link.get_attribute('href')
                text = await link.text_content()
                print(f"  Lien {i+1}: {text[:50]}... -> {href}")
            
            for link in all_links:
                href = await link.get_attribute('href')
                text = await link.text_content()
                if text and href:
                    # Critères plus permissifs pour les fiches d'avocats
                    text_clean = text.strip()
                    if (text_clean and 
                        len(text_clean) > 5 and 
                        'ordre des avocats' not in text_clean.lower() and
                        'barreau' not in text_clean.lower() and
                        'trouver un avocat' not in text_clean.lower()):
                        
                        lawyers.append({
                            'nom': text_clean,
                            'url_profil': urljoin(self.BASE_URL, href)
                        })
                        print(f"Avocat ajouté: {text_clean}")
        else:
            # Extraire les informations de chaque carte
            for i, card in enumerate(cards):
                lawyer_info = await self.extract_lawyer_info(card, page)
                if lawyer_info:
                    lawyers.append(lawyer_info)
                    print(f"Avocat {i+1}/{len(cards)}: {lawyer_info.get('nom', 'N/A')}")
        
        return lawyers
    
    async def extract_lawyer_info(self, element, page: Page) -> Optional[Dict]:
        """Extrait les informations d'un élément avocat"""
        info = {}
        
        try:
            # Extraire le texte complet
            full_text = await element.text_content()
            if not full_text:
                return None
            
            # Nom - généralement en gras ou dans un heading
            name_selectors = ['h2', 'h3', 'h4', 'strong', 'b', '.name', '.nom']
            for selector in name_selectors:
                try:
                    name_elem = await element.query_selector(selector)
                    if name_elem:
                        info['nom'] = (await name_elem.text_content()).strip()
                        break
                except:
                    pass
            
            # Si pas de nom trouvé, prendre la première ligne
            if 'nom' not in info:
                lines = full_text.strip().split('\n')
                if lines:
                    info['nom'] = lines[0].strip()
            
            # Téléphone
            phone_match = re.search(r'(?:Tél|Tel|Téléphone|📞|☎)?[:\s]*?([\d\s\.\-\(\)]+)', full_text)
            if phone_match:
                phone = re.sub(r'[^\d]', '', phone_match.group(1))
                if len(phone) >= 10:
                    info['telephone'] = phone
            
            # Email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
            if email_match:
                info['email'] = email_match.group(0)
            
            # Adresse
            address_patterns = [
                r'\d+.*rue.*',
                r'\d+.*avenue.*',
                r'\d+.*boulevard.*',
                r'\d+.*place.*',
                r'\d+.*cours.*'
            ]
            for pattern in address_patterns:
                address_match = re.search(pattern, full_text, re.IGNORECASE)
                if address_match:
                    info['adresse'] = address_match.group(0).strip()
                    break
            
            # Lien vers le profil
            profile_link = await element.query_selector('a[href*="avocat"]')
            if profile_link:
                href = await profile_link.get_attribute('href')
                if href:
                    info['url_profil'] = urljoin(self.BASE_URL, href)
            
            # Spécialités
            if 'spécialit' in full_text.lower() or 'domaine' in full_text.lower():
                spec_match = re.search(r'(?:Spécialité|Domaine)[s]?\s*:?\s*(.+?)(?:\n|$)', full_text, re.IGNORECASE)
                if spec_match:
                    info['specialites'] = spec_match.group(1).strip()
            
            return info if info else None
            
        except Exception as e:
            print(f"Erreur lors de l'extraction: {e}")
            return None
    
    async def scrape_lawyer_profile(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape une page de profil individuel d'avocat"""
        if url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            print(f"Visite du profil: {url}")
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(1000)
            
            info = {'url_profil': url}
            
            # Sélecteurs pour les informations du profil
            selectors = {
                'nom': ['h1', '.lawyer-name', '.nom-avocat', '#nom'],
                'prenom': ['.prenom', '#prenom'],
                'telephone': ['.tel', '.telephone', '[href^="tel:"]'],
                'email': ['.email', '[href^="mailto:"]'],
                'adresse': ['.adresse', '.address', '.lieu'],
                'specialites': ['.specialites', '.domaines', '.competences']
            }
            
            for field, field_selectors in selectors.items():
                for selector in field_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            text = await elem.text_content()
                            if text:
                                info[field] = text.strip()
                                break
                    except:
                        continue
            
            # Extraction alternative par analyse du texte complet
            full_text = await page.content()
            
            if 'telephone' not in info:
                phone_match = re.search(r'(?:0[\d\s\.\-]{9,})', full_text)
                if phone_match:
                    info['telephone'] = re.sub(r'[^\d]', '', phone_match.group(0))
            
            if 'email' not in info:
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', full_text)
                if email_match:
                    info['email'] = email_match.group(0)
            
            return info if len(info) > 1 else None
            
        except Exception as e:
            print(f"Erreur lors du scraping du profil {url}: {e}")
            return None
    
    async def handle_pagination(self, page: Page) -> bool:
        """Gère la pagination et retourne True s'il y a une page suivante"""
        print("Recherche de la pagination...")
        
        # Sélecteurs de pagination possibles
        next_selectors = [
            'a:has-text("Suivant")',
            'a:has-text("Next")',
            'a:has-text("»")',
            'a:has-text(">")',
            '.pagination .next',
            '.pagination-next',
            'a[rel="next"]',
            '.page-next'
        ]
        
        for selector in next_selectors:
            try:
                next_btn = await page.query_selector(selector)
                if next_btn:
                    is_disabled = await next_btn.get_attribute('disabled')
                    class_attr = await next_btn.get_attribute('class')
                    
                    if not is_disabled and (not class_attr or 'disabled' not in class_attr):
                        print(f"Page suivante trouvée avec: {selector}")
                        await next_btn.click()
                        await page.wait_for_timeout(2000)
                        await page.wait_for_load_state('networkidle')
                        return True
            except:
                continue
        
        # Méthode alternative: chercher les numéros de page
        try:
            page_numbers = await page.query_selector_all('.pagination a[href*="page"], .page-link')
            current_page = await page.query_selector('.pagination .active, .page-item.active')
            
            if current_page and page_numbers:
                current_text = await current_page.text_content()
                current_num = int(re.search(r'\d+', current_text).group()) if current_text else 1
                
                for page_link in page_numbers:
                    link_text = await page_link.text_content()
                    if link_text and link_text.isdigit():
                        page_num = int(link_text)
                        if page_num == current_num + 1:
                            print(f"Navigation vers la page {page_num}")
                            await page_link.click()
                            await page.wait_for_timeout(2000)
                            await page.wait_for_load_state('networkidle')
                            return True
        except:
            pass
        
        print("Pas de page suivante trouvée")
        return False
    
    async def scrape(self):
        """Fonction principale de scraping"""
        async with async_playwright() as p:
            # Lancer le navigateur avec interface graphique pour debug
            browser = await p.chromium.launch(
                headless=False,  # Mode visible pour debug
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # 1. Accéder à la page de recherche
                print(f"Accès à {self.SEARCH_URL}")
                await page.goto(self.SEARCH_URL, wait_until='networkidle')
                await page.wait_for_timeout(2000)
                
                # 2. Accepter les cookies
                await self.accept_cookies(page)
                
                # 3. Sélectionner Besançon
                await self.select_besancon(page)
                
                # 4. Soumettre la recherche
                await self.submit_search(page)
                
                # 5. Scraper toutes les pages de résultats
                page_num = 1
                while True:
                    print(f"\n--- Page {page_num} ---")
                    
                    # Extraire les avocats de la page actuelle
                    lawyers = await self.extract_lawyer_cards(page)
                    
                    # Si on a des URLs de profil, les visiter
                    for lawyer in lawyers:
                        if 'url_profil' in lawyer and lawyer['url_profil']:
                            profile_data = await self.scrape_lawyer_profile(page, lawyer['url_profil'])
                            if profile_data:
                                # Fusionner les données
                                lawyer.update(profile_data)
                    
                    self.lawyers_data.extend(lawyers)
                    print(f"Total d'avocats récupérés: {len(self.lawyers_data)}")
                    
                    # Passer à la page suivante
                    has_next = await self.handle_pagination(page)
                    if not has_next:
                        break
                    
                    page_num += 1
                    
                    # Limiter à 10 pages pour éviter les boucles infinies
                    if page_num > 10:
                        print("Limite de 10 pages atteinte")
                        break
                
                # 6. Sauvegarder les résultats
                await self.save_results()
                
            except Exception as e:
                print(f"Erreur lors du scraping: {e}")
                # Prendre une capture d'écran pour debug
                await page.screenshot(path='error_screenshot.png')
                raise
            
            finally:
                await browser.close()
    
    async def save_results(self):
        """Sauvegarde les résultats en CSV et JSON"""
        if not self.lawyers_data:
            print("Aucune donnée à sauvegarder")
            return
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f'avocats_besancon_{timestamp}.csv'
        json_filename = f'avocats_besancon_{timestamp}.json'
        
        # Sauvegarder en CSV
        if self.lawyers_data:
            keys = set()
            for lawyer in self.lawyers_data:
                keys.update(lawyer.keys())
            
            with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=sorted(keys))
                writer.writeheader()
                writer.writerows(self.lawyers_data)
            
            print(f"Données sauvegardées dans {csv_filename}")
        
        # Sauvegarder aussi en JSON pour backup
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.lawyers_data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"Backup JSON sauvegardé dans {json_filename}")
        print(f"Total: {len(self.lawyers_data)} avocats extraits")
        
        # Afficher un résumé
        print("\nRésumé des données extraites:")
        for i, lawyer in enumerate(self.lawyers_data[:5], 1):
            print(f"\n{i}. {lawyer.get('nom', 'N/A')}")
            for key, value in lawyer.items():
                if key != 'nom' and value:
                    print(f"   {key}: {value}")


async def main():
    """Point d'entrée principal"""
    print("=== Scraper des avocats du barreau de Besançon ===\n")
    
    scraper = BesanconLawyerScraper()
    await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())