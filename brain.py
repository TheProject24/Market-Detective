# brain.py

from scraper import scrape_properties
import pandas as pd
pd.options.display.float_format = '{:,.0f}'.format

# DEBUG: Let's see if the data actually made it across

all_listings = scrape_properties(8)
print(f"Total listings imported: {len(all_listings)}")

df = pd.DataFrame(all_listings)
print(f"Columns found in DataFrame: {df.columns.tolist()}")

if not df.empty:
    df =df[(df['Price'] > 0) & (df['Price'] < 2000000000)]

    df = df.dropna(subset=['Beds'])

    avg_prices = df.groupby('Beds')['Price'].mean()

    print("- - - Average Price by bedroom Count - - -")
    print(avg_prices)

    def find_deals(row):
        avg = avg_prices.get(row['Beds'])
        if avg and row['Price'] < (avg * 0.5):
            return True
        return False

    df['Is_Deal'] = df.apply(find_deals, axis=1)

    print("\n--- Top 5 Potential Deals ---")
    print(df[df['Is_Deal'] == True].sort_values('Price').head(5))


    df.to_csv("lagos_property_deals.csv", index=False)

else: 
    print("Scraper returned nothing. Check class anems in scraper.py!")

