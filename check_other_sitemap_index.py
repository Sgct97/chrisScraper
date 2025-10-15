import httpx
import asyncio
from bs4 import BeautifulSoup

async def check_other_index():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    url = 'https://www.costco.com/sitemap_index.xml'
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'xml')
        sitemaps = [loc.text.strip() for loc in soup.find_all('loc')]
        
        print(f"sitemap_index.xml contains {len(sitemaps)} sitemaps:\n")
        
        all_product_ids = set()
        
        for i, sitemap_url in enumerate(sitemaps):
            r = await client.get(sitemap_url)
            soup2 = BeautifulSoup(r.text, 'xml')
            locs = soup2.find_all('loc')
            
            # Find product URLs
            product_urls = [loc.text.strip() for loc in locs if '.product.' in loc.text.lower()]
            
            print(f"{i+1}. {sitemap_url.split('/')[-1]}")
            print(f"   Total URLs: {len(locs)}")
            print(f"   Product URLs: {len(product_urls)}")
            
            if product_urls:
                # Extract IDs
                import re
                for url in product_urls:
                    match = re.search(r'\.product\.(\d+)\.html', url)
                    if match:
                        all_product_ids.add(match.group(1))
                
                print(f"   Sample: {product_urls[0]}")
            print()
        
        print(f"{'='*60}")
        print(f"TOTAL UNIQUE PRODUCTS in sitemap_index.xml: {len(all_product_ids)}")
        print(f"{'='*60}")

asyncio.run(check_other_index())

