from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import json
import time
import datetime
import os

# Available categories with estimated scraping times (in minutes)
CATEGORIES = {
    "1": {"name": "headphones", "path": "headphones-audio/headphones", "time": 10},
    "2": {"name": "laptops", "path": "computers/laptops", "time": 15},
    "3": {"name": "smartphones", "path": "phones-gps/smartphones", "time": 12},
    "4": {"name": "graphics-cards", "path": "components/graphics-cards", "time": 8},
    "5": {"name": "tvs", "path": "tv-av/tvs", "time": 10},
    "6": {"name": "routers", "path": "networking/routers", "time": 8},
    "7": {"name": "cameras", "path": "cameras/cameras", "time": 10}
}

def display_menu():
    """Display the category selection menu"""
    print("\n=== PB Tech Scraper ===")
    print("Available categories:")
    
    total_time = sum(cat["time"] for cat in CATEGORIES.values())
    
    for key, value in CATEGORIES.items():
        print(f"{key}. {value['name'].title()} (Est. {value['time']} mins)")
    
    print(f"\n8. All Categories (Est. {total_time} mins)")
    print("0. Exit")
    
    return input("\nEnter your choice (multiple categories can be selected with spaces, e.g., '1 2 3'): ")

def get_product_details(driver, product_url):
    """Get detailed information from a product page"""
    driver.get(product_url)
    
    try:
        # Get product name from the product page
        name_element = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#productDiplayPage > div > div:nth-child(2) > div.col-12.js-space-save-top.position-relative > div > div.col-12.col-xl-8.col-xxl-9.js-product-header-block.product-header-block > h1"))
        )
        product_name = name_element.text.strip()
        
        # Get detailed specifications
        try:
            specs_container = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#featuresSpecs"))
            )
            
            specs_dict = {}
            labels = specs_container.find_elements(By.CSS_SELECTOR, "p.label_")
            values = specs_container.find_elements(By.CSS_SELECTOR, "p.value_")
            
            for label, value in zip(labels, values):
                label_text = label.text.strip().rstrip(':')
                value_text = value.text.strip()
                if value_text and value_text != "…":
                    specs_dict[label_text] = value_text
            
            detailed_specs = "\n".join(f"{k}: {v}" for k, v in specs_dict.items())
            if not detailed_specs:
                detailed_specs = "Detailed specs not found"
        except Exception as e:
            print(f"Error getting detailed specs: {e}")
            detailed_specs = "Detailed specs not found"
            
        return {
            'name': product_name,
            'detailed_specs': detailed_specs
        }
    except Exception as e:
        print(f"Error getting product details: {e}")
        return {
            'name': "Name not found",
            'detailed_specs': "Detailed specs not found"
        }

def scrape_page(driver, url):
    """Scrape products from a single page"""
    driver.get(url)
    
    # Find all product containers
    WebDriverWait(driver, 1).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div"))
    )
    
    product_data = []
    product_containers = driver.find_elements(By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div")
    print(f"Found {len(product_containers)} products")
    
    for container in product_containers:
        try:
            name_element = container.find_element(By.CSS_SELECTOR, ".card-item-header a h2")
            general_specs_element = container.find_element(By.CSS_SELECTOR, ".card-item-header a h3")
            
            name = name_element.text.strip()
            general_specs = general_specs_element.text.strip()
            product_url = container.find_element(By.CSS_SELECTOR, ".card-item-header a").get_attribute("href")
            
            try:
                price_elements = container.find_elements(By.CSS_SELECTOR, ".priceClass .item-price-amount .ginc span")
                price = "".join(e.text for e in price_elements).strip().replace('$','').replace(',','')
            except Exception as e:
                print(f"Error getting price from list for {name}: {e}")
                price = "Price not found"
            
            product_data.append({
                'name': name,
                'general_specs': general_specs,
                'url': product_url,
                'price': price
            })
            
        except Exception as e:
            print(f"Error finding product in list: {e}")
    
    return product_data

def get_total_pages(driver):
    """Get the total number of pages for the category"""
    try:
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, ".pagination .page-item .page-link")
        page_numbers = [int(e.text.strip()) for e in pagination_elements if e.text.strip().isdigit()]
        return max(page_numbers) if page_numbers else 1
    except Exception as e:
        print(f"Error getting total pages: {e}")
        return 1

def scrape_category(driver, category_path):
    """Scrape all products from a category"""
    products = []
    base_url = f"https://www.pbtech.co.nz/category/{category_path}/shop-all"
    
    # Get total pages
    driver.get(base_url)
    total_pages = get_total_pages(driver)
    print(f"Found {total_pages} pages for {category_path}")
    
    # Scrape each page
    for page_num in range(1, total_pages + 1):
        print(f"\nScraping page {page_num}/{total_pages}")
        page_url = f"{base_url}?pg={page_num}#sortGroupForm"
        
        # Get basic product info from the listing page
        product_data = scrape_page(driver, page_url)
        
        # Get detailed info for each product
        for product in product_data:
            try:
                details = get_product_details(driver, product['url'])
                products.append({
                    'Product Name': details['name'],
                    'Category': category_path,
                    'General Specs': product['general_specs'],
                    'Detailed Specs': details['detailed_specs'],
                    'Price': product['price'],
                    'Product URL': product['url']
                })
                print(f"Scraped details for: {details['name']}")
            except Exception as e:
                print(f"Error scraping product details: {e}")
    
    return products

def save_results(products, category_path):
    """Save scraped products to files"""
    if not products:
        print("No products to save")
        return
        
    # Create safe filename
    safe_cat_name = category_path.replace("/", "_")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Save as JSON
    json_filename = f'pbtech_{safe_cat_name}_{current_date}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)
    
    # Save as CSV
    csv_filename = f'pbtech_{safe_cat_name}_{current_date}.csv'
    pd.DataFrame(products).to_csv(csv_filename, index=False, encoding='utf-8-sig')
    
    print(f"Successfully scraped {len(products)} products")
    print(f"Data saved to {json_filename} and {csv_filename}")

def main():
    """Main execution function"""
    while True:
        choice = display_menu()
        
        if choice.strip() == "0":
            print("Exiting...")
            return
        
        # Parse user input
        selected_categories = []
        try:
            choices = choice.split()
            if "8" in choices:
                selected_categories = [cat["path"] for cat in CATEGORIES.values()]
                total_time = sum(cat["time"] for cat in CATEGORIES.values())
                print(f"\nScraping all categories. Estimated time: {total_time} minutes")
            else:
                for c in choices:
                    if c in CATEGORIES:
                        selected_categories.append(CATEGORIES[c]["path"])
                        print(f"\nWill scrape: {CATEGORIES[c]['name']}")
                total_time = sum(CATEGORIES[c]["time"] for c in choices if c in CATEGORIES)
                print(f"Estimated total time: {total_time} minutes")
            
            if not selected_categories:
                print("No valid categories selected. Please try again.")
                continue
                
            proceed = input("\nProceed with scraping? (y/n): ")
            if proceed.lower() != 'y':
                continue

            # Create directory for data files
            os.makedirs("data", exist_ok=True)
            os.chdir("data/")
            
            # Initialize Chrome driver only when we're ready to scrape
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
            
            try:
                # Scrape each selected category
                for category_path in selected_categories:
                    print(f"\nScraping category: {category_path}")
                    products = scrape_category(driver, category_path)
                    save_results(products, category_path)
                    
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()