#!/usr/bin/env python3
"""
Quick test to validate setup before running full scrape.
Tests imports, database creation, and basic connectivity.
"""

import asyncio
import sys


async def test_setup():
    """Run setup validation tests."""
    print("=" * 80)
    print("SETUP VALIDATION")
    print("=" * 80 + "\n")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Import core modules
    print("Test 1: Importing core modules...")
    tests_total += 1
    try:
        from config import CONFIG, RETAILERS
        from database import Database
        from proxy_manager import ProxyManager
        from browser_manager import BrowserManager
        from rate_limiter import RateLimiter
        from utils import ensure_directory
        from exporter import Exporter
        print("  ✓ Core modules imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Failed to import core modules: {e}")
        return False
    
    # Test 2: Import scrapers
    print("\nTest 2: Importing scraper modules...")
    tests_total += 1
    try:
        from scrapers import TargetScraper, CostcoScraper, HomeGoodsScraper, TJMaxxScraper
        print("  ✓ Scraper modules imported successfully")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Failed to import scrapers: {e}")
        return False
    
    # Test 3: Database initialization
    print("\nTest 3: Initializing database...")
    tests_total += 1
    try:
        db = Database('test_scraper.db')
        print("  ✓ Database initialized successfully")
        tests_passed += 1
        
        # Cleanup test database
        import os
        if os.path.exists('test_scraper.db'):
            os.remove('test_scraper.db')
    except Exception as e:
        print(f"  ✗ Failed to initialize database: {e}")
    
    # Test 4: Proxy manager
    print("\nTest 4: Initializing proxy manager...")
    tests_total += 1
    try:
        proxy_mgr = ProxyManager(CONFIG)
        stats = proxy_mgr.get_stats()
        print(f"  ✓ Proxy manager initialized (enabled: {proxy_mgr.is_enabled()})")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Failed to initialize proxy manager: {e}")
    
    # Test 5: Browser manager
    print("\nTest 5: Testing browser manager...")
    tests_total += 1
    try:
        browser_mgr = BrowserManager()
        await browser_mgr.initialize()
        context = await browser_mgr.create_context('test')
        await browser_mgr.close_context(context)
        await browser_mgr.cleanup()
        print("  ✓ Browser manager working")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Browser manager failed: {e}")
        print("  → Make sure Playwright is installed: playwright install chromium")
    
    # Test 6: Directory creation
    print("\nTest 6: Creating output directories...")
    tests_total += 1
    try:
        ensure_directory('exports')
        ensure_directory('manifests')
        print("  ✓ Directories created")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Failed to create directories: {e}")
    
    # Test 7: Configuration check
    print("\nTest 7: Checking configuration...")
    tests_total += 1
    try:
        from config import CONFIG
        print(f"  ZIP Code: {CONFIG['zip_code']}")
        print(f"  Concurrency: {CONFIG['concurrency']}")
        print(f"  Proxy enabled: {CONFIG['proxy']['enabled']}")
        print(f"  Database path: {CONFIG['database_path']}")
        print("  ✓ Configuration loaded")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Configuration check failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"RESULTS: {tests_passed}/{tests_total} tests passed")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("\n✓ All tests passed! Ready to run scraper.")
        print("\nNext steps:")
        print("  1. Review config.py and update ZIP code if needed")
        print("  2. Add proxy credentials if you have them")
        print("  3. Run test mode: python main.py --test")
        print("  4. Run full scrape: python main.py")
        return True
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed.")
        print("Please fix the issues above before running the scraper.")
        return False


if __name__ == '__main__':
    try:
        success = asyncio.run(test_setup())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

