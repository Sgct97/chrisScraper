import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def combine_all_costco():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    indexes_to_check = [
        'https://www.costco.com/sitemap_index.xml',
        'https://www.costco.com/sitemap_lw_index.xml',
    ]
    
    all_product_ids = set()
    all_urls = {}
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        
        for index_url in indexes_to_check:
            print(f"Checking: {index_url}")
            response = await client.get(index_url)
            soup = BeautifulSoup(response.text, 'xml')
            sitemaps = [loc.text.strip() for loc in soup.find_all('loc')]
            
            for sitemap_url in sitemaps:
                r = await client.get(sitemap_url)
                soup2 = BeautifulSoup(r.text, 'xml')
                locs = soup2.find_all('loc')
                
                for loc in locs:
                    url = loc.text.strip()
                    if '.product.' in url.lower():
                        match = re.search(r'\.product\.(\d+)\.html', url)
                        if match:
                            product_id = match.group(1)
                            all_product_ids.add(product_id)
                            all_urls[product_id] = url
            
            print(f"  Running total: {len(all_product_ids)} unique products\n")
    
    print(f"{'='*60}")
    print(f"COMBINED TOTAL: {len(all_product_ids)} unique products")
    print(f"{'='*60}")

asyncio.run(combine_all_costco())

