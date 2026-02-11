import asyncio
import json
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from prisma import Prisma
from scraper import scrape_properties
from cleaners import clean_price_string
from geocoding_service import GeocodingService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MarketDetective")

load_dotenv()

METADATA_FILE = "scrape_metadata_propro.json"

class ScraperState:
    def __init__(self):
        self.last_page = 0
        self.scraped_pages = []
        self.total_records = 0
        self.load()

    def load(self):
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.last_page = data.get('last_page', 0)
                    self.scraped_pages = data.get('scraped_pages', [])
                    self.total_records = data.get('total_records', 0)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")

    def save(self):
        try:
            with open(METADATA_FILE, 'w') as f:
                json.dump({
                    'last_page': self.last_page,
                    'scraped_pages': sorted(list(set(self.scraped_pages))),
                    'total_records': self.total_records,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")


async def save_propro_to_db(db, property_data, lat, lon):
    """Save a PropertyPro property to the database."""
    try:
        url = property_data.get('URL', '')
        if not url:
            logger.warning("Property missing URL, skipping...")
            return None

        sale_price = int(property_data.get('Price', 0))
        beds = int(property_data.get('Bedrooms', 0))
        baths = int(property_data.get('Baths', 0))
        features = json.loads(property_data.get('Features', '[]'))
        images = json.loads(property_data.get('Images', '[]'))

        furnished_status = property_data.get('Furnished')
        is_furnished = furnished_status is not None and ('furnished' in furnished_status.lower() or 'yes' in furnished_status.lower())

        prop = await db.propertypro.upsert(
            where={'url': url},
            data={
                'create': {
                    'title': property_data.get('Property Name', 'Unknown'),
                    'url': url,
                    'description': property_data.get('Description', ''),
                    'address': property_data.get('Location', 'Unknown'),
                    'city': property_data.get('City', 'Unknown'),
                    'state': property_data.get('State', 'Lagos'),
                    'latitude': lat,
                    'longitude': lon,
                    'price': sale_price,
                    'beds': beds,
                    'baths': baths,
                    'amenities': features,
                    'images': images,
                    'furnished': is_furnished,
                },
                'update': {
                    'title': property_data.get('Property Name', 'Unknown'),
                    'description': property_data.get('Description', ''),
                    'address': property_data.get('Location', 'Unknown'),
                    'city': property_data.get('City', 'Unknown'),
                    'state': property_data.get('State', 'Lagos'),
                    'latitude': lat,
                    'longitude': lon,
                    'price': sale_price,
                    'beds': beds,
                    'baths': baths,
                    'amenities': features,
                    'images': images,
                    'furnished': is_furnished,
                    'updatedAt': datetime.now()
                }
            }
        )
        return prop
    except Exception as e:
        logger.error(f"Failed to save PropertyPro to DB (URL: {property_data.get('URL')}): {e}")
        return None

async def main():
    state = ScraperState()
    geocoder = GeocodingService()
    db = Prisma()
    await db.connect()

    start_page = state.last_page + 1
    max_pages = 5  # Scrape 5 pages per run for safety/demo

    logger.info(f"Starting scrape from page {start_page} (PropertyPro.ng)")

    try:
        for page_num in range(start_page, start_page + max_pages):
            logger.info(f"Scraping page {page_num} from PropertyPro.ng...")

            listings = scrape_properties(pages=1, start_page=page_num)

            if not listings:
                logger.info(f"No more listings found on page {page_num}. Stopping.")
                break

            for item in listings:
                # Geocode
                address = item.get('Location', '')
                lat, lon = geocoder.geocode(address)

                # Save to DB
                prop = await save_propro_to_db(db, item, lat, lon)

                if prop:
                    state.total_records += 1

            # Update state after each page to protect against crashes
            state.last_page = page_num
            state.scraped_pages.append(page_num)
            state.save()
            logger.info(f"Finished page {page_num}. Total records so far: {state.total_records}")

            # Politeness
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        await db.disconnect()
        state.save()
        logger.info("Scraper finished.")

if __name__ == "__main__":
    asyncio.run(main())
