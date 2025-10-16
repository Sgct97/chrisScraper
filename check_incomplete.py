import sqlite3
conn = sqlite3.connect('scraper_data.db')
c = conn.cursor()

# Check incomplete products
c.execute("SELECT COUNT(*) FROM incomplete_products WHERE retailer='target'")
incomplete_count = c.fetchone()[0]

print(f"Incomplete products tracked: {incomplete_count:,}")

if incomplete_count > 0:
    # Get field breakdown
    c.execute("SELECT missing_fields FROM incomplete_products WHERE retailer='target' LIMIT 100")
    import json
    field_counts = {}
    for row in c.fetchall():
        fields = json.loads(row[0])
        for field in fields:
            field_counts[field] = field_counts.get(field, 0) + 1
    
    print("\nMost common missing fields:")
    for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {field}: {count} products")

conn.close()

