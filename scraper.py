from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Setup Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
base_url = "https://www.pbtech.co.nz/category/computers/laptops/shop-all"

# Lists to store scraped data
product_names, product_prices, product_specs = [], [], []

# Function to scrape products from a single page
def scrape_page(url):
    driver.get(url)
    print(f"Scraping: {url}")
    time.sleep(2)  # Brief wait for page load
    
    # Find all product containers
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div"))
    )
    product_containers = driver.find_elements(By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div")
    print(f"Found {len(product_containers)} products")
    
    for container in product_containers:
        try:
            # Extract product details
            name = container.find_element(By.CSS_SELECTOR, ".card-item-header a h2").text.strip()
            spec = container.find_element(By.CSS_SELECTOR, ".card-item-header a h3").text.strip()
            
            # JavaScript to extract price
            script = """
            const container = arguments[0];
            const priceContainer = container.querySelector('.item-price-amount');
            if (!priceContainer) return 'Price not found';
            
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
            
            # Store the data
            product_names.append(name)
            product_prices.append(price)
            product_specs.append(spec)
            
            print(f"Scraped: {name} - {price}")
        except Exception as e:
            print(f"Error scraping product: {e}")

# Function to get the total number of pages
def get_total_pages():
    # Try the specific selector first
    last_page_selector = "#mainCatList > div.products_list_wrapper.js-products-list-wrapper.expanded_list.none-swiper.w-100 > div > div.row.w-100.mx-0.pt-3 > div > div > div > ul > li:nth-child(5) > a > span"
    
    try:
        last_page_element = WebDriverWait(driver, 5).until(
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
try:
    # Load first page and get total page count
    driver.get(base_url)
    total_pages = get_total_pages()
    print(f"Found {total_pages} pages to scrape")
    
    # Scrape all pages
    scrape_page(base_url)  # First page
    
    for page_num in range(2, total_pages + 1):
        scrape_page(f"{base_url}?pg={page_num}#sortGroupForm")
        time.sleep(1)  # Small delay between pages
    
    # Save results
    pd.DataFrame({
        'Product Name': product_names,
        'Specification': product_specs,
        'Price': product_prices
    }).to_csv('pbtech_products.csv', index=False)
    
    print(f"Successfully scraped {len(product_names)} products")
    
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    driver.quit()