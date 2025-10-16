"""
Test the fixed Target scraper with real products.
"""
import asyncio
import sys
from scrapers.target import TargetScraper
from config import CONFIG
from database import Database
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from proxy_manager import ProxyManager

async def test_scraper():
    """Test the fixed scraper."""
    
    # Initialize components
    config = CONFIG
    database = Database('test_products.db')
    browser_manager = BrowserManager(config)
    rate_limiter = RateLimiter(config)
    proxy_manager = ProxyManager(config)
    
    scraper = TargetScraper(config, database, browser_manager, rate_limiter, proxy_manager)
    
    # Test products from sitemap
    test_products = [
        {'tcin': '1000000076', 'url': 'https://www.target.com/p/A-1000000076'},
        {'tcin': '1000000299', 'url': 'https://www.target.com/p/A-1000000299'},
        {'tcin': '93138910', 'url': 'https://www.target.com/p/A-93138910'},
        {'tcin': '1000006800', 'url': 'https://www.target.com/p/A-1000006800'},
        {'tcin': '1000003033', 'url': 'https://www.target.com/p/A-1000003033'},
    ]
    
    print("="*80)
    print("Testing Fixed Target Scraper")
    print("="*80)
    
    success = 0
    fail = 0
    
    for product in test_products:
        tcin = product['tcin']
        url = product['url']
        
        print(f"\n[Testing] TCIN: {tcin}")
        print(f"  URL: {url}")
        
        try:
            result = await scraper.scrape_product(url, tcin)
            
            if result and result.get('status') != 'needs_browser':
                # Check required fields
                has_title = bool(result.get('title'))
                has_price = result.get('price_current') is not None
                has_brand = bool(result.get('brand'))
                
                print(f"  [SUCCESS]")
                print(f"    Title: {result.get('title', 'N/A')[:60]}...")
                print(f"    Brand: {result.get('brand', 'N/A')}")
                print(f"    Price: ${result.get('price_current', 'N/A')}")
                print(f"    Availability: {result.get('availability', 'N/A')}")
                
                if has_title and has_price:
                    success += 1
                    print(f"    [OK] Has required data")
                else:
                    fail += 1
                    print(f"    [MISSING] Missing required fields")
            elif result and result.get('status') == 'needs_browser':
                print(f"  [NEEDS BROWSER] API returned no data - might be marketplace product")
                fail += 1
            else:
                print(f"  [FAILED] No result returned")
                fail += 1
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            fail += 1
        
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Success: {success}/{len(test_products)} ({success*100//len(test_products)}%)")
    print(f"Failed: {fail}/{len(test_products)} ({fail*100//len(test_products)}%)")
    
    if success >= 4:  # At least 80% success
        print("\n[OK] Scraper is working!")
        return True
    else:
        print("\n[FAIL] Scraper needs more work")
        return False

if __name__ == '__main__':
    result = asyncio.run(test_scraper())
    sys.exit(0 if result else 1)

