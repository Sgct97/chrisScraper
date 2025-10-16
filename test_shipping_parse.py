"""
Test if the scraper correctly parses shipping estimates for products that have them.
"""
import asyncio
from scrapers.target import TargetScraper
from config import CONFIG
from database import Database
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from proxy_manager import ProxyManager

async def test():
    config = CONFIG
    database = Database('test_shipping.db')
    browser_manager = BrowserManager(config)
    rate_limiter = RateLimiter(config)
    proxy_manager = ProxyManager(config)
    
    scraper = TargetScraper(config, database, browser_manager, rate_limiter, proxy_manager)
    
    # Test product 93138910 which HAS shipping services in the API
    tcin = '93138910'
    url = f'https://www.target.com/p/A-{tcin}'
    
    print(f"Testing TCIN {tcin} which has shipping service data...")
    result = await scraper.scrape_product(url, tcin)
    
    if result:
        print(f"\n[SUCCESS]")
        print(f"  Title: {result.get('title', 'N/A')[:60]}...")
        print(f"  Price: ${result.get('price_current', 'N/A')}")
        print(f"  Shipping Cost: ${result.get('shipping_cost', 'N/A')}")
        print(f"  Shipping Estimate: {result.get('shipping_estimate', 'N/A')}")
        
        if result.get('shipping_estimate'):
            print(f"\n✓ Shipping estimate is being captured!")
        else:
            print(f"\n✗ Shipping estimate is still N/A")
    else:
        print("[FAILED] No result")

if __name__ == '__main__':
    asyncio.run(test())

