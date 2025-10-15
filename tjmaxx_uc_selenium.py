import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import re
import random

def uc_enumeration():
    """Use undetected-chromedriver to bypass TJ Maxx detection"""
    
    print("Launching undetected Chrome...\n")
    
    # Create undetected chrome instance
    options = uc.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    
    driver = uc.Chrome(options=options, version_main=None)
    
    all_product_ids = set()
    all_urls = set()
    
    def get_products():
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        new = 0
        for link in soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x):
            m = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if m and m.group(1) not in all_product_ids:
                all_product_ids.add(m.group(1))
                new += 1
        return new
    
    def check_if_blocked():
        return 'Something went wrong' in driver.page_source or 'Challenge Validation' in driver.page_source
    
    try:
        print("Loading main page...")
        driver.get('https://tjmaxx.tjx.com/store/shop')
        time.sleep(5)
        
        if check_if_blocked():
            print("BLOCKED on main page!")
            return
        
        count = get_products()
        print(f"Main page: {count} products (total: {len(all_product_ids)})\n")
        
        # Get all URLs
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/store/shop/' in href:
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                href = href.split('?')[0]
                all_urls.add(href)
        
        urls_list = list(all_urls)
        print(f"Found {len(urls_list)} URLs to crawl\n")
        
        # Crawl with delays
        for i, url in enumerate(urls_list):
            name = url.split('/')[-1][:40]
            print(f"[{i+1}/{len(urls_list)}] {name}...", end=" ", flush=True)
            
            try:
                driver.get(url)
                time.sleep(random.uniform(2, 5))
                
                if check_if_blocked():
                    print("BLOCKED")
                    print(f"\nGot blocked after {i+1} pages")
                    break
                
                new = get_products()
                print(f"{new} new (total: {len(all_product_ids)})")
                
            except Exception as e:
                print(f"error")
            
            if (i + 1) % 25 == 0:
                print(f"\n>>> {len(all_product_ids):,} products <<<\n")
        
        print(f"\n{'='*60}")
        print(f"URLs crawled: {i+1}/{len(urls_list)}")
        print(f"Total products: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    uc_enumeration()

