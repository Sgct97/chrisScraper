import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from bs4 import BeautifulSoup

async def test_costco_with_browser():
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    
    await browser_mgr.initialize()
    
    url = 'https://www.costco.com/sitemap_lw_index.xml'
    print(f"Fetching with browser: {url}")
    
    try:
        context = await browser_mgr.create_context('costco')
        page = await browser_mgr.new_page(context)
        
        # Increase timeout and try
        response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        if response:
            print(f"Status: {response.status}")
            content = await page.content()
            print(f"Length: {len(content)} chars")
            
            soup = BeautifulSoup(content, 'xml')
            sitemaps = soup.find_all('sitemap')
            locs = soup.find_all('loc')
            
            print(f"Found {len(sitemaps)} sitemap tags")
            print(f"Found {len(locs)} loc tags")
            
            print("\nFirst 10 URLs:")
            for i, loc in enumerate(locs[:10]):
                print(f"  {i+1}. {loc.text.strip()}")
        
        await browser_mgr.close_context(context)
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    
    await browser_mgr.cleanup()

asyncio.run(test_costco_with_browser())

