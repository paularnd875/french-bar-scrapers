#!/usr/bin/env python3
import asyncio
import csv
from playwright.async_api import async_playwright
import re
from typing import List, Dict

async def scrape_lozere_lawyers_complet():
    """
    Scrape ALL lawyers from Lozère bar association directory
    """
    
    lawyers_data = []
    
    async with async_playwright() as p:
        # Launch browser in headless mode (no visual windows)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to main directory page
            print("Navigating to directory...")
            await page.goto("https://www.avocats-lozere.fr/annuaire/", wait_until="networkidle")
            
            # Accept cookies
            print("Accepting cookies...")
            try:
                # Wait for and click "TOUT ACCEPTER" button
                await page.wait_for_selector('button:has-text("TOUT ACCEPTER")', timeout=5000)
                await page.click('button:has-text("TOUT ACCEPTER")')
                await page.wait_for_timeout(2000)  # Wait for cookie acceptance to process
            except Exception as e:
                print(f"Cookie acceptance failed or not found: {e}")
            
            # Find all lawyer profile links
            print("Finding lawyer profile links...")
            # Look for "Voir la fiche" links specifically
            voir_fiche_links = await page.query_selector_all('a:has-text("Voir la fiche")')
            print(f"Found {len(voir_fiche_links)} 'Voir la fiche' links")
            
            print(f"Processing ALL {len(voir_fiche_links)} lawyers")
            
            # Extract data from each lawyer's profile
            for i, link in enumerate(voir_fiche_links):
                try:
                    # Get the lawyer's profile URL
                    href = await link.get_attribute('href')
                    if href.startswith('/'):
                        full_url = f"https://www.avocats-lozere.fr{href}"
                    else:
                        full_url = href
                    
                    print(f"Processing lawyer {i+1}/{len(voir_fiche_links)}: {full_url}")
                    
                    # Open new page for each lawyer to avoid navigation issues
                    new_page = await context.new_page()
                    await new_page.goto(full_url, wait_until="networkidle")
                    await new_page.wait_for_timeout(1000)
                    
                    # Extract lawyer data
                    lawyer_data = await extract_lawyer_data(new_page)
                    if lawyer_data:
                        lawyers_data.append(lawyer_data)
                        print(f"✓ Extracted: {lawyer_data.get('nom', 'N/A')} {lawyer_data.get('prenom', 'N/A')}")
                    else:
                        print(f"✗ Failed to extract data for lawyer {i+1}")
                    
                    await new_page.close()
                    
                    # Small delay to be respectful
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"✗ Error processing lawyer {i+1}: {e}")
                    continue
            
        finally:
            await browser.close()
    
    return lawyers_data

