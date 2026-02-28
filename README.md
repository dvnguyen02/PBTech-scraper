# PB Tech Scraper

Scrapes product data (name, specs, price, URL) from [PB Tech NZ](https://www.pbtech.co.nz) and saves to JSON.

## Setup

```bash
pip install -r requirements.txt
```

This project requires Google Chrome installed since we will be using ChromeDriverManager 

## Usage

1. **Get category paths** (only needed once, or to refresh):
   ```bash
   python getSitemapxml.py
   ```
   This crawls pbtech.com for category URLs and outputs `categorySites.json`.
   You could adjust the queue size to be much larger to get all category paths but I don't have enough time so...

2. **Run the scraper:**
   ```bash
   python scraper.py
   ```
   Scrapes all categories and saves JSON files to `data/`.
