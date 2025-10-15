import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager

async def test_site_with_browser(name, url, browser_mgr):
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    
    try:
        context = await browser_mgr.create_context(name.lower())
        page = await browser_mgr.new_page(context)
        
        print("  Navigating...")
        response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        
        if response:
            print(f"  ✓ Status: {response.status}")
            content = await page.content()
            print(f"  ✓ Content length: {len(content)} chars")
            
            # Show first 500 chars
            print(f"\n  First 500 chars:")
            print(f"  {content[:500]}")
        
        await browser_mgr.close_context(context)
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        return False

async def main():
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    
    await browser_mgr.initialize()
    
    # Test each site
    await test_site_with_browser("Costco", "https://www.costco.com/robots.txt", browser_mgr)
    await test_site_with_browser("HomeGoods", "https://www.homegoods.com", browser_mgr)
    await test_site_with_browser("TJ Maxx", "https://www.tjmaxx.com", browser_mgr)
    
    await browser_mgr.cleanup()

asyncio.run(main())

