#!/usr/bin/env python3
"""
Improved scraper for MUIS Halal Establishments with CSRF token handling
"""

import requests
import json
import csv
import time
import re
import os
from datetime import datetime
from typing import List, Dict, Set, Tuple
import logging
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HalalScraper:
    def __init__(self):
        self.base_url = "https://halal.muis.gov.sg/api/halal/establishments"
        self.main_url = "https://halal.muis.gov.sg/halal/establishments"
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
        self.csrf_token = None
        self.establishments: Set[str] = set()

    def get_csrf_token(self) -> bool:
        """Get CSRF token from the main page"""
        try:
            logger.info("Getting CSRF token from main page...")
            response = self.session.get(self.main_url, timeout=10)

            if response.status_code != 200:
                logger.error(f"Failed to load main page: {response.status_code}")
                return False

            # Try to find CSRF token in the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for CSRF token in various places
            csrf_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if csrf_input:
                self.csrf_token = csrf_input.get('value')
                logger.info("Found CSRF token in input field")
                return True

            # Look for token in meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                self.csrf_token = csrf_meta.get('content')
                logger.info("Found CSRF token in meta tag")
                return True

            # Look for token in script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # Look for common CSRF token patterns
                    token_match = re.search(r'csrf[_-]?token[\'\"]\s*:\s*[\'\"](.*?)[\'\"]', script.string, re.IGNORECASE)
                    if token_match:
                        self.csrf_token = token_match.group(1)
                        logger.info("Found CSRF token in script")
                        return True

            logger.warning("Could not find CSRF token")
            return False

        except Exception as e:
            logger.error(f"Error getting CSRF token: {e}")
            return False

    def get_search_terms(self) -> List[str]:
        """Generate comprehensive list of search terms to ensure complete coverage"""
        terms = []

        # Start with wildcard and most productive terms
        priority_terms = ['*', 'a', 'e', 'i', 'o', 'u', 'r', 's', 't', 'n']
        terms.extend(priority_terms)

        # All single characters (letters and numbers)
        terms.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
        terms.extend([str(i) for i in range(10)])

        # Two-letter combinations (most common ones)
        common_2letter = [
            'th', 'he', 'in', 'er', 'an', 're', 'ed', 'nd', 'ha', 'et',
            'ou', 'ea', 'ti', 'to', 'it', 'st', 'io', 'le', 'is', 'ul',
            'ar', 'as', 'de', 'rt', 've', 'ss', 'ee', 'tt', 'ff', 'al'
        ]
        terms.extend(common_2letter)

        # Food and restaurant terms
        food_terms = [
            'restaurant', 'cafe', 'food', 'kitchen', 'stall', 'court', 'centre',
            'mall', 'market', 'hawker', 'canteen', 'bakery', 'shop', 'bar',
            'muslim', 'halal', 'malay', 'indian', 'chinese', 'western', 'asian',
            'chicken', 'rice', 'noodle', 'beef', 'fish', 'seafood', 'pizza',
            'burger', 'sandwich', 'curry', 'soup', 'dessert', 'cake', 'bread',
            'coffee', 'tea', 'juice', 'grill', 'fried', 'roast', 'steam'
        ]
        terms.extend(food_terms)

        # Singapore locations and common words
        sg_terms = [
            'singapore', 'jurong', 'tampines', 'orchard', 'marina', 'bugis',
            'toa', 'ang', 'bedok', 'woodlands', 'yishun', 'sembawang',
            'changi', 'plaza', 'junction', 'hub', 'point', 'park', 'central',
            'north', 'south', 'east', 'west', 'avenue', 'road', 'street',
            'mrt', 'station', 'shopping', 'center', 'building', 'tower',
            'hotel', 'hospital', 'school', 'university', 'airport'
        ]
        terms.extend(sg_terms)

        # Common business words and prefixes
        business_terms = [
            'the', 'and', 'ltd', 'pte', 'co', 'group', 'international',
            'services', 'trading', 'holdings', 'corporation', 'company',
            'enterprise', 'business', 'outlet', 'branch', 'main', 'new'
        ]
        terms.extend(business_terms)

        # Special characters that might be in names
        special_terms = ['&', '@', '-', '+', '#', '(', ')', '[', ']']
        terms.extend(special_terms)

        return terms

    def search_establishments(self, search_term: str) -> List[Dict]:
        """Search for establishments with given term"""
        try:
            # Update headers for API call
            api_headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Referer': self.main_url,
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }

            if self.csrf_token:
                api_headers['X-CSRF-Token'] = self.csrf_token

            payload = {"text": search_term}

            response = self.session.post(
                self.base_url,
                headers=api_headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    logger.info(f"'{search_term}': {len(data['data'])} results ({data.get('totalRecords', 0)} total)")
                    return data['data']
                else:
                    logger.debug(f"'{search_term}': No results")
            else:
                logger.warning(f"'{search_term}': HTTP {response.status_code}")
                if response.status_code == 400:
                    logger.debug(f"Response: {response.text[:200]}")

        except Exception as e:
            logger.error(f"Error searching '{search_term}': {e}")

        return []

    def scrape_all(self) -> List[Dict]:
        """Scrape all establishments using various search terms"""
        logger.info("Starting comprehensive scrape of halal establishments...")

        # First, get CSRF token
        if not self.get_csrf_token():
            logger.warning("Proceeding without CSRF token")

        search_terms = self.get_search_terms()
        unique_establishments = {}  # Use dict to track by unique key

        for i, term in enumerate(search_terms, 1):
            logger.info(f"[{i}/{len(search_terms)}] Searching: '{term}'")

            results = self.search_establishments(term)

            if results:  # If we got results, this term works
                for establishment in results:
                    # Create unique key from ID and number
                    unique_key = f"{establishment.get('id', '')}-{establishment.get('number', '')}"

                    if unique_key not in unique_establishments:
                        unique_establishments[unique_key] = establishment

                # If we found a working search term, try variations
                if len(results) > 0:
                    logger.info(f"Found working term '{term}' - trying similar variations")

                    # Try with spaces and common prefixes/suffixes
                    variations = [
                        f" {term}",
                        f"{term} ",
                        f"*{term}",
                        f"{term}*",
                        f"{term}s",
                        f"the {term}"
                    ]

                    for var in variations:
                        var_results = self.search_establishments(var)
                        for establishment in var_results:
                            unique_key = f"{establishment.get('id', '')}-{establishment.get('number', '')}"
                            if unique_key not in unique_establishments:
                                unique_establishments[unique_key] = establishment

            # Rate limiting - be nice to the server
            time.sleep(0.3)

            # Progress update every 20 searches
            if i % 20 == 0:
                logger.info(f"Progress: {i}/{len(search_terms)} searches complete. "
                           f"Found {len(unique_establishments)} unique establishments so far.")

            # Continue until we've tried all terms to ensure complete coverage

        final_results = list(unique_establishments.values())
        logger.info(f"Scraping complete! Found {len(final_results)} unique establishments")

        return final_results

    def clean_data(self, data: List[Dict]) -> List[Dict]:
        """Clean and format the establishment data"""
        cleaned = []

        for item in data:
            cleaned_item = {
                'name': item.get('name', '').strip(),
                'address': item.get('address', '').strip(),
                'type': item.get('subSchemeText', '').strip(),
                'number': item.get('number', '').strip(),
                'scheme': item.get('schemeText', '').strip(),
                'id': item.get('id', '').strip(),
                'postal': item.get('postal', '').strip()
            }
            cleaned.append(cleaned_item)

        # Sort by name
        cleaned.sort(key=lambda x: x['name'].lower())

        return cleaned

    def save_to_json(self, data: List[Dict], filename: str = 'halal_establishments.json'):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(data)} establishments to {filename}")

    def save_to_csv(self, data: List[Dict], filename: str = 'halal_establishments.csv'):
        """Save data to CSV file"""
        if not data:
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} establishments to {filename}")

    def create_metadata(self, data: List[Dict]) -> Dict:
        """Create metadata about the scraped data"""
        metadata = {
            'last_updated': datetime.now().isoformat(),
            'total_establishments': len(data),
            'types': {},
            'schemes': {}
        }

        # Count by type and scheme
        for item in data:
            item_type = item.get('type', 'Unknown')
            scheme = item.get('scheme', 'Unknown')

            metadata['types'][item_type] = metadata['types'].get(item_type, 0) + 1
            metadata['schemes'][scheme] = metadata['schemes'].get(scheme, 0) + 1

        return metadata

    def compare_with_previous(self, current_data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare current data with previous version to find changes"""
        previous_file = 'halal_establishments.json'

        if not os.path.exists(previous_file):
            logger.info("No previous data found - treating all establishments as new")
            return current_data, [], []

        try:
            with open(previous_file, 'r', encoding='utf-8') as f:
                previous_data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading previous data: {e}")
            return current_data, [], []

        # Create sets of unique identifiers for comparison
        current_ids = {f"{item['id']}-{item['number']}" for item in current_data}
        previous_ids = {f"{item['id']}-{item['number']}" for item in previous_data}

        # Create dictionaries for easy lookup
        current_dict = {f"{item['id']}-{item['number']}": item for item in current_data}
        previous_dict = {f"{item['id']}-{item['number']}": item for item in previous_data}

        # Find new, removed, and updated establishments
        new_ids = current_ids - previous_ids
        removed_ids = previous_ids - current_ids
        existing_ids = current_ids & previous_ids

        new_establishments = [current_dict[id_] for id_ in new_ids]
        removed_establishments = [previous_dict[id_] for id_ in removed_ids]

        # Check for updates in existing establishments
        updated_establishments = []
        for id_ in existing_ids:
            current_item = current_dict[id_]
            previous_item = previous_dict[id_]

            # Compare key fields (excluding timestamps)
            if (current_item['name'] != previous_item['name'] or
                current_item['address'] != previous_item['address'] or
                current_item['type'] != previous_item['type']):
                updated_establishments.append({
                    'previous': previous_item,
                    'current': current_item
                })

        logger.info(f"Found {len(new_establishments)} new, {len(removed_establishments)} removed, "
                   f"{len(updated_establishments)} updated establishments")

        return new_establishments, removed_establishments, updated_establishments

    def save_changelog(self, new_establishments: List[Dict], removed_establishments: List[Dict],
                      updated_establishments: List[Dict]):
        """Save changelog of changes"""
        changelog_entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': {
                'new': len(new_establishments),
                'removed': len(removed_establishments),
                'updated': len(updated_establishments)
            },
            'changes': {
                'new': new_establishments,
                'removed': removed_establishments,
                'updated': updated_establishments
            }
        }

        # Load existing changelog or create new one
        changelog_file = 'changelog.json'
        changelog = []

        if os.path.exists(changelog_file):
            try:
                with open(changelog_file, 'r', encoding='utf-8') as f:
                    changelog = json.load(f)
            except Exception as e:
                logger.error(f"Error reading changelog: {e}")

        # Add new entry to the beginning
        changelog.insert(0, changelog_entry)

        # Keep only last 50 entries to prevent file from growing too large
        changelog = changelog[:50]

        # Save updated changelog
        with open(changelog_file, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, indent=2, ensure_ascii=False)

        logger.info(f"Changelog updated with {len(new_establishments)} new, "
                   f"{len(removed_establishments)} removed, {len(updated_establishments)} updated establishments")

def main():
    """Main function to run the scraper"""
    scraper = HalalScraper()

    # Scrape all data
    raw_data = scraper.scrape_all()

    if not raw_data:
        logger.error("No data scraped. Check if the API is accessible.")
        # Create empty files so GitHub Actions doesn't fail
        with open('halal_establishments.json', 'w') as f:
            json.dump([], f)
        with open('halal_establishments.csv', 'w') as f:
            f.write('name,address,type,number,scheme,postal\n')
        return

    # Clean the data
    clean_data = scraper.clean_data(raw_data)

    # Compare with previous data to track changes
    new_establishments, removed_establishments, updated_establishments = scraper.compare_with_previous(clean_data)

    # Save changelog if there are any changes
    if new_establishments or removed_establishments or updated_establishments:
        scraper.save_changelog(new_establishments, removed_establishments, updated_establishments)
    else:
        logger.info("No changes detected since last update")

    # Save to files
    scraper.save_to_json(clean_data)
    scraper.save_to_csv(clean_data)

    # Create and save metadata
    metadata = scraper.create_metadata(clean_data)
    with open('metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info("Scraping complete!")
    logger.info(f"Total establishments: {len(clean_data)}")
    logger.info(f"Types found: {len(metadata['types'])}")
    logger.info(f"Schemes found: {len(metadata['schemes'])}")

if __name__ == "__main__":
    main()