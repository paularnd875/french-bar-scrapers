#!/usr/bin/env python3
"""
Complete scraper for all lawyers from Alençon Bar Association
Clicks on each lawyer to extract their detailed information from modals
"""

import json
import csv
import logging
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alencon_complete_scraping.log'),
        logging.StreamHandler()
    ]
)

def setup_driver():
    """Setup Chrome driver with optimized options"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Chrome driver setup successful")
        return driver
    except Exception as e:
        logging.error(f"Failed to setup Chrome driver: {e}")
        raise

def close_cookie_banner(driver):
    """Close cookie banner if present"""
    try:
        cookie_selectors = [
            "//button[contains(text(), 'Accepter')]",
            "//button[contains(text(), 'Accept')]", 
            "//button[contains(text(), 'Tout refuser')]",
            "//button[@aria-label='Fermer']"
        ]
        
        for selector in cookie_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        logging.info(f"Closed cookie banner")
                        time.sleep(2)
                        return True
            except:
                continue
    except:
        pass
    return False

def close_modal(driver):
    """Close any open modal"""
    try:
        close_selectors = [
            "//button[@aria-label='Close']",
            "//button[contains(@class, 'close')]",
            "//*[text()='×']",
            "//div[@role='dialog']//button",
            "//*[contains(@class, 'modal')]//button"
        ]
        
        for selector in close_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                for button in buttons:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        return True
            except:
                continue
        
        # Try ESC key
        from selenium.webdriver.common.keys import Keys
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)
        return True
        
    except:
        pass
    return False

def extract_lawyer_info_from_modal(driver):
    """Extract lawyer information from modal content"""
    modal_content = ""
    modal_selectors = [
        "//div[@role='dialog']",
        "//div[contains(@class, 'lightbox')]",
        "//div[contains(@class, 'modal')]"
    ]
    
    for selector in modal_selectors:
        try:
            modals = driver.find_elements(By.XPATH, selector)
            for modal in modals:
                if modal.is_displayed() and modal.size['height'] > 100:
                    modal_content = modal.text
                    if len(modal_content) > 20:  # Has substantial content
                        break
            if modal_content:
                break
        except:
            continue
    
    if not modal_content:
        return None
    
    # Parse the modal content
    lawyer_info = {
        'full_name': '',
        'first_name': '',
        'last_name': '',
        'email': '',
        'phone': '',
        'address': '',
        'inscription_year': ''
    }
    
    lines = modal_content.split('\n')
    
    # Extract name (usually first non-empty lines)
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 3 and not line.startswith('#') and 'svg' not in line.lower():
            # Check if it looks like a name (contains spaces and capital letters)
            if re.match(r'^[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûü]+\s+[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ]', line):
                lawyer_info['full_name'] = line
                name_parts = line.split()
                lawyer_info['first_name'] = name_parts[0] if name_parts else ''
                lawyer_info['last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                break
    
    # Extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', modal_content)
    if email_match:
        lawyer_info['email'] = email_match.group()
    
    # Extract phone (French format)
    phone_match = re.search(r'(\+33|0)[1-9](?:[.\-\s]?\d{2}){4}', modal_content)
    if phone_match:
        lawyer_info['phone'] = phone_match.group().strip()
    
    # Extract inscription year
    year_match = re.search(r'(?:inscrit|inscription).*?depuis\s+(\d{4})', modal_content, re.IGNORECASE)
    if year_match:
        lawyer_info['inscription_year'] = year_match.group(1)
    
    # Extract address (lines with numbers and street indicators)
    address_parts = []
    for line in lines:
        line = line.strip()
        # Look for address patterns
        if (re.search(r'\d+.*(?:rue|avenue|boulevard|place|chemin|allée)', line, re.IGNORECASE) or
            re.search(r'\d{5}\s+[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ]', line) or  # Postal code
            'BP' in line or 'CEDEX' in line):
            address_parts.append(line)
    
    if address_parts:
        lawyer_info['address'] = ' - '.join(address_parts)
    
    return lawyer_info

def find_lawyer_elements(driver):
    """Find all lawyer name elements that can be clicked"""
    lawyers_list = []
    
    # First ensure we're in the right section
    try:
        section_element = driver.find_element(By.XPATH, "//*[contains(text(), 'Avocats inscrits au Barreau d')]")
        driver.execute_script("arguments[0].scrollIntoView(true);", section_element)
        time.sleep(2)
    except:
        logging.warning("Could not find 'Avocats inscrits' section")
    
    # Find all lawyer name elements
    lawyer_selectors = [
        "//span[contains(@class, 'wixui-rich-text__text')]",
        "//div[contains(@class, 'rich-text')]//span",
        "//p//span"
    ]
    
    potential_lawyers = set()  # Use set to avoid duplicates
    
    for selector in lawyer_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    text = element.text.strip()
                    # Check if text looks like a lawyer name
                    if (len(text) > 5 and 
                        re.match(r'^[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ][a-zàáâäèéêëìíîïòóôöùúûü]+\s+[A-ZÀÁÂÄÈÉÊËÌÍÎÏÒÓÔÖÙÚÛÜ]', text) and
                        'Avocat' not in text and 'Barreau' not in text and 'honoraire' not in text.lower()):
                        potential_lawyers.add((text, element))
        except:
            continue
    
    # Convert back to list and filter known lawyers
    known_active_lawyers = [
        "Stéphanie BELLEC-LANDE", "Jacques BLANCHET", "Eric BOCQUILLON", "Aline BOUGEARD",
        "Claire CAILLOT", "Nathalie CATTEAU-LEFRANÇOIS", "Guillaume CHESNOT", "Elise CORTAY",
        "Kévin DE AMORIM", "Bertrand DENIAUD", "Laurence DAURELLE", "Evelyne DUCHESNE",
        "Fabrice EGRET", "Florence GALLOT", "Céline GASNIER", "Agathe GAUTHIER",
        "Elodie GIARD", "Alexandra GIRARD", "Elsa GILET-GINISTY", "Yann GIRONDIN",
        "Paul GOASDOUE", "Baba Sarr GUEYE", "Flavien GUILLOT", "Hubert GUYOMARD",
        "Christine HILAIRE", "Thibaud KOHLLER", "Didier LEFÈVRE", "Stéphanie LELONG",
        "Léa LEMAIRE", "Priscille OZAN", "Blandine ROGUE", "Hélène THIEULART"
    ]
    
    filtered_lawyers = []
    for name, element in potential_lawyers:
        if name in known_active_lawyers:
            filtered_lawyers.append((name, element))
    
    logging.info(f"Found {len(filtered_lawyers)} lawyer elements to process")
    return filtered_lawyers

def scrape_all_lawyers():
    """Main scraping function for all lawyers"""
    driver = setup_driver()
    lawyers_data = []
    
    try:
        url = "https://www.barreau-alencon.fr/copie-de-le-barreau"
        logging.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for initial load
        time.sleep(8)
        
        # Close cookie banner
        close_cookie_banner(driver)
        
        # Find all lawyer elements
        lawyer_elements = find_lawyer_elements(driver)
        
        logging.info(f"Starting to process {len(lawyer_elements)} lawyers...")
        
        for i, (lawyer_name, element) in enumerate(lawyer_elements, 1):
            logging.info(f"\n=== Processing lawyer {i}/{len(lawyer_elements)}: {lawyer_name} ===")
            
            try:
                # Scroll to element and highlight it
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(2)
                driver.execute_script("arguments[0].style.border='2px solid red'", element)
                time.sleep(1)
                
                # Click on the lawyer
                try:
                    element.click()
                    logging.info(f"Clicked on {lawyer_name}")
                except:
                    # Try JavaScript click if regular click fails
                    driver.execute_script("arguments[0].click();", element)
                    logging.info(f"JavaScript clicked on {lawyer_name}")
                
                # Wait for modal to appear
                time.sleep(3)
                
                # Extract info from modal
                lawyer_info = extract_lawyer_info_from_modal(driver)
                
                if lawyer_info and lawyer_info['email']:
                    lawyers_data.append(lawyer_info)
                    logging.info(f"✅ Successfully extracted: {lawyer_info['full_name']} - {lawyer_info['email']}")
                    if lawyer_info['inscription_year']:
                        logging.info(f"   📅 Inscription year: {lawyer_info['inscription_year']}")
                else:
                    # Fallback: at least save the name
                    fallback_info = {
                        'full_name': lawyer_name,
                        'first_name': lawyer_name.split()[0] if lawyer_name.split() else '',
                        'last_name': ' '.join(lawyer_name.split()[1:]) if len(lawyer_name.split()) > 1 else '',
                        'email': '',
                        'phone': '',
                        'address': '',
                        'inscription_year': ''
                    }
                    lawyers_data.append(fallback_info)
                    logging.warning(f"⚠️ No detailed info found for {lawyer_name}, added basic info")
                
                # Close modal
                close_modal(driver)
                time.sleep(2)
                
                # Remove highlighting
                try:
                    driver.execute_script("arguments[0].style.border=''", element)
                except:
                    pass
                
            except Exception as e:
                logging.error(f"❌ Error processing {lawyer_name}: {e}")
                # Try to close any open modal and continue
                close_modal(driver)
                continue
        
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
    finally:
        driver.quit()
    
    return lawyers_data

def save_results(lawyers):
    """Save results to CSV and JSON files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if lawyers:
        # Save to CSV
        csv_filename = f'alencon_lawyers_final_{timestamp}.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['full_name', 'first_name', 'last_name', 'email', 'phone', 'address', 'inscription_year']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for lawyer in lawyers:
                writer.writerow(lawyer)
        
        # Save to JSON
        json_filename = f'alencon_lawyers_final_{timestamp}.json'
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(lawyers, jsonfile, ensure_ascii=False, indent=2)
        
        logging.info(f"Results saved to {csv_filename} and {json_filename}")
        return csv_filename, json_filename
    else:
        logging.warning("No lawyers found to save")
        return None, None

if __name__ == "__main__":
    logging.info("Starting complete Alençon Bar Association scraper...")
    
    lawyers = scrape_all_lawyers()
    csv_file, json_file = save_results(lawyers)
    
    if csv_file and json_file:
        print(f"\n🎯 SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"📁 Results saved to:")
        print(f"  - CSV: {csv_file}")
        print(f"  - JSON: {json_file}")
        print(f"👥 Total lawyers processed: {len(lawyers)}")
        
        # Statistics
        with_emails = len([l for l in lawyers if l.get('email')])
        with_years = len([l for l in lawyers if l.get('inscription_year')])
        
        print(f"\n📊 Statistics:")
        print(f"  - Lawyers with emails: {with_emails}")
        print(f"  - Lawyers with inscription years: {with_years}")
        print(f"  - Success rate: {(with_emails/len(lawyers)*100):.1f}%")
        
    else:
        print("\n❌ No lawyers found. Check the logs for more details.")
    
    logging.info("Complete scraping process finished")