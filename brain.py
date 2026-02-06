# brain.py

from scraper import scrape_properties
import pandas as pd
import os
import json
from datetime import datetime

pd.options.display.max_columns = None
pd.options.display.float_format = '{:,.0f}'.format

# Create pulled-data folder if it doesn't exist
PULLED_DATA_DIR = "pulled-data"
METADATA_FILE = f"{PULLED_DATA_DIR}/scrape_metadata.json"

if not os.path.exists(PULLED_DATA_DIR):
    os.makedirs(PULLED_DATA_DIR)
    print(f"Created '{PULLED_DATA_DIR}' folder")

def load_metadata():
    """Load scraping metadata (last page, total records, etc.)"""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_metadata(metadata):
    """Save scraping metadata."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_metadata_summary():
    """Print current scraping progress."""
    metadata = load_metadata()
    if not metadata:
        print("No scraping history found. Starting fresh!")
        return

    print("\n" + "="*60)
    print("SCRAPING HISTORY")
    print("="*60)
    print(f"Last page scraped: {metadata.get('last_page', 'N/A')}")
    print(f"Total records collected: {metadata.get('total_records', 0)}")
    print(f"Total batches created: {metadata.get('total_batches', 0)}")
    print(f"Last updated: {metadata.get('last_updated', 'N/A')}")
    print("="*60 + "\n")

def save_batch(batch_data, batch_number):
    """Save a batch of 100 records to a CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{PULLED_DATA_DIR}/batch_{batch_number:03d}_{timestamp}.csv"

    df_batch = pd.DataFrame(batch_data)
    df_batch.to_csv(filename, index=False)
    print(f"  ✓ Saved batch {batch_number} ({len(batch_data)} records) → {filename}")
    return filename

def run_analysis(start_page=None, end_page=None, resume=False):
    """
    Scrape properties and save in batches of 100 records.

    Parameters:
    -----------
    start_page : int, optional
        First page to scrape (default: 1 or resume from last)
    end_page : int, optional
        Last page to scrape (default: start_page if only start given)
    resume : bool, optional
        Resume from the last scraped page (default: False)

    Examples:
    ---------
    # Scrape pages 1-5
    run_analysis(start_page=1, end_page=5)

    # Scrape pages 10-20
    run_analysis(start_page=10, end_page=20)

    # Resume from last page
    run_analysis(resume=True)

    # Scrape 10 more pages from page 5
    run_analysis(start_page=5, end_page=15)
    """

    # Handle page range logic
    metadata = load_metadata()

    if resume:
        if not metadata:
            print("No previous scraping found. Starting from page 1.")
            start_page = 1
            end_page = 10
        else:
            last_page = metadata.get('last_page', 1)
            print(f"Resuming from page {last_page + 1}...")
            start_page = last_page + 1
            end_page = last_page + 10  # Scrape next 10 pages
    else:
        if start_page is None:
            start_page = 1
        if end_page is None:
            end_page = start_page

    # Validate page range
    if start_page > end_page:
        print("Error: start_page cannot be greater than end_page")
        return pd.DataFrame(), pd.Series()

    num_pages = end_page - start_page + 1

    print(f"\nStarting scrape for pages {start_page}-{end_page} ({num_pages} pages)...\n")

    # Scrape properties with custom page range
    all_listings = scrape_properties(pages=num_pages, start_page=start_page)
    print(f"\nTotal listings scraped: {len(all_listings)}")

    if not all_listings:
        print("Scraper returned nothing. Check class names in scraper.py!")
        return pd.DataFrame(), pd.Series()

    # Create dataframe for analysis
    df = pd.DataFrame(all_listings)

    if df.empty:
        print("DataFrame is empty after scraping!")
        return pd.DataFrame(), pd.Series()

    print(f"Columns found: {df.columns.tolist()}\n")

    # 1. Basic Cleaning
    df_clean = df[(df['Price'] > 0) & (df['Price'] < 2_000_000_000)].copy()
    df_clean = df_clean.dropna(subset=['Bedrooms'])
    df_clean = df_clean[df_clean['Bedrooms'] > 0]  # Filter out plots/lands with 0 bedrooms

    print(f"Records after cleaning: {len(df_clean)}\n")

    # 2. Save data in batches of 100
    print("Saving data in batches of 100 records:\n")

    # Get current batch number from metadata
    current_metadata = load_metadata()
    batch_number = (current_metadata.get('total_batches', 0) if current_metadata else 0) + 1
    batch_size = 100
    saved_files = []

    for i in range(0, len(df_clean), batch_size):
        batch = df_clean.iloc[i:i + batch_size]
        if len(batch) > 0:
            filename = save_batch(batch.to_dict('records'), batch_number)
            saved_files.append(filename)
            batch_number += 1

    print(f"\n✓ Total files created: {len(saved_files)}")

    # 3. Update metadata
    total_records = (current_metadata.get('total_records', 0) if current_metadata else 0) + len(df_clean)
    new_metadata = {
        'last_page': end_page,
        'total_records': total_records,
        'total_batches': batch_number - 1,
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'last_scrape_range': f"{start_page}-{end_page}"
    }
    save_metadata(new_metadata)

    # 4. Market Analysis: Average Price by Bedroom Count
    if len(df_clean) > 0:
        avg_prices = df_clean.groupby('Bedrooms')['Price'].mean()

        print("\n" + "="*60)
        print("MARKET ANALYSIS - Average Price by Bedroom Count")
        print("="*60)
        print(avg_prices)

        # 5. Deal Detection Logic
        def find_deals(row):
            avg = avg_prices.get(row['Bedrooms'])
            # A "Deal" is anything 50% below the average for that bedroom count
            if avg and row['Price'] < (avg * 0.5):
                return True
            return False

        df_clean['Is_Deal'] = df_clean.apply(find_deals, axis=1)

        # 6. Show interesting deals
        print("\n" + "="*60)
        print("TOP 10 POTENTIAL DEALS (50% below average)")
        print("="*60)
        deals = df_clean[df_clean['Is_Deal'] == True].sort_values('Price')
        if len(deals) > 0:
            print(deals[['Property Name', 'Price', 'Bedrooms', 'Location']].head(10).to_string())
            print(f"\nTotal deals found: {len(deals)}")
        else:
            print("No deals found (properties below 50% of average price)")

        print("\n" + "="*60)
        print(f"Data saved to: {PULLED_DATA_DIR}/")
        print(f"Last page scraped: {end_page}")
        print(f"Total records so far: {total_records}")
        print("="*60)

        return df_clean, avg_prices

    else:
        print("No data to analyze after cleaning!")
        return pd.DataFrame(), pd.Series()

if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'resume':
            run_analysis(resume=True)
        elif sys.argv[1] == 'history':
            get_metadata_summary()
        elif len(sys.argv) >= 3:
            try:
                start = int(sys.argv[1])
                end = int(sys.argv[2])
                run_analysis(start_page=start, end_page=end)
            except ValueError:
                print("Usage:")
                print("  python brain.py <start_page> <end_page>  # Scrape pages start to end")
                print("  python brain.py resume                   # Resume from last page")
                print("  python brain.py history                  # Show scraping history")
                print("\nExamples:")
                print("  python brain.py 1 5      # Scrape pages 1-5")
                print("  python brain.py 10 20    # Scrape pages 10-20")
                print("  python brain.py resume   # Resume from where you left off")
    else:
        # Default: scrape pages 1-5
        run_analysis(start_page=1, end_page=5)
