# 🕵️‍♂️ Market Detective: Lagos Real Estate Scraper

A Python-based data pipeline that scrapes property listings, cleans financial data using Regex, and identifies undervalued real estate deals through statistical analysis.

## 🚀 Overview

The **Market Detective** automatically scans multiple pages of property listings to find the "pulse" of the market. It calculates the average price per bedroom count and flags properties listed at **30% or more below the market average**.

## 🛠️ Tech Stack

- **Language:** Python 3.12
- **Libraries:** - `BeautifulSoup4` (Web Scraping)
  - `Pandas` (Data Analysis & Filtering)
  - `Matplotlib` (Data Visualization)
  - `Requests` (HTTP Handling)
  - `Re` (Regex for Data Cleaning)

## 📁 Project Structure

- `brain.py`: The analytical engine. Processes data and identifies deals.
- `scraper.py`: The data collector. Handles pagination and HTML parsing.
- `cleaners.py`: Utility functions for scrubbing currency symbols and strings.
- `plotter.py`: Generates visual market reports (Scatter & Bar charts).

## 📊 Sample Insights

Once run, the tool generates a market snapshot like this:

- **Average 2-Bedroom:** ₦233,960,714
- **Average 4-Bedroom:** ₦315,952,381
- **Total Listings Scanned:** 110+

## ⚙️ Installation & Usage

1. **Clone the repo:**
   ```bash
   git clone [https://github.com/TheProject0824/market-detective.git](https://github.com/TheProject0824/market-detective.git)
   cd market-detective
   ```bash
   pip install -r requirements.txt
   ```
Run the detective:
```bash
python plotter.py
```
📝 License
MIT License - feel free to use this for your own market research!
