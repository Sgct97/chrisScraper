#!/usr/bin/env python3
"""Test specific known-good products."""

import asyncio
import sys
sys.path.insert(0, '.')

from scrapers.target import TargetScraper
from database import Database
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
import config

async def main():
    db = Database('test.db')
    proxy = ProxyManager(config.PROXY_CONFIG)
    browser = BrowserManager()
    limiter = RateLimiter()
    
    await browser.initialize()
    
    scraper = TargetScraper(db, proxy, browser, limiter)
    
    # Test with known-good products from middle of manifest
    test_products = [
        ('93138910', 'https://www.target.com/p/-/A-93138910'),  # Item locator - verified working
        ('93495209', 'https://www.target.com/p/-/A-93495209'),  # Item locator navy
        ('91304528', 'https://www.target.com/p/-/A-91304528'),  # Item locator
    ]
    
    success_count = 0
    for tcin, url in test_products:
        print(f"\nTesting {tcin}...")
        result = await scraper.scrape_product(url, tcin)
        
        if result and result.get('status') != 'not_found':
            print(f"  ✓ SUCCESS!")
            print(f"    Title: {result.get('title')}")
            print(f"    Price: ${result.get('price_current')}")
            print(f"    Brand: {result.get('brand')}")
            success_count += 1
        else:
            print(f"  ✗ FAILED - Status: {result.get('status') if result else 'None'}")
    
    print(f"\n{'='*80}")
    print(f"Results: {success_count}/{len(test_products)} successful")
    print(f"{'='*80}")
    
    await browser.cleanup()

asyncio.run(main())

