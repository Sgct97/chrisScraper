import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from bs4 import BeautifulSoup

async def test_costco_categories():
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    
    await browser_mgr.initialize()
    
    # Try main page and look for categories
    urls_to_try = [
        'https://www.costco.com',
        'https://www.costco.com/warehouse-hot-buys.html',
        'https://www.costco.com/appliances.html',
    ]
    
    for url in urls_to_try:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print(f"{'='*60}")
        
        try:
            context = await browser_mgr.create_context('costco')
            page = await browser_mgr.new_page(context)
            
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            
            if response:
                print(f"✓ Status: {response.status}")
                content = await page.content()
                print(f"✓ Content length: {len(content)} chars")
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for product links
                product_links = soup.find_all('a', href=lambda x: x and '.product.' in x)
                print(f"✓ Found {len(product_links)} potential product links")
                
                if product_links:
                    print("\nSample product URLs:")
                    for i, link in enumerate(product_links[:5]):
                        print(f"  {i+1}. {link.get('href')}")
                
                # Look for category links
                cat_links = soup.find_all('a', href=lambda x: x and ('.html' in x or 'category' in x.lower()))
                print(f"✓ Found {len(cat_links)} potential category links")
                
                break  # If successful, stop trying
            
            await browser_mgr.close_context(context)
            
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            continue
    
    await browser_mgr.cleanup()

asyncio.run(test_costco_categories())

