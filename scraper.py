import requests
from bs4 import BeautifulSoup
from cleaners import clean_price_string
import re
import time
import json

def get_stat(soup, label):
    """
    Extract stats like 'Bed', 'Bath', 'Toilet' from the detail page.
    Extracts from JSON-LD structured data which is more reliable than HTML selectors.
    """
    # Try to extract from JSON-LD schema data
    schema_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if label.lower() == 'bed':
                bedrooms = data.get('numberOfBedrooms')
                if bedrooms is not None:
                    return int(bedrooms)
            elif label.lower() == 'bath':
                bathrooms = data.get('numberOfBathroomsTotal') or data.get('numberOfBathrooms')
                if bathrooms is not None:
                    return int(bathrooms)
        except:
            pass

    # Fallback: search in page text for the stat
    stats_alt = soup.find_all(string=re.compile(label, re.IGNORECASE))
    for text in stats_alt:
        match = re.search(r'(\d+)\s*' + label, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return 0

def get_property_type(name):
    """
    Extract property type (Duplex, Flat, House, Bungalow, etc.) from property name.
    """
    name_lower = name.lower()

    # Check for property types in order of specificity
    types = [
        'Detached Duplex', 'Semi Detached Duplex', 'Terrace Duplex',
        'Duplex', 'Detached House', 'Semi Detached House',
        'Terraced House', 'Bungalow', 'Apartment', 'Flat',
        'Condominium', 'Villa', 'Townhouse'
    ]

    for ptype in types:
        if ptype.lower() in name_lower:
            return ptype

    return "Other"

def get_description(soup):
    """Extract description from JSON-LD schema."""
    schema_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    for script in schema_scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') in ['RealEstateListing', 'SingleFamilyResidence']:
                desc = data.get('description', '')
                if desc:
                    # Clean up the description - remove duplicates and truncate
                    desc = desc.split('See property details')[0].strip()
                    return desc[:500]  # Limit to 500 chars
        except:
            pass
    return ""

def get_images(soup):
    """Extract image URLs from gallery."""
    images = soup.find_all('img', {'class': 'gallery-image'})
    image_urls = []
    for img in images:
        src = img.get('src') or img.get('data-lazy')
        if src:
            image_urls.append(src)
    return image_urls

def get_furnished_status(soup):
    """Detect furnished status from page text."""
    page_text = soup.get_text().lower()
    if 'fully furnished' in page_text:
        return 'Fully Furnished'
    elif 'partially furnished' in page_text:
        return 'Partially Furnished'
    elif 'unfurnished' in page_text:
        return 'Unfurnished'
    return None

def parse_location(location_text):
    """Parse location into city and state."""
    if not location_text:
        return "", ""

    # Common Nigerian states to look for
    states = [
        'Lagos', 'Abuja', 'Rivers', 'Ogun', 'Oyo', 'Kano', 'Kaduna',
        'Bauchi', 'Edo', 'Delta', 'Enugu', 'Imo', 'Kwara', 'Kogi',
        'Osun', 'Ondo', 'Cross River', 'Taraba', 'Adamawa', 'Yobe',
        'Borno', 'Jigawa', 'Kebbi', 'Katsina', 'Sokoto', 'Zamfara',
        'Nassarawa', 'Niger', 'Plateau', 'Gombe', 'Ekiti', 'Bayelsa'
    ]

    state = ""
    city = ""

    # First, try to find a state name in the location text
    for s in states:
        if s.lower() in location_text.lower():
            state = s
            # Extract everything before the state as city
            # Look for the word/phrase before state
            idx = location_text.lower().find(s.lower())
            before_state = location_text[:idx].strip()

            # Get the last meaningful part before state (usually the immediate preceding word/phrase)
            if before_state:
                # Split by space and get the last word(s)
                words = before_state.split()
                # Take the last word as the primary city identifier
                city = words[-1] if words else before_state
            else:
                city = location_text.split()[0] if location_text.split() else ""
            break

    # If no state found, try to guess from the text
    if not state:
        # Split by comma if available
        if ',' in location_text:
            parts = [p.strip() for p in location_text.split(',')]
            city = parts[0]
            state = parts[-1]
        else:
            # Split by space and take last part as state
            words = location_text.split()
            if len(words) > 1:
                state = words[-1]
                city = words[-2]
            else:
                city = location_text
                state = "Lagos"  # Default

    return city, state

def scrape_properties(pages=1, start_page=1):
    """
    Scrape properties from PropertyPro.

    Parameters:
    -----------
    pages : int
        Number of pages to scrape
    start_page : int
        Starting page number (default: 1)
    """
    all_listings = []
    base_url = "https://propertypro.ng"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    for page_num in range(start_page, start_page + pages):
        print(f"Scanning Page {page_num}...")
        search_url = f"{base_url}/property-for-sale/house?page={page_num}"
        
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # The search page container
            containers = soup.find_all(class_='pl-title-grid')
            print(f"  Found {len(containers)} listings on search page.")

            for house in containers: 
                link_tag = house.find('a')
                if not link_tag or not link_tag.get('href'):
                    continue
                
                property_url = base_url + link_tag.get('href')
                # Avoid relative paths vs full paths issues
                if not property_url.startswith('http'):
                    property_url = base_url + "/" + link_tag.get('href').lstrip('/')

                # Step 2: Visit the detail page
                try:
                    prop_res = requests.get(property_url, headers=headers)
                    prop_soup = BeautifulSoup(prop_res.text, 'html.parser')

                    # UPDATED SELECTORS based on live site audit
                    name = prop_soup.find('h1', class_='page-heading')
                    
                    price_container = prop_soup.find('div', class_='property-pricing')
                    price = price_container.find('h2') if price_container else None
                    
                    # Location is in the first <p> tag after the h1 title
                    location = None
                    h1 = prop_soup.find('h1', class_='page-heading')
                    if h1:
                        location = h1.find_next('p')
                    # Fallback: if not found, search for location patterns
                    if not location:
                        location = prop_soup.find('p', string=re.compile(r'Property address|address', re.IGNORECASE))
                        if location:
                            location = location.find_next_sibling('p') or location

                    # Features list - extracted from feature icons (img alt text)
                    features = []
                    features_header = prop_soup.find(string=re.compile(r'^Features$', re.IGNORECASE))
                    if features_header:
                        features_container = features_header.find_parent(['div', 'section'])
                        if features_container:
                            # Features are shown as images with alt text like "Feature Name-icon"
                            feature_images = features_container.find_all('img', alt=re.compile('icon', re.IGNORECASE))
                            features = [img.get('alt', '').replace('-icon', '').strip() for img in feature_images]

                    if name and price:
                        property_name = name.get_text().strip()
                        location_text = location.get_text().strip() if location else "N/A"
                        city, state = parse_location(location_text)

                        all_listings.append({
                            "Property Name": property_name,
                            "Property Type": get_property_type(property_name),
                            "Description": get_description(prop_soup),
                            "Price": clean_price_string(price.get_text().strip()),
                            "Bedrooms": get_stat(prop_soup, "Bed"),
                            "Baths": get_stat(prop_soup, "Bath"),
                            "Toilets": get_stat(prop_soup, "Toilet"),
                            "Location": location_text,
                            "City": city,
                            "State": state,
                            "Country": "Nigeria",
                            "Images": json.dumps(get_images(prop_soup)),
                            "Furnished": get_furnished_status(prop_soup),
                            "Features": json.dumps(features),
                            "URL": property_url
                        })
                        print(f"    [OK] Extracted: {name.get_text().strip()[:40]}...")
                    else:
                        print(f"    [SKIP] Missing core data (Name/Price) for {property_url}")

                    time.sleep(0.3) 
                except Exception as e:
                    print(f"    [ERROR] On property page: {e}")
            
            time.sleep(1) 
        except Exception as e:
            print(f"Error scanning page {page_num}: {e}")
    
    return all_listings


