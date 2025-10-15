import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def find_tjmaxx_products():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        
        # Try different category/product URLs
        test_urls = [
            'https://tjmaxx.tjx.com/store/shop',
            'https://tjmaxx.tjx.com/store/shop/_/N-1854576536',  # Common TJX category structure
            'https://tjmaxx.tjx.com/store/shop/women',
            'https://tjmaxx.tjx.com/store/shop/home',
            'https://tjmaxx.tjx.com/store/jump/category/Women/1000001',
        ]
        
        print("Testing TJ Maxx product pages...\n")
        
        for url in test_urls:
            try:
                print(f"Trying: {url}")
                r = await client.get(url)
                print(f"  Status: {r.status_code}")
                print(f"  Final URL: {r.url}")
                
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    
                    # Look for product links - TJX uses specific patterns
                    all_links = soup.find_all('a', href=True)
                    
                    product_patterns = [
                        r'/store/jump/product/',
                        r'/store/jump/topic/',
                        r'\.product\.',
                        r'/product/',
                    ]
                    
                    product_links = []
                    for link in all_links:
                        href = link['href']
                        if any(re.search(pattern, href) for pattern in product_patterns):
                            product_links.append(href)
                    
                    print(f"  Product links found: {len(set(product_links))}")
                    
                    if product_links:
                        unique = list(set(product_links))[:5]
                        print(f"  Samples:")
                        for sample in unique:
                            print(f"    {sample}")
                        break  # Found products, stop
                
                print()
                
            except Exception as e:
                print(f"  Error: {e}\n")

asyncio.run(find_tjmaxx_products())

