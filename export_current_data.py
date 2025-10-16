"""
Export current scraped data to CSV/JSON for analysis.
"""
import sqlite3
import json
import csv
from datetime import datetime

def export_to_csv():
    """Export all products to CSV."""
    conn = sqlite3.connect('scraper_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT product_id, product_url, title, brand, category, 
               price_current, price_compare_at, currency, availability,
               description, specifications, image_urls, 
               ratings_average, ratings_count, 
               shipping_cost, shipping_estimate, 
               variants, seller, scraped_at
        FROM products 
        WHERE retailer = 'target'
        ORDER BY scraped_at DESC
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No products to export")
        return
    
    filename = f"target_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    
    print(f"✓ Exported {len(rows):,} products to: {filename}")
    print(f"  File size: {round(len(open(filename, 'rb').read()) / 1024 / 1024, 2)} MB")
    
    conn.close()
    return filename

def export_to_json():
    """Export all products to JSON."""
    conn = sqlite3.connect('scraper_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM products WHERE retailer = 'target'
        ORDER BY scraped_at DESC
    """)
    
    rows = cursor.fetchall()
    products = [dict(row) for row in rows]
    
    filename = f"target_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, default=str)
    
    print(f"✓ Exported {len(products):,} products to: {filename}")
    print(f"  File size: {round(len(open(filename, 'rb').read()) / 1024 / 1024, 2)} MB")
    
    conn.close()
    return filename

def show_stats():
    """Show current statistics."""
    conn = sqlite3.connect('scraper_data.db')
    cursor = conn.cursor()
    
    # Total stats
    cursor.execute("SELECT COUNT(*) FROM products WHERE retailer='target'")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products WHERE retailer='target' AND price_current IS NOT NULL")
    with_price = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM incomplete_products WHERE retailer='target'")
    incomplete = cursor.fetchone()[0]
    
    print(f"\n{'='*60}")
    print(f"CURRENT SCRAPING STATS")
    print(f"{'='*60}")
    print(f"Total products scraped: {total:,}")
    print(f"Products with price: {with_price:,} ({with_price*100//total if total else 0}%)")
    print(f"Incomplete (need re-scrape): {incomplete:,}")
    print(f"{'='*60}\n")
    
    conn.close()

if __name__ == '__main__':
    show_stats()
    
    print("Export options:")
    print("  1. CSV (best for Excel/analysis)")
    print("  2. JSON (best for programmatic use)")
    print("  3. Both")
    
    choice = input("\nChoose (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        export_to_csv()
    
    if choice in ['2', '3']:
        export_to_json()

