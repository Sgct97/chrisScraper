import sqlite3
import time

conn = sqlite3.connect('scraper_data.db')
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM products WHERE retailer='target'")
count1 = c.fetchone()[0]
print(f"Starting count: {count1:,} products")
print("Waiting 10 seconds to measure speed...")

time.sleep(10)

c.execute("SELECT COUNT(*) FROM products WHERE retailer='target'")
count2 = c.fetchone()[0]
diff = count2 - count1

print(f"After 10 seconds: {count2:,} products")
print(f"\nSpeed: {diff} products in 10s")
print(f"  = {diff * 6} products/minute")
print(f"  = {diff * 360} products/hour")
print(f"\nAt this rate: {2436399 // (diff * 360)} hours for 2.4M products ({(2436399 // (diff * 360)) / 24:.1f} days)")

conn.close()

