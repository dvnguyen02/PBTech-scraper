from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import datetime
import os

# Setup Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Lists to store scraped data
product_names, product_prices, product_specs, product_features, product_categories = [], [], [], [], []

def get_product_details(product_url):
    # Navigate to product page
    driver.get(product_url)
    #print(f"Getting details from: {product_url}")
    
    try:
        # Wait for and extract the product details
        detail_element = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#undefined1 > div.pt-3"))
        )
        return detail_element.text.strip()
    except Exception as e:
        print(f"Error getting product details: {e}")
        return "Details not found"

# Function to scrape products from a single page
def scrape_page(url):
    driver.get(url)
    #print(f"Scraping: {url}")
    
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
            # Extract product details
            name_element = container.find_element(By.CSS_SELECTOR, ".card-item-header a h2")
            name = name_element.text.strip()
            spec = container.find_element(By.CSS_SELECTOR, ".card-item-header a h3").text.strip()
            
            # Get product URL
            product_url = container.find_element(By.CSS_SELECTOR, ".card-item-header a").get_attribute("href")
            
            # JavaScript to extract price
            script = """
            const container = arguments[0];
            const priceContainer = container.querySelector('.item-price-amount');
            if (!priceContainer) return '';
            
            const dollarElement = priceContainer.querySelector('.ginc div span.price-dollar');
            const centsElement = priceContainer.querySelector('.ginc div span.price-cents');
            
            if (dollarElement && centsElement) {
                return (dollarElement.textContent.trim() + centsElement.textContent.trim()).replace('$', '');
            } else if (dollarElement) {
                return dollarElement.textContent.trim().replace('$', '');
            }
            return 'Price not found';
            """
            
            price = driver.execute_script(script, container)
            
            # Store the basic data with URL for later processing
            product_data.append({
                'name': name,
                'spec': spec,
                'price': price,
                'url': product_url
            })
            
            #print(f"Found: {name} - {price}")
        except Exception as e:
            print(f"Error finding product: {e}")
    
    # Now visit each product page to get detailed features
    for product in product_data:
        try:
            # Get detailed features
            detailed_features = get_product_details(product['url'])
            
            # Store all the data
            product_names.append(product['name'])
            product_prices.append(product['price'])
            product_specs.append(product['spec'])
            product_features.append(detailed_features)
            
            #print(f"Scraped details for: {product['name']}")
        except Exception as e:
            print(f"Error scraping product details: {e}")

# Function to get the total number of pages
def get_total_pages():
    # Try the specific selector first
    last_page_selector = "#mainCatList > div.products_list_wrapper.js-products-list-wrapper.expanded_list.none-swiper.w-100 > div > div.row.w-100.mx-0.pt-3 > div > div > div > ul > li:nth-child(5) > a > span"
    
    try:
        last_page_element = WebDriverWait(driver, 3).until(
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

# Main execution
cat_list = ["headphones-audio/headphones", "computers/laptops", "phones-gps/smartphones", "components/graphics-cards",
            "tv-av/tvs", "networking/routers", "cameras/cameras"]
os.chdir("datas/")
try:
    for cat in cat_list:   
        # Clear previous category data
        product_names, product_prices, product_specs, product_features, product_categories = [], [], [], [], []     
        # Scrape all pages
        base_url = f"https://www.pbtech.co.nz/category/{cat}/shop-all"

        # Load first page and get total page count
        driver.get(base_url)
        total_pages = get_total_pages()
        print(f"Found {total_pages} pages to scrape")
        
        scrape_page(base_url)  # First page
        
        for page_num in range(2, total_pages + 1):
            scrape_page(f"{base_url}?pg={page_num}#sortGroupForm")
        
        
        
        os.makedirs(f"{cat}", exist_ok=True)
        
        pd.DataFrame({
            'Product Name': product_names,
            'Category': cat,
            'Specification': product_specs,
            'Price': product_prices,
            'Detailed Features': product_features
        }).to_json(f'pbtech_data_on_{datetime.datetime.now().strftime("%Y-%m-%d")}.json', index=False)
        
        print(f"Successfully scraped {len(product_names)} products")
    
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()
