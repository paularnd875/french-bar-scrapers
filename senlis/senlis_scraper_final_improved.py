#!/usr/bin/env python3
"""
Script amélioré pour extraire les avocats du Barreau de Senlis
Corrige les problèmes d'extraction des adresses et sites web
"""

import json
import csv
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'senlis_improved_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SenlisImprovedScraper:
    """
    Scraper amélioré pour extraire TOUS les avocats du Barreau de Senlis
    Corrections apportées:
    - Meilleure extraction des adresses
    - Meilleure extraction des sites web
    - Meilleure parsing du contenu des modales
    """
    
    def __init__(self):
        self.base_url = "https://senlis-avocats.fr/besoin-dun-avocat/annuaire-des-avocats"
        self.lawyers_data = []
        self.failed_extractions = []
        self.total_pages = 12
        
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def separate_name(self, full_name: str) -> tuple[str, str]:
        """
        Separate first name and last name based on capitalization rules:
        - First names: First letter uppercase, rest lowercase (can be compound)
        - Last names: ALL UPPERCASE (can be compound with hyphens)
        """
        if not full_name:
            return "", ""
        
        parts = full_name.strip().split()
        if not parts:
            return "", ""
        
        first_names = []
        last_names = []
        
        for part in parts:
            # Skip empty parts
            if not part:
                continue
            
            # Last name pattern: ALL UPPERCASE (possibly with hyphens)
            if part.isupper():
                last_names.append(part)
            # First name pattern: First letter uppercase, rest lowercase
            elif part[0].isupper() and (len(part) == 1 or part[1:].islower()):
                first_names.append(part)
            # Handle compound first names with hyphens (e.g., "Marie-Claire")
            elif '-' in part and all(
                subpart[0].isupper() and (len(subpart) == 1 or subpart[1:].islower()) 
                for subpart in part.split('-') if subpart
            ):
                first_names.append(part)
            # Handle compound last names with hyphens that might not be all caps
            elif '-' in part and any(subpart.isupper() for subpart in part.split('-')):
                last_names.append(part)
            else:
                # If uncertain, check position - first parts tend to be first names
                if len(first_names) == 0:
                    first_names.append(part)
                else:
                    last_names.append(part)
        
        return ' '.join(first_names), ' '.join(last_names)
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract and format phone number"""
        phone_patterns = [
            r'0[1-9](?:[\s\-\.]*\d{2}){4}',
            r'\+33[1-9](?:[\s\-\.]*\d{2}){4}',
            r'\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = re.sub(r'[^\d+]', '', match.group(0))
                if phone.startswith('+33'):
                    return phone
                elif phone.startswith('0') and len(phone) == 10:
                    return ' '.join([phone[i:i+2] for i in range(0, 10, 2)])
        return None
    
    def extract_website(self, text: str, lawyer_name: str) -> Optional[str]:
        """Extract website URL more intelligently"""
        # Look for URLs
        url_patterns = [
            r'https?://[^\s<>"]+',
            r'www\.[^\s<>"]+',
        ]
        
        found_urls = []
        for pattern in url_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_urls.extend(matches)
        
        if not found_urls:
            return None
            
        # Filter out generic websites that shouldn't be associated with this lawyer
        for url in found_urls:
            url_lower = url.lower()
            # Check if URL contains lawyer's name parts
            name_parts = lawyer_name.lower().split()
            for part in name_parts:
                if len(part) > 3 and part in url_lower:  # Only check meaningful name parts
                    return url
                    
        # If no name match, return the first non-generic URL
        for url in found_urls:
            url_lower = url.lower()
            generic_keywords = ['cabinetamoyal', 'example', 'google', 'facebook']
            is_generic = any(keyword in url_lower for keyword in generic_keywords)
            if not is_generic:
                return url
                
        return None
    
    def parse_address_info(self, text_lines: List[str], lawyer_name: str) -> Dict[str, str]:
        """Parse address information more intelligently"""
        result = {
            'address': '',
            'postal_code': '',
            'city': ''
        }
        
        # Filter out lines that are obviously not addresses
        address_lines = []
        skip_patterns = [
            r'prestation', r'serment', r'contacter', r'telephone', r'mail',
            r'avocat', r'barreau', r'spécialisation', r'domaine',
            r'@', r'http', r'www\.', r'\+33', r'06\s', r'07\s', r'01\s', r'03\s'
        ]
        
        for line in text_lines:
            line = line.strip()
            if len(line) < 5:  # Too short to be an address
                continue
            if line.lower() == lawyer_name.lower():  # Skip if it's just the lawyer name
                continue
            
            # Skip lines matching skip patterns
            skip_line = any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
            if skip_line:
                continue
                
            address_lines.append(line)
        
        # Look for postal code and city
        for line in address_lines:
            postal_match = re.search(r'\b(\d{5})\s+(.+)', line)
            if postal_match:
                result['postal_code'] = postal_match.group(1)
                result['city'] = postal_match.group(2).strip().upper()
                address_lines.remove(line)  # Remove this line from consideration for address
                break
        
        # The remaining lines might be the street address
        street_addresses = []
        for line in address_lines:
            # Look for patterns that suggest a street address
            street_patterns = [
                r'\d+.*(?:rue|avenue|boulevard|place|impasse|allée)',
                r'(?:rue|avenue|boulevard|place|impasse|allée).*\d+',
                r'\d+\s+[A-Za-z]',  # Number followed by letters
            ]
            
            is_street = any(re.search(pattern, line, re.IGNORECASE) for pattern in street_patterns)
            if is_street:
                street_addresses.append(line)
        
        # Take the first valid street address
        if street_addresses:
            result['address'] = street_addresses[0]
        elif address_lines:  # Fallback to first remaining line
            result['address'] = address_lines[0]
            
        return result
    
    def build_page_url(self, page_num: int) -> str:
        """Build correct URL for page number"""
        if page_num == 1:
            return self.base_url
        else:
            return f"{self.base_url}/page-{page_num}"
    
    def extract_lawyer_from_modal(self, page, lawyer_card_element) -> Dict:
        """Extract lawyer info by clicking on their card to open modal"""
        lawyer_info = {
            'first_name': '',
            'last_name': '',
            'name': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'phone': '',
            'email': '',
            'bar_admission': '',
            'website': '',
            'source_url': '',
            'modal_extracted': False,
            'extraction_date': datetime.now().isoformat()
        }
        
        try:
            # Click on the lawyer card to open modal
            lawyer_card_element.click()
            logger.debug("Clicked on lawyer card")
            self.random_delay(1, 2)
            
            # Wait for modal to appear
            try:
                page.wait_for_selector('.modal:visible, [role="dialog"]:visible, .popup:visible', timeout=5000)
            except PlaywrightTimeout:
                logger.debug("Modal did not appear")
            
            # Get modal content with better extraction
            modal_html = page.evaluate('''() => {
                const selectors = [
                    '.modal:not([style*="display: none"])',
                    '[role="dialog"]',
                    '.popup:not([style*="display: none"])',
                    '.modal-content',
                    '.modal-body'
                ];
                
                for (const selector of selectors) {
                    const modal = document.querySelector(selector);
                    if (modal && modal.offsetParent !== null) {
                        return modal.innerHTML;
                    }
                }
                return document.body.innerHTML;
            }''')
            
            if modal_html:
                soup = BeautifulSoup(modal_html, 'html.parser')
                text_content = soup.get_text()
                
                # Extract name (first strong element or h3/h4)
                name_elem = soup.find('strong') or soup.find('h3') or soup.find('h4')
                if name_elem:
                    full_name = self.clean_text(name_elem.get_text())
                    lawyer_info['name'] = full_name
                    
                    # Separate first name and last name
                    first_name, last_name = self.separate_name(full_name)
                    lawyer_info['first_name'] = first_name
                    lawyer_info['last_name'] = last_name
                
                # Extract email
                email = self.extract_email(text_content)
                if email:
                    lawyer_info['email'] = email
                
                # Extract phone number
                phone = self.extract_phone(text_content)
                if phone:
                    lawyer_info['phone'] = phone
                
                # Extract website using improved method
                if lawyer_info['name']:
                    website = self.extract_website(text_content, lawyer_info['name'])
                    if website:
                        lawyer_info['website'] = website
                
                # Parse address information better
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                address_info = self.parse_address_info(lines, lawyer_info['name'])
                lawyer_info.update(address_info)
                
                # Extract bar admission date
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text_content)
                if date_match:
                    lawyer_info['bar_admission'] = date_match.group(1)
                
                lawyer_info['modal_extracted'] = True
                logger.info(f"✅ Extracted: {lawyer_info['name']} - {lawyer_info['email']} - {lawyer_info['address']}")
                
            # Close modal
            self.close_modal(page)
            
        except Exception as e:
            logger.error(f"❌ Error extracting lawyer: {str(e)}")
            
        return lawyer_info
    
    def close_modal(self, page):
        """Close the modal using various methods"""
        try:
            close_methods = [
                lambda: page.keyboard.press('Escape'),
                lambda: page.click('button:has-text("×")', timeout=1000),
                lambda: page.click('.modal-close', timeout=1000),
                lambda: page.click('[aria-label="Close"]', timeout=1000),
                lambda: page.click('body', position={'x': 10, 'y': 10})
            ]
            
            for close_method in close_methods:
                try:
                    close_method()
                    break
                except:
                    continue
                    
            self.random_delay(0.5, 1)
            
        except Exception as e:
            logger.debug(f"Could not close modal: {str(e)}")
    
    def scrape_page(self, page, page_num: int) -> List[Dict]:
        """Scrape all lawyers from a single page"""
        lawyers = []
        
        try:
            url = self.build_page_url(page_num)
            logger.info(f"🔍 Page {page_num}/12: {url}")
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            self.random_delay(2, 4)
            page.wait_for_load_state('networkidle')
            
            # Find lawyer cards
            card_selectors = ['.carte-avocat', '.lawyer-card', 'article']
            lawyer_cards = None
            
            for selector in card_selectors:
                try:
                    cards = page.locator(selector).all()
                    if cards and len(cards) > 1:
                        lawyer_cards = cards
                        logger.info(f"📋 Found {len(cards)} cards with {selector}")
                        break
                except:
                    continue
            
            if lawyer_cards:
                for i, card in enumerate(lawyer_cards):
                    try:
                        logger.info(f"👨‍⚖️ Processing lawyer {i+1}/{len(lawyer_cards)}")
                        
                        lawyer_info = self.extract_lawyer_from_modal(page, card)
                        lawyer_info['page'] = page_num
                        lawyer_info['source_url'] = url
                        
                        if lawyer_info['name']:
                            lawyers.append(lawyer_info)
                        
                        self.random_delay(0.5, 1.5)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing card {i+1}: {str(e)}")
            
            logger.info(f"✅ Page {page_num} done: {len(lawyers)} lawyers")
            
        except Exception as e:
            logger.error(f"❌ Page {page_num} error: {str(e)}")
            
        return lawyers
    
    def save_results(self, filename_prefix: str):
        """Save results to JSON and CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.lawyers_data, f, ensure_ascii=False, indent=2)
        
        # CSV
        csv_file = f"{filename_prefix}_{timestamp}.csv"
        if self.lawyers_data:
            fieldnames = ['first_name', 'last_name', 'name', 'email', 'phone', 'address', 'postal_code', 'city', 'bar_admission', 'website', 'source_url', 'page']
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lawyer in self.lawyers_data:
                    writer.writerow({k: lawyer.get(k, '') for k in fieldnames})
        
        # Email-only file
        emails_file = f"{filename_prefix}_emails_{timestamp}.txt"
        emails = [l['email'] for l in self.lawyers_data if l.get('email')]
        with open(emails_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(emails))
        
        logger.info(f"📁 Files: {json_file}, {csv_file}, {emails_file}")
        logger.info(f"📊 Total: {len(self.lawyers_data)} lawyers, {len(emails)} emails")
        return json_file, csv_file, emails_file
    
    def run(self, test_pages: int = None):
        """Main execution method"""
        pages_to_scrape = test_pages if test_pages else self.total_pages
        
        logger.info("=" * 80)
        logger.info("🚀 SENLIS IMPROVED SCRAPER")
        logger.info(f"📊 Pages à traiter: {pages_to_scrape}")
        logger.info("=" * 80)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,  # Mode headless activé
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                locale='fr-FR'
            )
            
            page = context.new_page()
            
            try:
                for page_num in range(1, pages_to_scrape + 1):
                    lawyers = self.scrape_page(page, page_num)
                    self.lawyers_data.extend(lawyers)
                    
                    if page_num < pages_to_scrape:
                        delay = random.uniform(2, 4)
                        logger.info(f"⏱️ Pause {delay:.1f}s...")
                        time.sleep(delay)
                
                # Save results
                prefix = "SENLIS_IMPROVED_TEST" if test_pages else "SENLIS_IMPROVED_COMPLETE"
                self.save_results(prefix)
                
            except Exception as e:
                logger.error(f"❌ Critical error: {str(e)}")
                self.save_results("SENLIS_IMPROVED_PARTIAL")
                
            finally:
                browser.close()


def main():
    """Main entry point"""
    import sys
    
    try:
        scraper = SenlisImprovedScraper()
        
        # Check if test mode
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            logger.info("🧪 TEST MODE - Processing only 2 pages")
            scraper.run(test_pages=2)
        else:
            logger.info("🚀 PRODUCTION MODE - Processing all pages")
            scraper.run()
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()