async def extract_lawyer_data(page) -> Dict[str, str]:
    """Extract data from a lawyer's profile page"""
    
    data = {}
    
    try:
        # Wait for page content to load
        await page.wait_for_selector('body', timeout=10000)
        
        # Extract name from h2 tag specifically
        name_element = await page.query_selector('h2')
        if name_element:
            full_name = await name_element.text_content()
            full_name = full_name.strip()
            # Remove "Maître" prefix if present
            full_name = re.sub(r'^Maître\s+', '', full_name, flags=re.IGNORECASE)
            
            # Try to split name into first name and last name
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                data['prenom'] = name_parts[0]
                data['nom'] = ' '.join(name_parts[1:])
            else:
                data['nom'] = full_name
                data['prenom'] = ''
        else:
            # Fallback: try other selectors
            fallback_element = await page.query_selector('h1, .entry-title, .lawyer-name')
            if fallback_element:
                full_name = await fallback_element.text_content()
                full_name = full_name.strip()
                full_name = re.sub(r'^Maître\s+', '', full_name, flags=re.IGNORECASE)
                
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    data['prenom'] = name_parts[0]
                    data['nom'] = ' '.join(name_parts[1:])
                else:
                    data['nom'] = full_name
                    data['prenom'] = ''
        
        # Extract all text content and look for common fields
        page_text = await page.text_content('body')
        
        # Look for phone numbers
        phone_pattern = r'(?:\+33|0)[1-9](?:[.\s-]?\d{2}){4}'
        phone_matches = re.findall(phone_pattern, page_text)
        if phone_matches:
            data['telephone'] = phone_matches[0].strip()
        
        # Look for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, page_text)
        if email_matches:
            data['email'] = email_matches[0]
        
        # Extract address more cleanly
        address_parts = []
        text_lines = page_text.split('\n')
        
        # Look for address patterns
        for line in text_lines:
            line = line.strip()
            # Skip unwanted content
            if any(skip in line.lower() for skip in ['email:', 'tél:', 'fax:', 'site web:', 'contacter', 'var cf7', 'document.getelementbyid']):
                continue
                
            # Look for address components
            if re.search(r'\d+.*(?:rue|avenue|boulevard|place|chemin|route|résidence)', line, re.IGNORECASE):
                address_parts.append(line)
            elif re.search(r'\d{5}\s*-?\s*[A-Z]+', line):  # Postal code + city
                address_parts.append(line)
        
        if address_parts:
            # Clean and join address parts
            clean_address = ', '.join(address_parts)
            # Remove the lawyer name if it appears in the address
            if data.get('nom') and data.get('prenom'):
                full_name_pattern = f"Maître\\s+{data['prenom']}\\s+{data['nom']}"
                clean_address = re.sub(full_name_pattern, '', clean_address, flags=re.IGNORECASE).strip()
            data['adresse'] = clean_address
        
        # Look for specialties/domains
        specialty_indicators = ['Spécialités', 'Domaines', 'Compétences']
        for indicator in specialty_indicators:
            for line in text_lines:
                if indicator.lower() in line.lower():
                    # Find the next few lines that might contain specialties
                    idx = text_lines.index(line)
                    specialty_text = ' '.join(text_lines[idx:idx+3])
                    data['specialites'] = specialty_text.replace(indicator, '').strip()
                    break
        
        # Look for fax
        fax_pattern = r'(?:Fax|Télécopie)[\s:]*(\+?\d+(?:[.\s-]?\d+)*)'
        fax_match = re.search(fax_pattern, page_text, re.IGNORECASE)
        if fax_match:
            data['fax'] = fax_match.group(1).strip()
        
        # Look for bar admission year
        admission_pattern = r'(?:Barreau|Serment).*?(\d{4})'
        admission_match = re.search(admission_pattern, page_text, re.IGNORECASE)
        if admission_match:
            data['annee_admission'] = admission_match.group(1)
        
    except Exception as e:
        print(f"Error extracting data: {e}")
    
    return data

def save_to_csv(lawyers_data: List[Dict], filename: str):
    """Save lawyers data to CSV file"""
    
    if not lawyers_data:
        print("No data to save")
        return
    
    # Get all possible field names
    all_fields = set()
    for lawyer in lawyers_data:
        all_fields.update(lawyer.keys())
    
    # Sort fields with name and firstname first
    ordered_fields = []
    if 'nom' in all_fields:
        ordered_fields.append('nom')
        all_fields.remove('nom')
    if 'prenom' in all_fields:
        ordered_fields.append('prenom')
        all_fields.remove('prenom')
    
    # Add remaining fields
    ordered_fields.extend(sorted(all_fields))
    
    # Write CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered_fields)
        writer.writeheader()
        writer.writerows(lawyers_data)
    
    print(f"Data saved to {filename}")
    print(f"Total lawyers: {len(lawyers_data)}")

async def main():
    print("Starting Lozère lawyers scraper (COMPLET)...")
    print("This will extract ALL lawyers from the directory.")
    
    lawyers_data = await scrape_lozere_lawyers_complet()
    
    if lawyers_data:
        save_to_csv(lawyers_data, 'avocats_lozere_complet.csv')
        
        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Total lawyers scraped: {len(lawyers_data)}")
        print("\nFirst 5 lawyers:")
        for i, lawyer in enumerate(lawyers_data[:5], 1):
            print(f"{i}. {lawyer.get('nom', 'N/A')} {lawyer.get('prenom', 'N/A')}")
            print(f"   Email: {lawyer.get('email', 'N/A')}")
            print(f"   Tel: {lawyer.get('telephone', 'N/A')}")
            print()
            
        print("All data saved to 'avocats_lozere_complet.csv'")
    else:
        print("No lawyers data extracted")

if __name__ == "__main__":
    asyncio.run(main())