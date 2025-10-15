import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from bs4 import BeautifulSoup
import re

async def check_catalog_size():
    """Check if we can find total product count from the website"""
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    
    await browser_mgr.initialize()
    
    # Try different approaches
    test_urls = [
        'https://www.costco.com/all-products.html',
        'https://www.costco.com/grocery-household.html',
        'https://www.costco.com/appliances.html',
    ]
    
    for url in test_urls:
        print(f"\nTrying: {url}")
        try:
            import httpx
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
            
            async with httpx.AsyncClient(timeout=15, http2=False, headers=headers) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"  ✓ Loaded successfully")
                    
                    # Look for product count in page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Search for text like "1-24 of 1,234 products"
                    text = response.text
                    patterns = [
                        r'(\d{1,3}(?:,\d{3})*)\s+(?:products|items|results)',
                        r'of\s+(\d{1,3}(?:,\d{3})*)\s+(?:products|items|results)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            print(f"  Found counts: {matches}")
                    
                    break
                else:
                    print(f"  ✗ Status: {response.status_code}")
                    
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    await browser_mgr.cleanup()

asyncio.run(check_catalog_size())

