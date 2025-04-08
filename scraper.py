from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import time

# Set up the ChromeDriver service using webdriver_manager
service = Service(executable_path=ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

print("Im on the website")

# Navigate to the PB Tech business laptops page
driver.get("https://www.pbtech.co.nz/category/computers/laptops/business-laptops")

# Wait for the page to load
time.sleep(3)

# Lists to store scraped data
product_names = []
product_prices = []

try:
    # Find all product containers
    product_containers = driver.find_elements(By.CSS_SELECTOR, "#mainCatList .row.w-100.mx-0.ms-xl-2.me-xl-1 > div")
    print(f"Found {len(product_containers)} products")
    
    for container in product_containers:
        try:
            # Get product name using the provided selector
            name_element = container.find_element(By.CSS_SELECTOR, 
                "div.col.col-md-12.col-xl.order-2.order-md-1.order-xl-2.expanded-details.product-details-info > div.overflow-hidden.card-item-header.content-box > a")
            product_name = name_element.text.strip()
            
            # Get price using the provided selector
            price_dollar_element = container.find_element(By.CSS_SELECTOR, 
                "div.col.col-md-12.col-xl.order-2.order-md-1.order-xl-2.expanded-details.product-details-info > div.d-md-none.col-12.col-xl-3.col-override.py-2.px-3.border-box.price-block-placeholder.d-flex.flex-column.justify-content-center.justify-content-md-end.order-3 > div.priceClass.position-relative > div.item-price-block.text-end.d-flex.flex-column.align-items-end.mb-0 > div.item-price-amount.overflow-hidden.fw-bold.d-flex.justify-content-end.priceClass-pb > div.ginc > div > span.price-dollar.hide-plain")
            
            price_cent_element = container.find_element(By.CSS_SELECTOR,
                    "div.col.col-md-12.col-xl.order-2.order-md-1.order-xl-2.expanded-details.product-details-info > div.d-md-none.col-12.col-xl-3.col-override.py-2.px-3.border-box.price-block-placeholder.d-flex.flex-column.justify-content-center.justify-content-md-end.order-3 > div.priceClass.position-relative > div.item-price-block.text-end.d-flex.flex-column.align-items-end.mb-0 > div.item-price-amount.overflow-hidden.fw-bold.d-flex.justify-content-end.priceClass-pb > div.ginc > div > span.price-cents.hide-plain")
            product_dollar_price = price_dollar_element.text.strip()
            product_cent_price = price_cent_element.text.strip()
            product_price = f"{product_dollar_price}.{product_cent_price}"
            
            # Store the data
            product_names.append(product_name)
            product_prices.append(product_price)
            
            print(f"Scraped: {product_name} - {product_price}")
        
        except NoSuchElementException:
            print("Couldn't extract data for a product, skipping...")
            continue
    
    # Create a DataFrame with the scraped data
    products_df = pd.DataFrame({
        'Product Name': product_names,
        'Price': product_prices
    })
    
    # Save to CSV
    products_df.to_csv('pbtech_products.csv', index=False)
    print(f"Successfully scraped {len(products_df)} products and saved to 'pbtech_products.csv'")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Clean up
    driver.quit()
