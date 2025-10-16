#!/usr/bin/env python3
"""
Show recent products from database - for verifying data quality during scraping
"""
import sqlite3
import json
import sys
from datetime import datetime

def show_recent_products(db_path='scraper_data.db', limit=5):
    """Show most recent products with full details."""
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM products 
            ORDER BY scraped_at DESC 
            LIMIT ?
        """, (limit,))
        
        products = cursor.fetchall()
        
        if not products:
            print("No products found in database yet.")
            return
        
        print(f"\n{'='*80}")
        print(f"MOST RECENT {len(products)} PRODUCTS")
        print(f"{'='*80}\n")
        
        for i, p in enumerate(products, 1):
            print(f"{'='*80}")
            print(f"PRODUCT #{i}")
            print(f"{'='*80}")
            print(f"Product ID: {p['product_id']}")
            print(f"Retailer: {p['retailer']}")
            print(f"URL: {p['product_url']}")
            print(f"Title: {p['title']}")
            print(f"Brand: {p['brand']}")
            print(f"Category: {p['category']}")
            print(f"")
            print(f"PRICING:")
            print(f"  Current Price: ${p['price_current']}")
            print(f"  Compare-At Price: ${p['price_compare_at'] or 'N/A'}")
            print(f"  Currency: {p['currency']}")
            print(f"")
            print(f"AVAILABILITY:")
            print(f"  Status: {p['availability']}")
            print(f"  Seller: {p['seller'] or 'Target'}")
            print(f"")
            print(f"SHIPPING:")
            print(f"  Cost: ${p['shipping_cost'] or 'N/A'}")
            print(f"  Estimate: {p['shipping_estimate'] or 'N/A'}")
            print(f"")
            print(f"IMAGES:")
            if p['image_urls']:
                try:
                    images = json.loads(p['image_urls'])
                    print(f"  Count: {len(images)}")
                    if images:
                        print(f"  Primary: {images[0][:80]}...")
                except:
                    print(f"  {p['image_urls'][:100]}...")
            else:
                print(f"  None")
            print(f"")
            print(f"RATINGS:")
            print(f"  Average: {p['ratings_average'] or 'N/A'}")
            print(f"  Count: {p['ratings_count'] or 0}")
            print(f"")
            print(f"DESCRIPTION:")
            desc = p['description'] or ''
            if isinstance(desc, str) and desc.startswith('['):
                try:
                    desc_list = json.loads(desc)
                    print(f"  {' | '.join(desc_list[:3])}...")
                except:
                    print(f"  {desc[:200]}...")
            else:
                print(f"  {desc[:200]}...")
            print(f"")
            print(f"SPECIFICATIONS:")
            if p['specifications']:
                try:
                    specs = json.loads(p['specifications'])
                    if isinstance(specs, dict):
                        for key, val in list(specs.items())[:5]:
                            print(f"  {key}: {val}")
                    else:
                        print(f"  {str(specs)[:200]}...")
                except:
                    print(f"  {p['specifications'][:200]}...")
            else:
                print(f"  None")
            print(f"")
            print(f"VARIANTS:")
            if p['variants']:
                try:
                    variants = json.loads(p['variants'])
                    print(f"  {variants[:200]}...")
                except:
                    print(f"  {p['variants'][:200]}...")
            else:
                print(f"  None")
            print(f"")
            print(f"Scraped: {p['scraped_at']}")
            print(f"{'='*80}\n")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Show recent products from database')
    parser.add_argument('--limit', type=int, default=5, help='Number of products to show (default: 5)')
    parser.add_argument('--db', default='scraper_data.db', help='Database path')
    
    args = parser.parse_args()
    
    show_recent_products(args.db, args.limit)

