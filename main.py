#!/usr/bin/env python3
"""
Main orchestrator for retail scraping.
Runs enumeration, scraping, validation, and export.
"""

import asyncio
from datetime import datetime
from typing import List, Dict
import sys
import json
import os

from config import CONFIG, RETAILERS
from database import Database
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from utils import ensure_directory, export_manifest, format_timestamp, ProgressTracker
from exporter import Exporter

from scrapers import TargetScraper, CostcoScraper, HomeGoodsScraper, TJMaxxScraper

# Import Spot monitoring if available (only on AWS)
try:
    from spot_monitor import run_with_spot_monitoring, GracefulShutdown
    SPOT_MONITORING_AVAILABLE = True
except ImportError:
    SPOT_MONITORING_AVAILABLE = False


class RetailScraper:
    """Main scraper orchestrator."""
    
    def __init__(self):
        self.config = CONFIG
        self.database = Database(CONFIG['database_path'])
        self.proxy_manager = ProxyManager(CONFIG)
        self.browser_manager = BrowserManager(self.proxy_manager)
        self.rate_limiter = RateLimiter(CONFIG)
        self.exporter = Exporter(CONFIG, self.database)
        
        # Initialize scrapers
        self.scrapers = {
            'target': TargetScraper(CONFIG, self.database, self.browser_manager, self.rate_limiter, self.proxy_manager),
            'costco': CostcoScraper(CONFIG, self.database, self.browser_manager, self.rate_limiter, self.proxy_manager),
            'homegoods': HomeGoodsScraper(CONFIG, self.database, self.browser_manager, self.rate_limiter, self.proxy_manager),
            'tjmaxx': TJMaxxScraper(CONFIG, self.database, self.browser_manager, self.rate_limiter, self.proxy_manager),
        }
        
        self.retailer_runs = {}  # Track scrape run IDs
    
    async def cleanup(self):
        """Graceful cleanup on shutdown (for Spot interruptions)."""
        print("\n[CLEANUP] Closing browser connections and saving state...")
        try:
            await self.browser_manager.cleanup()
            print("[CLEANUP] Browser manager closed")
            
            # Export current data
            print("[CLEANUP] Exporting current progress...")
            for retailer in self.retailer_runs.keys():
                try:
                    self.exporter.export_retailer_data(retailer, live_update=True)
                    print(f"[CLEANUP] Exported {retailer} data")
                except Exception as e:
                    print(f"[CLEANUP] Failed to export {retailer}: {e}")
            
            print("[CLEANUP] ✓ Cleanup complete. Database saved. Safe to terminate.")
        except Exception as e:
            print(f"[CLEANUP] Error during cleanup: {e}")
    
    def _get_already_scraped(self, retailer: str) -> set:
        """Get set of product IDs already scraped for this retailer."""
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id FROM products 
                WHERE retailer = ? AND status = 'success'
            """, (retailer,))
            return {row[0] for row in cursor.fetchall()}
    
    async def run_enumeration(self, retailer: str) -> str:
        """Run enumeration for a retailer using streaming (memory-efficient).
        Returns path to manifest file instead of products list to save memory."""
        print(f"\n{'='*80}")
        print(f"ENUMERATION: {retailer.upper()}")
        print(f"{'='*80}")
        
        scraper = self.scrapers[retailer]
        
        # Create manifest file for streaming writes
        manifest_path = ensure_directory(self.config['manifests_dir']) / f"manifest_{retailer}_{format_timestamp()}.csv"
        
        # Deduplicate by product_id (keep only set of IDs in memory, not full dicts)
        seen = set()
        unique_count = 0
        
        # Write manifest incrementally as we enumerate (TRUE STREAMING)
        import csv
        import hashlib
        hasher = hashlib.sha256()
        
        with open(manifest_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['url', 'hash'])
            
            # Consume async generator - products yielded one-by-one
            async for product in scraper.enumerate_products():
                if product['product_id'] not in seen:
                    seen.add(product['product_id'])
                    unique_count += 1
                    url = product['product_url']
                    # Calculate hash for this URL
                    hasher.update(url.encode('utf-8'))
                    writer.writerow([url, ''])
        
        # Update final hash in database
        manifest_hash = hasher.hexdigest()[:16]
        
        print(f"\n✓ Total unique products: {unique_count:,}")
        print(f"✓ Manifest written to: {manifest_path}")
        
        return str(manifest_path)
    
    async def scrape_products_from_manifest(self, retailer: str, manifest_path: str, resume: bool = True, skip_count: int = 0, max_items: int = None):
        """Scrape products from manifest in batches to avoid OOM."""
        import csv
        import re
        
        BATCH_SIZE = 10000  # Process 10K products at a time
        
        # Count total products in manifest
        with open(manifest_path, 'r') as f:
            total_count = sum(1 for _ in csv.reader(f)) - 1  # Subtract header
        
        print(f"✓ Total products in manifest: {total_count:,}")
        
        # Get already scraped products for resume
        already_scraped = set()
        if resume:
            already_scraped = self._get_already_scraped(retailer)
            if already_scraped:
                print(f"✓ Resume mode: {len(already_scraped):,} products already scraped")
        
        # Create scrape run
        run_id = self.database.create_scrape_run(retailer, self.proxy_manager.is_enabled())
        self.retailer_runs[retailer] = run_id
        
        scraper = self.scrapers[retailer]
        progress = ProgressTracker(total_count - skip_count, retailer)
        
        # Get concurrency limit for this retailer
        concurrency = self.config['concurrency'].get(retailer, 10)
        
        # Process manifest in batches
        batch_num = 0
        total_processed = 0
        
        with open(manifest_path, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            batch = []
            for idx, row in enumerate(reader):
                # Skip if before skip_count
                if idx < skip_count:
                    continue
                
                # Stop if max_items reached
                if max_items and total_processed >= max_items:
                    break
                
                if not row or not row[0]:
                    continue
                
                url = row[0]
                
                # Extract product ID from URL
                if retailer == 'target':
                    match = re.search(r'/A-(\d+)', url)
                elif retailer == 'costco':
                    match = re.search(r'\.product\.(\d+)\.html', url)
                else:
                    match = None
                
                product_id = match.group(1) if match else url.split('/')[-1]
                
                # Skip if already scraped
                if resume and product_id in already_scraped:
                    continue
                
                batch.append({
                    'product_id': product_id,
                    'product_url': url,
                    'method': 'manifest'
                })
                
                # Process batch when it reaches BATCH_SIZE
                if len(batch) >= BATCH_SIZE:
                    batch_num += 1
                    print(f"\n{'='*60}")
                    print(f"Processing batch {batch_num} ({len(batch):,} products)")
                    print(f"{'='*60}")
                    
                    await self._scrape_batch(scraper, batch, run_id, progress, concurrency, retailer)
                    total_processed += len(batch)
                    batch = []  # Clear batch from memory
            
            # Process remaining products in last batch
            if batch:
                batch_num += 1
                print(f"\n{'='*60}")
                print(f"Processing final batch {batch_num} ({len(batch):,} products)")
                print(f"{'='*60}")
                
                await self._scrape_batch(scraper, batch, run_id, progress, concurrency)
                total_processed += len(batch)
        
        # Update run stats
        stats = progress.get_stats()
        self.database.update_scrape_run(
            run_id,
            completed_at=datetime.now(),
            total_attempted=stats['completed'],
            total_success=stats['success'],
            total_failed=stats['failed'] + stats['blocked'] + stats['not_found'],
            block_rate_percent=stats['block_rate_percent']
        )
        
        print(f"\n\n✓ Scraping complete for {retailer}")
        print(f"  Total processed: {total_processed:,}")
        print(f"  Success: {stats['success']:,}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Blocked: {stats['blocked']}")
        print(f"  Not Found: {stats['not_found']}")
    
    async def _scrape_batch(self, scraper, batch: List[Dict[str, str]], run_id: int, progress: ProgressTracker, concurrency: int, retailer: str):
        """Scrape a single batch of products."""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_limit(product_info):
            async with semaphore:
                return await self._scrape_single_product(
                    scraper, 
                    product_info, 
                    run_id, 
                    progress
                )
        
        tasks = [scrape_with_limit(p) for p in batch]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Export progress every 1000 items (live update - overwrites same file)
        if not hasattr(self, '_items_since_export'):
            self._items_since_export = 0
        
        self._items_since_export += len(batch)
        
        if self._items_since_export >= 1000:
            self.exporter.export_retailer_data(retailer, live_update=True)
            self._items_since_export = 0
    
    async def scrape_products(self, retailer: str, products: List[Dict[str, str]], resume: bool = True, max_items: int = None):
        """Scrape all products for a retailer."""
        print(f"\n{'='*80}")
        print(f"SCRAPING: {retailer.upper()}")
        print(f"{'='*80}\n")
        
        # Check for already scraped products (resume capability)
        if resume:
            already_scraped = self._get_already_scraped(retailer)
            if already_scraped:
                original_count = len(products)
                products = [p for p in products if p['product_id'] not in already_scraped]
                skipped = original_count - len(products)
                if skipped > 0:
                    print(f"✓ Resume mode: Skipping {skipped:,} already scraped products")
                    print(f"  Remaining to scrape: {len(products):,}\n")
        
        # Apply max_items limit if specified (for testing)
        if max_items:
            print(f"[TEST MODE] Limiting to {max_items} products\n")
            products = products[:max_items]
        
        if not products:
            print(f"✓ All products already scraped for {retailer}!\n")
            return
        
        # Create scrape run
        run_id = self.database.create_scrape_run(retailer, self.proxy_manager.is_enabled())
        self.retailer_runs[retailer] = run_id
        
        scraper = self.scrapers[retailer]
        progress = ProgressTracker(len(products), retailer)
        
        # Get concurrency limit for this retailer
        concurrency = self.config['concurrency'].get(retailer, 10)
        
        # Scrape with concurrency limit
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_limit(product_info):
            async with semaphore:
                return await self._scrape_single_product(
                    scraper, 
                    product_info, 
                    run_id, 
                    progress
                )
        
        # Process all products
        tasks = [scrape_with_limit(p) for p in products]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update run stats
        stats = progress.get_stats()
        self.database.update_scrape_run(
            run_id,
            completed_at=datetime.now(),
            total_attempted=stats['completed'],
            total_success=stats['success'],
            total_failed=stats['failed'] + stats['blocked'] + stats['not_found'],
            block_rate_percent=stats['block_rate_percent']
        )
        
        print(f"\n\n✓ Scraping complete for {retailer}")
        print(f"  Success: {stats['success']:,}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Blocked: {stats['blocked']}")
        print(f"  Not Found: {stats['not_found']}")
    
    async def _scrape_single_product(self, scraper, product_info: Dict, run_id: int, progress: ProgressTracker):
        """Scrape a single product with error handling."""
        product_url = product_info['product_url']
        product_id = product_info['product_id']
        retailer = scraper.retailer_name
        
        try:
            # Check if we're getting blocked too much - STOP if no proxy configured
            if self.proxy_manager.consecutive_failures >= 10:
                print(f"\n\n{'='*80}")
                print(f"⚠️  STOPPING: Too many consecutive failures ({self.proxy_manager.consecutive_failures})")
                print(f"{'='*80}")
                print(f"This usually means we're getting blocked by Target.")
                print(f"")
                print(f"Options:")
                print(f"  1. Add proxies to config.py and restart")
                print(f"  2. Wait 30-60 minutes and try lower concurrency")
                print(f"")
                print(f"Progress saved! Run again to resume.")
                print(f"{'='*80}\n")
                # Exit gracefully - scraper will resume from database on restart
                sys.exit(1)
            
            # Pause on moderate failures
            if self.proxy_manager.consecutive_failures >= 5:
                backoff_seconds = min(60, 5 * (2 ** (self.proxy_manager.consecutive_failures - 5)))
                print(f"\n[WARNING] High failure rate ({self.proxy_manager.consecutive_failures} consecutive)! Pausing {backoff_seconds}s...\n")
                await asyncio.sleep(backoff_seconds)
            
            # Check if we should enable proxy (only if proxy is configured)
            if self.proxy_manager.should_enable_proxy() and CONFIG['proxy'].get('datacenter_pool'):
                print(f"\n\n[SWITCHING] Block rate threshold exceeded! Switching to proxy mode...")
                self.proxy_manager.enable_proxy(reason="Block rate threshold exceeded")
                print(f"[OK] Now using proxy. Resuming scraping...\n")
            
            # Scrape product
            product_data = await scraper.scrape_product(product_url, product_id)
            
            if not product_data:
                # Failed to scrape
                progress.record_failure('failed')
                self.database.log_error(
                    retailer, product_url, 'scrape_failed', 
                    'Failed to fetch or parse product', run_id
                )
            elif product_data.get('status') == 'not_found':
                # 404
                progress.record_failure('not_found')
            else:
                # Success
                product_data['scrape_run_id'] = run_id
                self.database.insert_product(product_data)
                
                # Print sample product every 100 items to verify data quality
                if progress.successful % 100 == 1:  # Print first and every 100th
                    print(f"\n{'='*80}")
                    print(f"SAMPLE PRODUCT #{progress.successful}")
                    print(f"{'='*80}")
                    print(f"ID: {product_data.get('product_id')}")
                    print(f"Title: {product_data.get('title', 'MISSING')[:80]}")
                    print(f"Brand: {product_data.get('brand', 'MISSING')}")
                    print(f"Price: ${product_data.get('price_current', 'MISSING')}")
                    print(f"Compare At: ${product_data.get('price_compare_at', 'N/A')}")
                    print(f"Category: {product_data.get('category', 'MISSING')}")
                    print(f"Availability: {product_data.get('availability', 'MISSING')}")
                    print(f"Shipping: ${product_data.get('shipping_cost', 'MISSING')} - {product_data.get('shipping_estimate', 'MISSING')}")
                    print(f"Images: {len(product_data.get('image_urls', '[]').split(',')) if product_data.get('image_urls') else 0} images")
                    print(f"Rating: {product_data.get('ratings_average', 'N/A')} ({product_data.get('ratings_count', 0)} reviews)")
                    print(f"Description: {(product_data.get('description', 'MISSING') or '')[:100]}...")
                    print(f"{'='*80}\n")
                
                # Check for missing critical fields and track for re-scraping
                missing_fields = []
                critical_fields = {
                    'price_current': 'price',
                    'title': 'title',
                    'brand': 'brand',
                    'shipping_estimate': 'shipping_estimate',
                    'description': 'description'
                }
                
                for field, display_name in critical_fields.items():
                    if not product_data.get(field):
                        missing_fields.append(display_name)
                
                # Log if ANY critical field is missing
                if missing_fields:
                    self.database.log_incomplete_product(
                        product_data.get('product_id'),
                        retailer,
                        product_url,
                        missing_fields,
                        run_id
                    )
                
                progress.record_success()
            
            # Print progress
            mode = "Proxy Mode" if self.proxy_manager.is_enabled() else "Home Network"
            progress.print_progress(mode)
            
        except Exception as e:
            progress.record_failure('failed')
            self.database.log_error(
                retailer, product_url, 'exception', 
                str(e), run_id
            )
            # CRITICAL: Add delay to prevent runaway error loops
            await asyncio.sleep(1)
    
    async def run_enumeration_only(self, retailers: List[str] = None):
        """Run enumeration only (no scraping) to prove completeness."""
        if retailers is None:
            retailers = ['target', 'costco', 'homegoods', 'tjmaxx']
        
        print(f"\n{'='*80}")
        print("RETAIL SCRAPER - ENUMERATION ONLY MODE")
        print(f"{'='*80}")
        print(f"Retailers: {', '.join(retailers)}")
        print(f"This will discover all products and prove completeness WITHOUT scraping.")
        print(f"{'='*80}\n")
        
        # Initialize browser (needed for some enumeration methods)
        await self.browser_manager.initialize()
        
        all_counts = {}
        
        # Run enumeration for each retailer
        for retailer in retailers:
            try:
                manifest_path = await self.run_enumeration(retailer)
                # Count products in manifest
                import csv
                with open(manifest_path, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    count = sum(1 for row in reader if row and row[0])
                all_counts[retailer] = count
                
            except Exception as e:
                print(f"\n✗ Error enumerating {retailer}: {e}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        await self.browser_manager.cleanup()
        
        # Export completeness package
        print(f"\n{'='*80}")
        print("GENERATING COMPLETENESS REPORTS")
        print(f"{'='*80}\n")
        
        self.exporter.export_completeness_package()
        
        # Print summary
        print(f"\n{'='*80}")
        print("ENUMERATION SUMMARY")
        print(f"{'='*80}\n")
        
        total_products = 0
        for retailer, count in all_counts.items():
            print(f"{retailer.upper()}: {count:,} products discovered")
            total_products += count
        
        print(f"\nTOTAL ACROSS ALL RETAILERS: {total_products:,} products")
        print(f"\n{'='*80}")
        print("✓ ENUMERATION COMPLETE")
        print(f"{'='*80}")
        print("\nNext steps:")
        print("  1. Review manifests in manifests/ directory")
        print("  2. Check completeness_report.json for validation")
        print("  3. Run full scrape: python main.py")
        print()
    
    async def run_full_scrape(self, retailers: List[str] = None, resume: bool = True):
        """Run full scrape for specified retailers."""
        if retailers is None:
            retailers = ['target', 'costco', 'homegoods', 'tjmaxx']
        
        print(f"\n{'='*80}")
        print("RETAIL SCRAPER - INITIAL SCRAPE")
        print(f"{'='*80}")
        print(f"Retailers: {', '.join(retailers)}")
        print(f"Mode: Home Network (auto-escalate to proxy if blocked)")
        if resume:
            print(f"Resume: Enabled (will skip already scraped products)")
        else:
            print(f"Resume: Disabled (starting from scratch)")
        print(f"{'='*80}\n")
        
        # Initialize browser
        await self.browser_manager.initialize()
        
        # Run enumeration and scraping for each retailer
        for retailer in retailers:
            try:
                # Check if manifest exists
                import glob
                manifests = sorted(glob.glob(f"manifests/manifest_{retailer}_*.csv"))
                
                # Use manifest if: skip-enum flag OR (max-items set AND manifest exists)
                use_manifest = CONFIG.get('skip_enum') or (CONFIG.get('max_items') and manifests)
                
                if use_manifest and manifests:
                    manifest_path = manifests[-1]
                elif use_manifest and not manifests:
                    print(f"✗ No manifest found for {retailer}, run enumeration first")
                    continue
                else:
                    # Run enumeration and get manifest path
                    manifest_path = await self.run_enumeration(retailer)
                
                # Scrape in batches to avoid OOM (process manifest in chunks)
                skip_count = CONFIG.get('skip_products', 0)
                print(f"Processing products from manifest: {manifest_path}")
                if skip_count > 0:
                    print(f"  Skipping first {skip_count:,} products...")
                
                await self.scrape_products_from_manifest(
                    retailer, 
                    manifest_path, 
                    resume=resume, 
                    skip_count=skip_count,
                    max_items=CONFIG.get('max_items')
                )
                
            except Exception as e:
                print(f"\n✗ Error processing {retailer}: {e}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        await self.browser_manager.cleanup()
        
        # Export data
        print(f"\n{'='*80}")
        print("EXPORTING DATA")
        print(f"{'='*80}\n")
        
        self.exporter.export_all_retailers()
        self.exporter.export_completeness_package()
        self.exporter.export_coverage_matrix(self.retailer_runs)
        
        # Print summary
        self.exporter.print_summary(self.retailer_runs)
        
        # Print incomplete products summary
        print(f"\n{'='*80}")
        print("INCOMPLETE PRODUCTS (Need Re-scraping)")
        print(f"{'='*80}\n")
        
        for retailer in retailers:
            incomplete = self.database.get_incomplete_products(retailer=retailer)
            if incomplete:
                print(f"{retailer.upper()}: {len(incomplete):,} products missing data")
                # Count what fields are most commonly missing
                field_counts = {}
                for item in incomplete:
                    fields = json.loads(item['missing_fields'])
                    for field in fields:
                        field_counts[field] = field_counts.get(field, 0) + 1
                
                print(f"  Most common missing fields:")
                for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"    - {field}: {count:,} products")
            else:
                print(f"{retailer.upper()}: 0 products (all complete!)")
            print()
        
        print("To re-scrape incomplete products, run:")
        print("  python rescrape_incomplete.py --retailer target")
        
        print(f"\n{'='*80}")
        print("✓ SCRAPE COMPLETE")
        print(f"{'='*80}\n")


async def main():
    """Main entry point."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Retail Product Scraper')
    parser.add_argument('--retailers', nargs='+', 
                        choices=['target', 'costco', 'homegoods', 'tjmaxx'],
                        help='Specific retailers to scrape (default: all)')
    parser.add_argument('--test', action='store_true',
                        help='Run test mode with limited products')
    parser.add_argument('--enumerate-only', action='store_true',
                        help='Only run enumeration to prove completeness, skip scraping')
    parser.add_argument('--no-resume', action='store_true',
                        help='Start from scratch, ignore already scraped products')
    parser.add_argument('--max-items', type=int, default=None,
                        help='Maximum number of products to scrape per retailer (for testing)')
    parser.add_argument('--skip-enum', action='store_true',
                        help='Skip enumeration, use last manifest (for testing scraping only)')
    parser.add_argument('--skip', type=int, default=0,
                        help='Skip first N products from manifest (for testing different products)')
    
    args = parser.parse_args()
    
    # Update config from args
    if args.max_items:
        CONFIG['max_items'] = args.max_items
    if args.skip_enum:
        CONFIG['skip_enum'] = True
    if args.skip:
        CONFIG['skip_products'] = args.skip
    
    scraper = RetailScraper()
    
    if args.test:
        print("\n[TEST MODE] Limited enumeration for validation\n")
        # In test mode, scrapers will limit enumeration (already set in code with [:5], [:10] slices)
    
    # Check if we're on AWS Spot instance
    use_spot_monitoring = os.getenv('AWS_SPOT_INSTANCE', 'false').lower() == 'true'
    
    if use_spot_monitoring and SPOT_MONITORING_AVAILABLE:
        print("\n[AWS SPOT] Spot instance monitoring enabled")
        print("[AWS SPOT] Will gracefully shutdown on interruption warnings")
        print("[AWS SPOT] Progress is auto-saved - scraping will resume on restart\n")
    
    # Define the main scraping task
    async def scraping_task():
        if args.enumerate_only:
            await scraper.run_enumeration_only(retailers=args.retailers)
        else:
            resume = not args.no_resume
            await scraper.run_full_scrape(retailers=args.retailers, resume=resume)
    
    # Run with Spot monitoring if on AWS, otherwise run normally
    if use_spot_monitoring and SPOT_MONITORING_AVAILABLE:
        await run_with_spot_monitoring(scraping_task(), cleanup_callback=scraper.cleanup)
    else:
        await scraping_task()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScrape interrupted by user")
        sys.exit(0)

