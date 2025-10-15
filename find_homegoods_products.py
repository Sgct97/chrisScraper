import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def find_products():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers) as client:
        
        # Try to find shop/products pages
        test_urls = [
            'https://www.homegoods.com/shop',
            'https://www.homegoods.com/products',
            'https://www.homegoods.com/catalog',
            'https://www.homegoods.com/us/store/shop',
            'https://www.homegoods.com/us/store/products',
        ]
        
        print("Searching for product catalog pages...\n")
        
        for url in test_urls:
            try:
                r = await client.get(url)
                print(f"{url}")
                print(f"  Status: {r.status_code}")
                
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    # Look for product links
                    all_links = soup.find_all('a', href=True)
                    product_patterns = ['/product/', '/p/', '/item/', '.html']
                    
                    potential_products = []
                    for link in all_links:
                        href = link['href']
                        if any(p in href for p in product_patterns) and any(char.isdigit() for char in href):
                            potential_products.append(href)
                    
                    print(f"  Found {len(potential_products)} potential product links")
                    if potential_products:
                        print(f"  Samples:")
                        for sample in potential_products[:3]:
                            print(f"    {sample}")
                    
                    # Look for JSON data
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string and 'product' in script.string.lower():
                            # Check for product data
                            if '"products"' in script.string or '"items"' in script.string:
                                print(f"  ✓ Found potential product JSON data")
                                break
                    
                    print()
                    break  # If we found a working page, stop
                    
            except Exception as e:
                print(f"  Error: {e}\n")

asyncio.run(find_products())

