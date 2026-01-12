import requests
from bs4 import BeautifulSoup
from cleaners import clean_price_string
import re
import time

all_listings = []
url = "https://propertypro.ng/property-for-sale"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/57.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
first_title = soup.find(class_='pl-title')

def get_bedrooms(text):
    match = re.search(r'(\d+)\s*Bed', text)
    return int(match.group(1)) if match else None

def scrape_properties(pages=5):
    all_listings = []
    headers = {"User-Agent": "Mozilla/5.0 ..."} # Your full header here

    for page_num in range(1, pages + 1):
        print(f"Scanning Page {page_num}...")
        url = f"https://propertypro.ng/property-for-sale?page={page_num}"
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        containers = soup.find_all(class_='pl-title-grid position-relative')

        for house in containers: 
            name_el = house.find(class_='pl-title')
            price_el = house.find(class_='pl-price')

            if name_el and price_el:
                all_listings.append({
                    "Title": name_el.get_text().strip().split('\n')[0],
                    "Price": clean_price_string(price_el.get_text().strip()),
                    "Beds": get_bedrooms(house.get_text())
                })
        time.sleep(1) # Be gentle
    
    return all_listings # This sends the list back to brain.py