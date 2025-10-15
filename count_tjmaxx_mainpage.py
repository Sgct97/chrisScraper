import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def count_main_page():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        
        print("Counting products visible on TJ Maxx main shop page...\n")
        
        r = await client.get('https://tjmaxx.tjx.com/store/shop')
        print(f"Status: {r.status_code}")
        print(f"Content length: {len(r.text)}\n")
        
        if 'Challenge Validation' in r.text:
            print("⚠️  Bot challenge detected on main page too!\n")
            return
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Count products
        product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
        
        print(f"Product links on main shop page: {len(product_links)}")
        
        # Extract unique product IDs
        product_ids = set()
        for link in product_links:
            match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if match:
                product_ids.add(match.group(1))
        
        print(f"Unique product IDs: {len(product_ids)}\n")
        
        if product_ids:
            print("Sample products:")
            for i, pid in enumerate(list(product_ids)[:5]):
                for link in product_links:
                    if pid in link['href']:
                        print(f"  {i+1}. {link.get_text(strip=True)[:50]}")
                        break
        
        print(f"\n{'='*60}")
        print("ANALYSIS:")
        print(f"{'='*60}")
        print(f"\nTJ Maxx has STRONG bot protection (Challenge Validation pages)")
        print(f"Can only access main page which shows {len(product_ids)} products")
        print(f"\nTo enumerate all products would require:")
        print(f"  - Advanced CAPTCHA solving")
        print(f"  - Residential proxy rotation") 
        print(f"  - Browser automation with human-like behavior")
        print(f"  - Or API reverse engineering")
        print(f"\nEstimated catalog size: 10,000-50,000 products (typical for TJ Maxx)")
        print(f"{'='*60}")

asyncio.run(count_main_page())

