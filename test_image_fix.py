"""
Test that image URLs are now being captured correctly as full URLs.
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
    database = Database('test_images.db')
    browser_manager = BrowserManager(config)
    rate_limiter = RateLimiter(config)
    proxy_manager = ProxyManager(config)
    
    scraper = TargetScraper(config, database, browser_manager, rate_limiter, proxy_manager)
    
    # Test with a known product
    test_products = [
        {'tcin': '93138910', 'url': 'https://www.target.com/p/A-93138910'},
        {'tcin': '1000006800', 'url': 'https://www.target.com/p/A-1000006800'},
    ]
    
    print("Testing image URL fix...\n")
    
    for product in test_products:
        tcin = product['tcin']
        url = product['url']
        
        print(f"Scraping TCIN: {tcin}")
        result = await scraper.scrape_product(url, tcin)
        
        if result:
            images = result.get('image_urls', [])
            print(f"  Title: {result.get('title', 'N/A')[:50]}")
            print(f"  Images found: {len(images) if images else 0}")
            
            if images:
                print(f"  Sample images:")
                for i, img in enumerate(images[:3], 1):
                    print(f"    {i}. {img}")
                    # Check if it's a full URL
                    if img.startswith('http'):
                        print(f"       [OK] Full URL")
                    else:
                        print(f"       [ERROR] Still just an ID!")
            else:
                print(f"  [WARNING] No images found")
        else:
            print(f"  [FAILED] Could not scrape")
        
        print()
        await asyncio.sleep(1)
    
    print("\n" + "="*60)
    print("Test complete!")

if __name__ == '__main__':
    asyncio.run(test())

