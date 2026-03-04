#!/usr/bin/env python3
"""
Fixed web scraper for Senlis Lawyers Directory
Based on actual website structure analysis
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
        logging.FileHandler(f'senlis_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SenlisLawyersScraperFixed:
    """
    Fixed scraper for Senlis Lawyers Directory using actual website structure
    """
    
    def __init__(self):
        self.base_url = "https://senlis-avocats.fr/besoin-dun-avocat/annuaire-des-avocats/"
        self.lawyers_data = []
        self.failed_extractions = []
        
    def random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def clean_text(self, text: Optional[str]) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from text using regex"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract and format phone number"""
        # Look for French phone number patterns
        phone_patterns = [
            r'0[1-9](?:[\s\-\.]*\d{2}){4}',  # 01 23 45 67 89
            r'\+33[1-9](?:[\s\-\.]*\d{2}){4}',  # +33 1 23 45 67 89
            r'\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                # Clean and format the phone number
                phone = re.sub(r'[^\d+]', '', match.group(0))
                if phone.startswith('+33'):
                    return phone
                elif phone.startswith('0') and len(phone) == 10:
                    return ' '.join([phone[i:i+2] for i in range(0, 10, 2)])
        return None
    
    def scrape_page(self, page, page_num: int = 1) -> List[Dict]:
        """Scrape all lawyers from a single page"""
        lawyers = []
        
        try:
            # Build URL for the page
            if page_num == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}page/{page_num}/"
            
            logger.info(f"Scraping page {page_num}: {url}")
            
            # Navigate to the page
            page.goto(url, wait_until='networkidle', timeout=30000)
            self.random_delay(2, 3)
            
            # Wait for the page content to load
            page.wait_for_load_state('networkidle')
            
            # Get page content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for lawyer information using h3 tags (names)
            h3_elements = soup.find_all('h3')
            logger.info(f"Found {len(h3_elements)} h3 elements (potential lawyer names)")
            
            for i, h3 in enumerate(h3_elements):
                try:
                    lawyer_info = {
                        'name': '',
                        'address': '',
                        'city': '',
                        'postal_code': '',
                        'phone': '',
                        'email': '',
                        'page': page_num,
                        'extraction_date': datetime.now().isoformat()
                    }
                    
                    # Extract name from h3
                    name = self.clean_text(h3.get_text())
                    if not name:
                        continue
                        
                    lawyer_info['name'] = name
                    logger.info(f"Processing lawyer: {name}")
                    
                    # Look for contact information in the same container/parent
                    parent = h3.find_parent()
                    if parent:
                        parent_text = parent.get_text()
                        
                        # Extract phone number
                        phone = self.extract_phone(parent_text)
                        if phone:
                            lawyer_info['phone'] = phone
                        
                        # Extract email
                        email = self.extract_email(parent_text)
                        if email:
                            lawyer_info['email'] = email
                        
                        # Extract address (look for text that's not the name or phone)
                        text_lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                        for line in text_lines:
                            line = self.clean_text(line)
                            if line and line != name and not self.extract_phone(line) and not self.extract_email(line):
                                # This might be address
                                if re.search(r'\d{5}', line):  # Contains postal code
                                    postal_match = re.search(r'\b(\d{5})\b', line)
                                    if postal_match:
                                        lawyer_info['postal_code'] = postal_match.group(1)
                                        city = line.replace(postal_match.group(1), '').strip()
                                        lawyer_info['city'] = city
                                elif not lawyer_info['address']:
                                    lawyer_info['address'] = line
                    
                    # Try to click on the lawyer card to get modal information
                    try:
                        # Look for clickable elements related to this lawyer
                        lawyer_links = page.locator(f'text="{name}"').all()
                        if lawyer_links:
                            for link in lawyer_links:
                                try:
                                    if link.is_visible():
                                        logger.info(f"Clicking on {name} for modal info")
                                        link.click()
                                        self.random_delay(1, 2)
                                        
                                        # Extract modal content
                                        modal_info = self.extract_modal_info(page)
                                        if modal_info:
                                            lawyer_info.update(modal_info)
                                        
                                        # Close modal
                                        self.close_modal(page)
                                        break
                                except:
                                    continue
                    except Exception as e:
                        logger.debug(f"Could not extract modal info for {name}: {str(e)}")
                    
                    if lawyer_info['name']:
                        lawyers.append(lawyer_info)
                        logger.info(f"Successfully extracted: {lawyer_info['name']}")
                    
                    self.random_delay(0.5, 1)
                    
                except Exception as e:
                    logger.error(f"Error processing lawyer {i+1}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error scraping page {page_num}: {str(e)}")
            
        return lawyers
    
    def extract_modal_info(self, page) -> Dict:
        """Extract detailed information from the modal popup"""
        modal_info = {}
        
        try:
            # Wait a bit for modal to load
            self.random_delay(1, 2)
            
            # Get current page content to see if modal opened
            modal_content = page.evaluate('''() => {
                // Look for modal or popup content
                const modal = document.querySelector('[style*="display: block"], .modal:not([style*="display: none"]), .popup, [role="dialog"]');
                if (modal) {
                    return modal.innerText || modal.textContent;
                }
                
                // Look for any element that might contain additional info
                const body = document.body;
                return body.innerText || body.textContent;
            }''')
            
            if modal_content:
                # Extract email if present
                email = self.extract_email(modal_content)
                if email:
                    modal_info['email'] = email
                
                # Look for additional contact info
                phone = self.extract_phone(modal_content)
                if phone:
                    modal_info['phone'] = phone
                    
                # Store modal content for analysis
                modal_info['modal_content'] = modal_content[:500]  # First 500 chars
                
        except Exception as e:
            logger.debug(f"Error extracting modal info: {str(e)}")
        
        return modal_info
    
    def close_modal(self, page):
        """Close the modal using various methods"""
        try:
            # Try pressing ESC key
            page.keyboard.press('Escape')
            self.random_delay(0.5, 1)
            
            # Try clicking outside modal area
            page.click('body', position={'x': 10, 'y': 10})
            
        except Exception as e:
            logger.debug(f"Could not close modal: {str(e)}")
    
    def get_total_pages(self, page) -> int:
        """Determine the total number of pages"""
        try:
            page.goto(self.base_url, wait_until='networkidle')
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for pagination links
            pagination_links = soup.find_all('a', href=re.compile(r'/page/\d+/'))
            if pagination_links:
                page_numbers = []
                for link in pagination_links:
                    href = link.get('href', '')
                    page_match = re.search(r'/page/(\d+)/', href)
                    if page_match:
                        page_numbers.append(int(page_match.group(1)))
                
                if page_numbers:
                    return max(page_numbers)
            
            # If no pagination found, check for page number indicators in text
            page_text = soup.get_text()
            page_matches = re.findall(r'Page \d+ sur (\d+)', page_text)
            if page_matches:
                return int(page_matches[0])
            
            return 1  # Default to 1 page if no pagination found
            
        except Exception as e:
            logger.warning(f"Could not determine total pages: {str(e)}")
            return 12  # Default fallback
    
    def save_to_json(self, data: List[Dict], filename: str):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """Save data to CSV file"""
        try:
            if not data:
                logger.warning("No data to save to CSV")
                return
            
            # Get all unique keys
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())
            
            fieldnames = ['name', 'email', 'phone', 'address', 'postal_code', 'city', 'page', 'extraction_date']
            other_keys = sorted([k for k in all_keys if k not in fieldnames])
            fieldnames.extend(other_keys)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def run(self):
        """Main execution method"""
        logger.info("=" * 60)
        logger.info("Starting Fixed Senlis Lawyers Directory Scraper")
        logger.info(f"Target: {self.base_url}")
        logger.info("=" * 60)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Keep visible for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='fr-FR'
            )
            
            page = context.new_page()
            
            try:
                # Determine total pages
                total_pages = self.get_total_pages(page)
                logger.info(f"Detected {total_pages} total pages")
                
                # Scrape all pages
                for page_num in range(1, total_pages + 1):
                    logger.info(f"\n--- Processing page {page_num}/{total_pages} ---")
                    lawyers = self.scrape_page(page, page_num)
                    self.lawyers_data.extend(lawyers)
                    
                    logger.info(f"Extracted {len(lawyers)} lawyers from page {page_num}")
                    
                    # Add delay between pages
                    if page_num < total_pages:
                        delay = random.uniform(2, 4)
                        logger.info(f"Waiting {delay:.1f} seconds before next page...")
                        time.sleep(delay)
                
                # Save final results
                self.save_final_results()
                
            except Exception as e:
                logger.error(f"Critical error during scraping: {str(e)}")
                self.save_final_results()
                
            finally:
                browser.close()
    
    def save_final_results(self):
        """Save final results to multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to JSON
        json_file = f"senlis_lawyers_fixed_{timestamp}.json"
        self.save_to_json(self.lawyers_data, json_file)
        
        # Save to CSV
        csv_file = f"senlis_lawyers_fixed_{timestamp}.csv"
        self.save_to_csv(self.lawyers_data, csv_file)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETED - SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total lawyers extracted: {len(self.lawyers_data)}")
        
        # Count lawyers with email
        with_email = sum(1 for l in self.lawyers_data if l.get('email'))
        logger.info(f"Lawyers with email: {with_email}/{len(self.lawyers_data)}")
        
        # Count lawyers with phone
        with_phone = sum(1 for l in self.lawyers_data if l.get('phone'))
        logger.info(f"Lawyers with phone: {with_phone}/{len(self.lawyers_data)}")
        
        logger.info(f"\nResults saved to:")
        logger.info(f"  - {json_file}")
        logger.info(f"  - {csv_file}")


def main():
    """Main entry point"""
    try:
        scraper = SenlisLawyersScraperFixed()
        scraper.run()
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()