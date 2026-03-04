#!/usr/bin/env python3
"""
Script pour scraper la liste des avocats du barreau de Mayotte
"""

import asyncio
import aiohttp
import PyPDF2
import pdfplumber
import fitz  # pymupdf
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import csv
import json
from playwright.async_api import async_playwright
from pathlib import Path
import io

class MayotteAvocatsScraper:
    def __init__(self):
        self.url = "https://www.cdad976.fr/liste-des-avocats-2023-barreau-de-mayotte/"
        self.pdf_url = None
        self.pdf_content = None
        self.avocats_data = []
        
    async def navigate_and_find_pdf(self):
        """Navigue sur la page et trouve le lien PDF en acceptant les cookies"""
        async with async_playwright() as p:
            # Lancer un navigateur avec des paramètres pour éviter la détection
            browser = await p.chromium.launch(
                headless=False,  # Mode visible pour déboguer
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                print(f"Navigation vers: {self.url}")
                # Essayer avec différentes stratégies de chargement
                try:
                    await page.goto(self.url, wait_until='load', timeout=60000)
                except:
                    print("Échec avec 'load', essai avec 'domcontentloaded'")
                    await page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                
                # Attendre un peu pour que la page se charge complètement
                await page.wait_for_timeout(3000)
                
                # Accepter les cookies si un bannière apparaît
                cookie_selectors = [
                    'button[id*="cookie"]',
                    'button[class*="cookie"]',
                    'button[id*="accept"]',
                    'button[class*="accept"]',
                    '.cookie-consent button',
                    '#cookie-banner button',
                    '[data-cookie] button',
                    'button:has-text("Accepter")',
                    'button:has-text("Accept")',
                    'button:has-text("J\'accepte")'
                ]
                
                for selector in cookie_selectors:
                    try:
                        cookie_btn = await page.query_selector(selector)
                        if cookie_btn:
                            print(f"Cookie banner trouvé avec: {selector}")
                            await cookie_btn.click()
                            await page.wait_for_timeout(1000)
                            break
                    except:
                        continue
                
                # Chercher tous les liens PDF possibles et iframes
                pdf_links = await page.evaluate("""
                    () => {
                        const links = [];
                        
                        // Chercher dans les liens classiques
                        document.querySelectorAll('a').forEach(link => {
                            const href = link.href || '';
                            const text = link.textContent || '';
                            if (href.toLowerCase().includes('.pdf') || 
                                text.toLowerCase().includes('pdf') ||
                                text.toLowerCase().includes('télécharger') ||
                                text.toLowerCase().includes('liste') ||
                                href.toLowerCase().includes('download')) {
                                links.push({
                                    url: href,
                                    text: text.trim(),
                                    title: link.title || '',
                                    type: 'link'
                                });
                            }
                        });
                        
                        // Chercher dans les iframes PDF
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src || '';
                            if (src.toLowerCase().includes('.pdf')) {
                                links.push({
                                    url: src.startsWith('http') ? src : window.location.origin + src,
                                    text: 'PDF depuis iframe',
                                    title: iframe.title || '',
                                    type: 'iframe'
                                });
                            }
                        });
                        
                        return links;
                    }
                """)
                
                print(f"Liens PDF trouvés: {len(pdf_links)}")
                for link in pdf_links:
                    print(f"  - {link['text']} -> {link['url']}")
                
                # Prendre le premier lien PDF trouvé
                if pdf_links:
                    self.pdf_url = pdf_links[0]['url']
                    print(f"URL PDF sélectionnée: {self.pdf_url}")
                else:
                    # Si aucun lien PDF direct, chercher dans le contenu de la page
                    content = await page.content()
                    print("Aucun lien PDF direct trouvé. Analyse du contenu...")
                    
                    # Sauvegarder le contenu HTML pour inspection
                    with open('/Users/paularnould/mayotte_page_content.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("Contenu de la page sauvegardé dans mayotte_page_content.html")
                
            except Exception as e:
                print(f"Erreur lors de la navigation: {e}")
            finally:
                await browser.close()
    
    async def download_pdf(self):
        """Télécharge le PDF si trouvé"""
        if not self.pdf_url:
            print("Aucune URL PDF trouvée")
            return False
            
        try:
            # Configuration SSL pour ignorer la vérification des certificats
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                async with session.get(self.pdf_url, headers=headers) as response:
                    if response.status == 200:
                        self.pdf_content = await response.read()
                        with open('/Users/paularnould/avocats_mayotte.pdf', 'wb') as f:
                            f.write(self.pdf_content)
                        print("PDF téléchargé avec succès")
                        return True
                    else:
                        print(f"Erreur téléchargement PDF: {response.status}")
                        return False
        except Exception as e:
            print(f"Erreur lors du téléchargement: {e}")
            return False
    
    def extract_pdf_data(self):
        """Extrait les données du PDF avec plusieurs méthodes"""
        if not self.pdf_content and not Path('/Users/paularnould/avocats_mayotte.pdf').exists():
            print("Aucun PDF disponible pour extraction")
            return False
            
        pdf_path = '/Users/paularnould/avocats_mayotte.pdf'
        text = ""
        
        # Essayer d'abord avec pdfplumber (meilleur pour les tableaux)
        try:
            print("Tentative d'extraction avec pdfplumber...")
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"--- Page {page_num + 1} ---\n"
                        text += page_text + "\n"
                        
                    # Essayer aussi d'extraire les tableaux
                    tables = page.extract_tables()
                    if tables:
                        for table_num, table in enumerate(tables):
                            text += f"\n--- Tableau {table_num + 1} ---\n"
                            for row in table:
                                if row:
                                    text += " | ".join([cell or "" for cell in row]) + "\n"
                                    
            print(f"Extraction pdfplumber: {len(text)} caractères")
            
        except Exception as e:
            print(f"Erreur avec pdfplumber: {e}")
            
        # Si pdfplumber n'a pas donné beaucoup de texte, essayer PyMuPDF
        if len(text) < 100:
            try:
                print("Tentative d'extraction avec PyMuPDF...")
                doc = fitz.open(pdf_path)
                text = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text:
                        text += f"--- Page {page_num + 1} ---\n"
                        text += page_text + "\n"
                doc.close()
                print(f"Extraction PyMuPDF: {len(text)} caractères")
                
            except Exception as e:
                print(f"Erreur avec PyMuPDF: {e}")
                
        # Fallback avec PyPDF2
        if len(text) < 100:
            try:
                print("Tentative d'extraction avec PyPDF2...")
                with open(pdf_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"--- Page {page_num + 1} ---\n"
                            text += page_text + "\n"
                print(f"Extraction PyPDF2: {len(text)} caractères")
                
            except Exception as e:
                print(f"Erreur avec PyPDF2: {e}")
                
        # Si toujours pas de texte, essayer OCR sur le PDF image
        if len(text) < 100:
            try:
                print("Tentative d'extraction avec OCR (PDF probablement image)...")
                # Convertir PDF en images
                images = convert_from_path(pdf_path, dpi=300)
                text = ""
                
                for page_num, image in enumerate(images):
                    # Sauvegarder l'image pour inspection
                    image_path = f'/Users/paularnould/page_{page_num + 1}.png'
                    image.save(image_path, 'PNG')
                    
                    # OCR avec tesseract - français
                    page_text = pytesseract.image_to_string(image, lang='fra+eng')
                    if page_text.strip():
                        text += f"--- Page {page_num + 1} (OCR) ---\n"
                        text += page_text + "\n"
                        
                print(f"Extraction OCR: {len(text)} caractères")
                
            except Exception as e:
                print(f"Erreur avec OCR: {e}")
                
        # Sauvegarder le texte extrait pour inspection
        with open('/Users/paularnould/avocats_mayotte_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Texte extrait final: {len(text)} caractères")
        
        if len(text) > 10:
            # Parser le texte pour extraire les informations des avocats
            self.parse_avocat_data(text)
            return True
        else:
            print("Pas assez de texte extrait du PDF")
            return False
    
    def parse_avocat_data(self, text):
        """Parse le texte pour extraire les données des avocats"""
        # Patterns de recherche pour les informations d'avocats
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'nom_prenom': r'^([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ][a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]+(?:\s[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ][a-zàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]+)*)',
            'annee': r'\b(19|20)\d{2}\b',
            'specialisation': r'(spécialis|spécial|domaine|matière|droit)',
        }
        
        lines = text.split('\n')
        current_avocat = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_avocat:
                    self.avocats_data.append(current_avocat)
                    current_avocat = {}
                continue
            
            # Rechercher email
            email_match = re.search(patterns['email'], line, re.IGNORECASE)
            if email_match:
                current_avocat['email'] = email_match.group()
            
            # Rechercher année
            annee_match = re.search(patterns['annee'], line)
            if annee_match:
                current_avocat['annee_inscription'] = annee_match.group()
            
            # Si la ligne contient un nom (commence par une majuscule)
            if re.match(r'^[A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ]', line):
                if 'nom' not in current_avocat:
                    current_avocat['nom'] = line
            
            # Rechercher spécialisations
            if re.search(patterns['specialisation'], line, re.IGNORECASE):
                if 'specialisations' not in current_avocat:
                    current_avocat['specialisations'] = []
                current_avocat['specialisations'].append(line)
            
            # Stocker la ligne brute pour analyse
            if 'raw_data' not in current_avocat:
                current_avocat['raw_data'] = []
            current_avocat['raw_data'].append(line)
        
        # Ajouter le dernier avocat s'il existe
        if current_avocat:
            self.avocats_data.append(current_avocat)
        
        print(f"Nombre d'avocats extraits: {len(self.avocats_data)}")
    
    def save_data(self):
        """Sauvegarde les données extraites"""
        if not self.avocats_data:
            print("Aucune donnée à sauvegarder")
            return
        
        # Sauvegarde JSON
        with open('/Users/paularnould/avocats_mayotte.json', 'w', encoding='utf-8') as f:
            json.dump(self.avocats_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarde CSV
        if self.avocats_data:
            fieldnames = set()
            for avocat in self.avocats_data:
                fieldnames.update(avocat.keys())
            
            with open('/Users/paularnould/avocats_mayotte.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=list(fieldnames))
                writer.writeheader()
                for avocat in self.avocats_data:
                    # Convertir les listes en string pour CSV
                    row = avocat.copy()
                    for key, value in row.items():
                        if isinstance(value, list):
                            row[key] = '; '.join(value)
                    writer.writerow(row)
        
        print("Données sauvegardées dans:")
        print("  - avocats_mayotte.json")
        print("  - avocats_mayotte.csv")
    
    async def run(self):
        """Exécute le processus complet de scraping"""
        print("=== Scraping des avocats du barreau de Mayotte ===")
        
        # Étape 1: Navigation et recherche PDF
        await self.navigate_and_find_pdf()
        
        # Étape 2: Téléchargement PDF si trouvé
        if self.pdf_url:
            await self.download_pdf()
        
        # Étape 3: Extraction des données
        if self.extract_pdf_data():
            # Étape 4: Sauvegarde
            self.save_data()
        else:
            print("Échec de l'extraction des données du PDF")

async def main():
    scraper = MayotteAvocatsScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())