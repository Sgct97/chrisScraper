import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('scraper_data.db')
c = conn.cursor()

# Check recent products
c.execute("SELECT product_id, scraped_at FROM products WHERE retailer='target' ORDER BY scraped_at DESC LIMIT 5")
print("Last 5 products scraped:")
for row in c.fetchall():
    print(f"  {row[0]} at {row[1]}")

# Check errors
c.execute("SELECT COUNT(*) FROM errors WHERE retailer='target'")
error_count = c.fetchone()[0]
print(f"\nTotal errors: {error_count}")

if error_count > 0:
    c.execute("SELECT error_type, error_message, timestamp FROM errors WHERE retailer='target' ORDER BY timestamp DESC LIMIT 5")
    print("\nRecent errors:")
    for row in c.fetchall():
        print(f"  {row[2]}: {row[0]} - {row[1][:80]}")

# Check scrape runs
c.execute("SELECT * FROM scrape_runs WHERE retailer='target' ORDER BY started_at DESC LIMIT 2")
print("\nRecent scrape runs:")
for row in c.fetchall():
    print(f"  Run {row[0]}: Started {row[2]}, Success: {row[5]}, Failed: {row[6]}")

conn.close()


