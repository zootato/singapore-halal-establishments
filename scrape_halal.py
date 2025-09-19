#!/usr/bin/env python3
"""
Automated scraper for MUIS Halal Establishments
Fetches all halal establishments and saves to CSV/JSON
"""

import requests
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HalalScraper:
    def __init__(self):
        self.base_url = "https://halal.muis.gov.sg/api/halal/establishments"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.establishments: Set[str] = set()  # Track unique establishments
        self.all_data: List[Dict] = []

    def get_search_terms(self) -> List[str]:
        """Generate comprehensive list of search terms"""
        terms = []

        # Single characters
        terms.extend([chr(i) for i in range(ord('a'), ord('z') + 1)])
        terms.extend([str(i) for i in range(10)])

        # Common food/restaurant terms
        food_terms = [
            'restaurant', 'cafe', 'food', 'kitchen', 'stall', 'court', 'centre',
            'mall', 'market', 'hawker', 'canteen', 'bakery', 'shop', 'bar',
            'muslim', 'halal', 'malay', 'indian', 'chinese', 'western',
            'chicken', 'rice', 'noodle', 'beef', 'fish', 'seafood', 'pizza',
            'burger', 'sandwich', 'curry', 'soup', 'dessert', 'cake', 'bread'
        ]
        terms.extend(food_terms)

        # Singapore locations
        sg_terms = [
            'singapore', 'jurong', 'tampines', 'orchard', 'marina', 'bugis',
            'toa', 'ang', 'bedok', 'woodlands', 'yishun', 'sembawang',
            'changi', 'plaza', 'junction', 'hub', 'point', 'park', 'mall',
            'central', 'north', 'south', 'east', 'west', 'avenue', 'road',
            'street', 'crescent', 'drive', 'lane', 'close', 'gardens'
        ]
        terms.extend(sg_terms)

        # Symbols and wildcards
        terms.extend(['*', '&', '@', '-', '/', '(', ')', '#', '+'])

        return terms

    def search_establishments(self, search_term: str) -> List[Dict]:
        """Search for establishments with given term"""
        try:
            payload = {"text": search_term}
            response = requests.post(
                self.base_url,
                headers=self.headers,
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

        except Exception as e:
            logger.error(f"Error searching '{search_term}': {e}")

        return []

    def scrape_all(self) -> List[Dict]:
        """Scrape all establishments using various search terms"""
        logger.info("Starting comprehensive scrape of halal establishments...")

        search_terms = self.get_search_terms()
        unique_establishments = {}  # Use dict to track by unique key

        for i, term in enumerate(search_terms, 1):
            logger.info(f"[{i}/{len(search_terms)}] Searching: '{term}'")

            results = self.search_establishments(term)

            for establishment in results:
                # Create unique key from ID and number
                unique_key = f"{establishment.get('id', '')}-{establishment.get('number', '')}"

                if unique_key not in unique_establishments:
                    unique_establishments[unique_key] = establishment

            # Rate limiting - be nice to the server
            time.sleep(0.2)

            # Progress update every 10 searches
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(search_terms)} searches complete. "
                           f"Found {len(unique_establishments)} unique establishments so far.")

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

def main():
    """Main function to run the scraper"""
    scraper = HalalScraper()

    # Scrape all data
    raw_data = scraper.scrape_all()

    if not raw_data:
        logger.error("No data scraped. Exiting.")
        return

    # Clean the data
    clean_data = scraper.clean_data(raw_data)

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