#!/usr/bin/env python3
"""
Main orchestrator for retail scraping.
Runs enumeration, scraping, validation, and export.
"""

import asyncio
from datetime import datetime
from typing import List, Dict
import sys

from config import CONFIG, RETAILERS
from database import Database
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from rate_limiter import RateLimiter
from utils import ensure_directory, export_manifest, format_timestamp, ProgressTracker
from exporter import Exporter

from scrapers import TargetScraper, CostcoScraper, HomeGoodsScraper, TJMaxxScraper


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
    
    def _get_already_scraped(self, retailer: str) -> set:
        """Get set of product IDs already scraped for this retailer."""
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id FROM products 
                WHERE retailer = ? AND status = 'success'
            """, (retailer,))
            return {row[0] for row in cursor.fetchall()}
    
    async def run_enumeration(self, retailer: str) -> List[Dict[str, str]]:
        """Run enumeration for a retailer using multiple methods."""
        print(f"\n{'='*80}")
        print(f"ENUMERATION: {retailer.upper()}")
        print(f"{'='*80}")
        
        scraper = self.scrapers[retailer]
        products = await scraper.enumerate_products()
        
        # Deduplicate by product_id
        seen = set()
        unique_products = []
        for product in products:
            if product['product_id'] not in seen:
                seen.add(product['product_id'])
                unique_products.append(product)
        
        print(f"\n✓ Total unique products: {len(unique_products):,}")
        
        # Export manifest
        urls = [p['product_url'] for p in unique_products]
        manifest_path = ensure_directory(self.config['manifests_dir']) / f"manifest_{retailer}_{format_timestamp()}.csv"
        manifest_hash = export_manifest(urls, str(manifest_path))
        
        return unique_products
    
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
            print(f"⚠️  TEST MODE: Limiting to {max_items} products\n")
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
            # Check if we should enable proxy
            if self.proxy_manager.should_enable_proxy():
                self.proxy_manager.enable_proxy(reason="Block rate threshold exceeded")
            
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
                products = await self.run_enumeration(retailer)
                all_counts[retailer] = len(products)
                
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
                    # Load from last manifest
                    print(f"Loading products from manifest: {manifests[-1]}")
                    import csv
                    products = []
                    with open(manifests[-1], 'r') as f:
                        # CSV has format: url,hash (each line is url,hash)
                        lines = f.readlines()[1:]  # Skip header
                        for line in lines:
                            parts = line.strip().split(',')
                            if len(parts) < 1:
                                continue
                            url = parts[0]
                            # Extract product ID from URL
                            import re
                            if retailer == 'target':
                                match = re.search(r'/A-(\d+)', url)
                            elif retailer == 'costco':
                                match = re.search(r'\.product\.(\d+)\.html', url)
                            else:
                                match = None
                            
                            product_id = match.group(1) if match else url.split('/')[-1]
                            products.append({
                                'product_id': product_id,
                                'product_url': url,
                                'method': 'manifest'
                            })
                    print(f"✓ Loaded {len(products):,} products from manifest\n")
                elif use_manifest and not manifests:
                    print(f"✗ No manifest found for {retailer}, run enumeration first")
                    continue
                else:
                    products = await self.run_enumeration(retailer)
                
                if not products:
                    print(f"⚠️  No products found for {retailer}, skipping scrape")
                    continue
                
                # Scraping
                max_items = CONFIG.get('max_items')
                await self.scrape_products(retailer, products, resume=resume, max_items=max_items)
                
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
    
    args = parser.parse_args()
    
    # Update config from args
    if args.max_items:
        CONFIG['max_items'] = args.max_items
    if args.skip_enum:
        CONFIG['skip_enum'] = True
    
    scraper = RetailScraper()
    
    if args.test:
        print("\n⚠️  TEST MODE: Limited enumeration for validation\n")
        # In test mode, scrapers will limit enumeration (already set in code with [:5], [:10] slices)
    
    if args.enumerate_only:
        await scraper.run_enumeration_only(retailers=args.retailers)
    else:
        resume = not args.no_resume
        await scraper.run_full_scrape(retailers=args.retailers, resume=resume)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nScrape interrupted by user")
        sys.exit(0)

