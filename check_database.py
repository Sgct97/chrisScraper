#!/usr/bin/env python3
"""
Read-only database checker - safe to run while scraper is active.
Prints sample data to stdout/logs.
"""
import sqlite3
import os
from pathlib import Path

# Use same path as scraper
DB_PATH = os.getenv('DATABASE_PATH', 'scraper_data.db')

print(f"\n{'='*80}")
print(f"DATABASE CHECK: {DB_PATH}")
print(f"{'='*80}\n")

try:
    # Read-only connection with short timeout
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total counts
    cursor.execute("SELECT COUNT(*) as total FROM products")
    total = cursor.fetchone()['total']
    print(f"📊 TOTAL PRODUCTS: {total:,}\n")
    
    # Get count by status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM products 
        GROUP BY status
    """)
    print("Status breakdown:")
    for row in cursor.fetchall():
        print(f"  {row['status']}: {row['count']:,}")
    
    # Get count with/without prices
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE price_current IS NOT NULL")
    with_price = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE price_current IS NULL AND status = 'success'")
    without_price = cursor.fetchone()['count']
    
    print(f"\n💰 Price stats:")
    print(f"  With price: {with_price:,} ({100*with_price/total if total > 0 else 0:.1f}%)")
    print(f"  Without price (marketplace): {without_price:,} ({100*without_price/total if total > 0 else 0:.1f}%)")
    
    # Show 5 sample products WITH prices
    print(f"\n📦 SAMPLE PRODUCTS (with prices):")
    print("-" * 80)
    cursor.execute("""
        SELECT product_id, title, brand, price_current, availability, scraped_at
        FROM products 
        WHERE price_current IS NOT NULL
        ORDER BY scraped_at DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"\nID: {row['product_id']}")
        print(f"  Title: {row['title'][:60]}...")
        print(f"  Brand: {row['brand']}")
        print(f"  Price: ${row['price_current']}")
        print(f"  Availability: {row['availability']}")
        print(f"  Scraped: {row['scraped_at']}")
    
    # Show 5 sample products WITHOUT prices (marketplace)
    print(f"\n\n📦 SAMPLE MARKETPLACE PRODUCTS (no prices):")
    print("-" * 80)
    cursor.execute("""
        SELECT product_id, title, brand, price_current, availability, scraped_at
        FROM products 
        WHERE price_current IS NULL AND status = 'success'
        ORDER BY scraped_at DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"\nID: {row['product_id']}")
        print(f"  Title: {row['title'][:60] if row['title'] else 'N/A'}...")
        print(f"  Brand: {row['brand'] or 'N/A'}")
        print(f"  Price: NULL (marketplace)")
        print(f"  Availability: {row['availability']}")
        print(f"  Scraped: {row['scraped_at']}")
    
    # Get recent scrape run stats
    print(f"\n\n🔄 RECENT SCRAPE RUNS:")
    print("-" * 80)
    cursor.execute("""
        SELECT id, started_at, completed_at, total_attempted, total_success, total_failed
        FROM scrape_runs
        ORDER BY started_at DESC
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"\nRun #{row['id']} - Started: {row['started_at']}")
        if row['completed_at']:
            print(f"  Completed: {row['completed_at']}")
            print(f"  Attempted: {row['total_attempted']:,}")
            print(f"  Success: {row['total_success']:,}")
            print(f"  Failed: {row['total_failed']:,}")
        else:
            print(f"  Status: IN PROGRESS")
            print(f"  Success so far: {row['total_success']:,}")
    
    conn.close()
    print(f"\n{'='*80}")
    print("✅ DATABASE CHECK COMPLETE")
    print(f"{'='*80}\n")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

