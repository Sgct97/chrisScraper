import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from database import Database
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from scrapers.target import TargetScraper

async def test():
    db = Database('test.db')
    proxy_mgr = ProxyManager(CONFIG)
    browser_mgr = BrowserManager(proxy_mgr)
    rate_limiter = RateLimiter(CONFIG)
    
    scraper = TargetScraper(CONFIG, db, browser_mgr, rate_limiter, proxy_mgr)
    
    # Test sitemap fetch
    print("Testing sitemap fetch...")
    html = await scraper._fetch_gzipped_sitemap(scraper.sitemap_url)
    
    if html:
        print(f"✓ Fetched {len(html)} chars")
        print(f"\nFirst 500 chars:")
        print(html[:500])
    else:
        print("✗ Failed to fetch")

asyncio.run(test())

