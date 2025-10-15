import httpx
import asyncio
from bs4 import BeautifulSoup

async def deep_check_costco():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    url = 'https://www.costco.com/sitemap_lw_index.xml'
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        # Get all sitemaps
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'xml')
        all_sitemaps = [loc.text.strip() for loc in soup.find_all('loc')]
        
        print(f"Analyzing all {len(all_sitemaps)} sitemaps:\n")
        
        total_products = 0
        all_product_ids = set()
        
        for i, sitemap_url in enumerate(all_sitemaps):
            r = await client.get(sitemap_url)
            soup2 = BeautifulSoup(r.text, 'xml')
            locs = soup2.find_all('loc')
            
            # Find product URLs
            product_urls = [loc.text.strip() for loc in locs if '.product.' in loc.text.lower()]
            
            if product_urls:
                # Extract IDs
                for url in product_urls:
                    import re
                    match = re.search(r'\.product\.(\d+)\.html', url)
                    if match:
                        all_product_ids.add(match.group(1))
                
                print(f"{i+1}. {sitemap_url.split('/')[-1]}")
                print(f"   Total URLs: {len(locs)}")
                print(f"   Product URLs: {len(product_urls)}")
                print(f"   Running unique ID count: {len(all_product_ids)}")
        
        print(f"\n{'='*60}")
        print(f"FINAL COUNT: {len(all_product_ids)} unique product IDs")
        print(f"{'='*60}")

asyncio.run(deep_check_costco())

