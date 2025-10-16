import sqlite3
import json

conn = sqlite3.connect('scraper_data.db')
c = conn.cursor()

# Get detailed breakdown
c.execute("SELECT missing_fields FROM incomplete_products WHERE retailer='target'")

field_counts = {}
products_by_field_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

for row in c.fetchall():
    fields = json.loads(row[0])
    num_missing = len(fields)
    products_by_field_count[min(num_missing, 5)] = products_by_field_count.get(min(num_missing, 5), 0) + 1
    
    for field in fields:
        field_counts[field] = field_counts.get(field, 0) + 1

total_incomplete = c.execute("SELECT COUNT(*) FROM incomplete_products WHERE retailer='target'").fetchone()[0]
total_scraped = c.execute("SELECT COUNT(*) FROM products WHERE retailer='target'").fetchone()[0]

print(f"Total products scraped: {total_scraped:,}")
print(f"Total incomplete products: {total_incomplete:,} ({total_incomplete*100//total_scraped}%)")
print(f"\nBreakdown by number of missing fields:")
for num_fields, count in sorted(products_by_field_count.items()):
    if count > 0:
        print(f"  Missing {num_fields} field(s): {count:,} products")

print(f"\nAll missing fields (full count):")
for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {field}: {count:,} products ({count*100//total_scraped}%)")

# Check if shipping_estimate is the main issue
only_shipping = c.execute("""
    SELECT COUNT(*) FROM incomplete_products 
    WHERE retailer='target' 
    AND missing_fields = '["shipping_estimate"]'
""").fetchone()[0]

print(f"\nProducts ONLY missing shipping_estimate: {only_shipping:,}")
print(f"Products missing other critical data: {total_incomplete - only_shipping:,}")

conn.close()

