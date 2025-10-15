import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from bs4 import BeautifulSoup
import json

async def debug_target():
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    
    await browser_mgr.initialize()
    context = await browser_mgr.create_context('target')
    page = await browser_mgr.new_page(context)
    
    url = 'https://www.target.com/p/unique-loom-outdoor-botanical-gate-border-woven-area-rug/-/A-1000006800'
    
    print(f"Loading: {url}\n")
    await page.goto(url, wait_until='domcontentloaded', timeout=30000)
    await page.wait_for_timeout(2000)
    
    html = await page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for __NEXT_DATA__
    script = soup.find('script', id='__NEXT_DATA__')
    if script and script.string:
        print("✓ Found __NEXT_DATA__\n")
        data = json.loads(script.string)
        
        # Navigate structure
        props = data.get('props', {})
        page_props = props.get('pageProps', {})
        
        print("Top-level keys in pageProps:")
        print(f"  {list(page_props.keys())}\n")
        
        product = page_props.get('product') or page_props.get('initialData', {}).get('product')
        if product:
            print("✓ Found product data")
            print(f"  Keys: {list(product.keys())[:20]}\n")
            
            print(f"Title: {product.get('title')}")
            print(f"Brand: {product.get('brand')}")
            print(f"Price: {product.get('price')}")
            print(f"Available: {product.get('available')}")
        else:
            print("✗ No product data found in expected locations")
            print(f"\nSaving full JSON to debug_target_data.json")
            with open('debug_target_data.json', 'w') as f:
                json.dump(data, f, indent=2)
    else:
        print("✗ No __NEXT_DATA__ found\n")
        print("Page title:", soup.find('title'))
        print(f"Page length: {len(html)} chars")
    
    await browser_mgr.cleanup()

asyncio.run(debug_target())

