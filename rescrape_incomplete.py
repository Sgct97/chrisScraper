"""
Re-scrape products that were missing critical data fields.
This script uses browser fallback to get missing shipping estimates and other data.
"""
import asyncio
import argparse
from database import Database
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from proxy_manager import ProxyManager
from config import CONFIG
from scrapers.target import TargetScraper
import json

async def rescrape_incomplete(retailer: str, max_items: int = None):
    """Re-scrape incomplete products for a retailer."""
    
    database = Database(CONFIG['database_path'])
    browser_manager = BrowserManager(CONFIG)
    rate_limiter = RateLimiter(CONFIG)
    proxy_manager = ProxyManager(CONFIG)
    
    # Get incomplete products
    incomplete = database.get_incomplete_products(retailer=retailer, rescrape_attempted=False)
    
    if not incomplete:
        print(f"No incomplete products found for {retailer}")
        return
    
    print(f"\n{'='*80}")
    print(f"RE-SCRAPING INCOMPLETE PRODUCTS: {retailer.upper()}")
    print(f"{'='*80}")
    print(f"Total incomplete: {len(incomplete):,} products")
    
    if max_items:
        incomplete = incomplete[:max_items]
        print(f"Limited to: {max_items} products\n")
    
    # Initialize scraper
    if retailer == 'target':
        scraper = TargetScraper(CONFIG, database, browser_manager, rate_limiter, proxy_manager)
    else:
        print(f"Scraper for {retailer} not yet implemented")
        return
    
    await browser_manager.initialize()
    
    success = 0
    still_incomplete = 0
    
    for i, item in enumerate(incomplete, 1):
        product_id = item['product_id']
        product_url = item['product_url']
        missing_fields = json.loads(item['missing_fields'])
        
        print(f"\n[{i}/{len(incomplete)}] {product_id}")
        print(f"  Missing: {', '.join(missing_fields)}")
        print(f"  URL: {product_url}")
        
        try:
            # Force browser scraping for these products
            context = await browser_manager.create_context(retailer)
            page = await browser_manager.new_page(context)
            await page.goto(product_url, wait_until='networkidle', timeout=30000)
            
            # Use browser fallback parser
            result = await scraper._parse_browser_fallback_live(page, product_url, product_id)
            
            await browser_manager.close_context(context)
            
            if result:
                # Update database
                result['scrape_run_id'] = item['scrape_run_id']
                database.insert_product(result)
                
                # Check if still incomplete
                still_missing = []
                for field in ['price_current', 'title', 'brand', 'shipping_estimate', 'description']:
                    if not result.get(field):
                        still_missing.append(field)
                
                if still_missing:
                    print(f"  [PARTIAL] Still missing: {', '.join(still_missing)}")
                    still_incomplete += 1
                    # Update incomplete record
                    database.log_incomplete_product(product_id, retailer, product_url, still_missing, item['scrape_run_id'])
                else:
                    print(f"  [SUCCESS] All fields captured!")
                    success += 1
                    # Remove from incomplete table
                    with database.get_connection() as conn:
                        conn.execute("DELETE FROM incomplete_products WHERE product_id = ?", (product_id,))
                        conn.commit()
            else:
                print(f"  [FAILED] No result")
                still_incomplete += 1
                
        except Exception as e:
            print(f"  [ERROR] {e}")
            still_incomplete += 1
        
        await asyncio.sleep(2)  # Rate limit
    
    await browser_manager.cleanup()
    
    # Summary
    print(f"\n{'='*80}")
    print("RE-SCRAPE SUMMARY")
    print(f"{'='*80}")
    print(f"Attempted: {len(incomplete):,}")
    print(f"Now Complete: {success:,}")
    print(f"Still Incomplete: {still_incomplete:,}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Re-scrape incomplete products')
    parser.add_argument('--retailer', required=True, choices=['target', 'costco', 'homegoods', 'tjmaxx'],
                        help='Retailer to re-scrape')
    parser.add_argument('--max-items', type=int, default=None,
                        help='Maximum number of products to re-scrape (for testing)')
    
    args = parser.parse_args()
    
    asyncio.run(rescrape_incomplete(args.retailer, args.max_items))

