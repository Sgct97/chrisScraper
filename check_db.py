import sqlite3
conn = sqlite3.connect('scraper_data.db')
c = conn.cursor()

# Get total stats
c.execute("SELECT COUNT(*), COUNT(CASE WHEN price_current IS NOT NULL THEN 1 END) FROM products WHERE retailer='target'")
total, with_price = c.fetchone()
print(f"Target Products: {total:,} total, {with_price:,} with price ({with_price*100//total if total else 0}%)")

# Get last 5
c.execute("SELECT product_id, title, price_current, shipping_cost, shipping_estimate FROM products WHERE retailer='target' ORDER BY scraped_at DESC LIMIT 5")
print("\nLast 5 scraped:")
for row in c.fetchall():
    print(f"  TCIN: {row[0]}")
    print(f"    Title: {row[1][:60] if row[1] else 'N/A'}...")
    print(f"    Price: ${row[2] if row[2] else 'MISSING'}")
    print(f"    Shipping: cost=${row[3] if row[3] else 'N/A'}, est={row[4] if row[4] else 'N/A'}")

conn.close()

