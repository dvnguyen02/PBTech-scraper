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

# Setup Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Lists to store scraped data
product_names, product_prices, product_general_specs, product_detailed_specs, product_categories, product_urls = [], [], [], [], [], []

def get_product_details(product_url):
    """Get detailed information from a product page"""
    # Navigate to product page
    driver.get(product_url)
    
    try:
        # Get product name from the product page using the updated selector
        name_element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#productDiplayPage > div > div:nth-child(2) > div.col-12.js-space-save-top.position-relative > div > div.col-12.col-xl-8.col-xxl-9.js-product-header-block.product-header-block > h1"))
        )
        product_name = name_element.text.strip()
        
        # Get detailed specifications from #featuresSpecs
        try:
            # First check if the featuresSpecs element exists
            specs_container = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#featuresSpecs"))
            )
            
            # Extract all label-value pairs
            labels = specs_container.find_elements(By.CSS_SELECTOR, "p.label_")
            values = specs_container.find_elements(By.CSS_SELECTOR, "p.value_")
            
            # Combine labels and values into a structured format
            specs_dict = {}
            for i in range(min(len(labels), len(values))):
                label_text = labels[i].text.strip().rstrip(':')
                value_text = values[i].text.strip()
                # Skip empty values
                if value_text and value_text != "…":
                    specs_dict[label_text] = value_text
            
            # Convert dict to formatted string and handle special characters
            detailed_specs_list = []
            for key, value in specs_dict.items():
                # Replace special characters that might cause encoding issues
                sanitized_key = key.replace('™', '').replace('@', 'at')
                sanitized_value = value.replace('™', '').replace('@', 'at')
                detailed_specs_list.append(f"{sanitized_key}: {sanitized_value}")
            
            detailed_specs = "\n".join(detailed_specs_list)
            
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

def scrape_page(url):
    """Scrape products from a single page"""
    driver.get(url)
    
    # Find all product containers
    WebDriverWait(driver, 2).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div"))
    )
    
    # First collect all basic product data and URLs
    product_data = []
    product_containers = driver.find_elements(By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div")
    print(f"Found {len(product_containers)} products")
    
    for container in product_containers:
        try:
            # Extract product name and general specs from product list
            name_element = container.find_element(By.CSS_SELECTOR, ".card-item-header a h2")
            general_specs_element = container.find_element(By.CSS_SELECTOR, ".card-item-header a h3")
            
            name = name_element.text.strip()
            general_specs = general_specs_element.text.strip()
            
            # Get product URL
            product_url = container.find_element(By.CSS_SELECTOR, ".card-item-header a").get_attribute("href")
            
            # Get price from the list page using the new selector
            try:
                price_elements = container.find_elements(By.CSS_SELECTOR, ".priceClass .item-price-amount .ginc span")
                price_text = ""
                for e in price_elements:
                    price_text = price_text+e.text
                price = price_text.strip().replace('$','').replace(',','')
            except Exception as e:
                print(f"Error getting price from list for {name}: {e}")
                price = "Price not found"
            
            # Add to product data for further processing
            product_data.append({
                'name': name,
                'general_specs': general_specs,
                'url': product_url,
                'price': price
            })
            
        except Exception as e:
            print(f"Error finding product in list: {e}")
    
    # Now visit each product page to get detailed information
    for product in product_data:
        try:
            # Get detailed product information (only specs, no detailed features)
            details = get_product_details(product['url'])
            
            # Store all the data
            product_names.append(details['name'])
            product_prices.append(product['price'])  # Using price from list page
            product_general_specs.append(product['general_specs'])
            product_detailed_specs.append(details['detailed_specs'])
            product_urls.append(product['url'])  # Store the product URL
            
            print(f"Scraped details for: {details['name']}")
        except Exception as e:
            print(f"Error scraping product details: {e}")

def get_total_pages():
    """Get the total number of pages for the category"""
    # Try the specific selector first
    last_page_selector = "#mainCatList > div.products_list_wrapper.js-products-list-wrapper.expanded_list.none-swiper.w-100 > div > div.row.w-100.mx-0.pt-3 > div > div > div > ul > li:nth-child(5) > a > span"
    
    try:
        last_page_element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, last_page_selector))
        )
        last_page_text = last_page_element.text.strip()
        if last_page_text.isdigit():
            return int(last_page_text)
    except:
        # Fallback: get all page numbers and find max
        pagination_elements = driver.find_elements(By.CSS_SELECTOR, ".pagination .page-item .page-link")
        page_numbers = [int(e.text.strip()) for e in pagination_elements if e.text.strip().isdigit()]
        return max(page_numbers) if page_numbers else 1

def main():
    """Main execution function"""
    # List of categories to scrape
    # Uncomment this line to scrape multiple categories
    # cat_list = ["headphones-audio/headphones", "computers/laptops", "phones-gps/smartphones", "components/graphics-cards",
    #             "tv-av/tvs", "networking/routers", "cameras/cameras"]
    cat_list = ["computers/laptops"]
    
    # Create directory for data files
    os.makedirs("data", exist_ok=True)
    os.chdir("data/")
    
    try:
        for cat in cat_list:   
            # Clear previous category data
            global product_names, product_prices, product_general_specs, product_detailed_specs, product_categories, product_urls
            
            product_names, product_prices, product_general_specs, product_detailed_specs, product_categories, product_urls = [], [], [], [], [], []
            
            # Set up base URL for the category
            base_url = f"https://www.pbtech.co.nz/category/{cat}/shop-all"

            # Load first page and get total page count (for information only)
            driver.get(base_url)
            total_pages = get_total_pages()
            print(f"Found {total_pages} pages for {cat}")
            
            # Scrape only the first page
            # print("Scraping only page 1 for testing purposes")
            # scrape_page(base_url)
            
            # # Commented out the code to scrape remaining pages
            for page_num in range(1, total_pages + 1):
                scrape_page(f"{base_url}?pg={page_num}#sortGroupForm")
            
            # Create a safe category name for the filename (replace / with _)
            safe_cat_name = cat.replace("/", "_")
            
            # Current date for the filename
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Populate category column
            category_values = [cat] * len(product_names)
            
            # Create product dictionaries
            products = []
            for i in range(len(product_names)):
                product_dict = {
                    'Product Name': product_names[i],
                    'Category': category_values[i],
                    'General Specs': product_general_specs[i],
                    'Detailed Specs': product_detailed_specs[i],
                    'Price': product_prices[i],
                    'Product URL': product_urls[i]
                }
                products.append(product_dict)
            
            # Save as JSON file
            json_filename = f'pbtech_{safe_cat_name}_{current_date}.json'
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=4)
            
            # Save as CSV file
            csv_filename = f'pbtech_{safe_cat_name}_{current_date}.csv'
            pd.DataFrame({
                'Product Name': product_names,
                'Category': category_values,
                'General Specs': product_general_specs,
                'Detailed Specs': product_detailed_specs,
                'Price': product_prices,
                'Product URL': product_urls
            }).to_csv(csv_filename, index=False, encoding='utf-8-sig')  # Use utf-8-sig encoding for better handling of special characters
            
            print(f"Successfully scraped {len(product_names)} products for {cat}")
            print(f"Data saved to {json_filename} and {csv_filename}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

# Run the script
if __name__ == "__main__":
    main()