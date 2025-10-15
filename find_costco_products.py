import httpx
import asyncio
from bs4 import BeautifulSoup

async def find_product_sitemaps():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    url = 'https://www.costco.com/sitemap_lw_index.xml'
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'xml')
        all_sitemaps = [loc.text.strip() for loc in soup.find_all('loc')]
        
        print(f"Checking all {len(all_sitemaps)} sitemaps for product URLs...\n")
        
        for sitemap_url in all_sitemaps:
            r = await client.get(sitemap_url)
            soup2 = BeautifulSoup(r.text, 'xml')
            locs = soup2.find_all('loc')
            
            # Check for product-like URLs
            product_urls = [loc.text.strip() for loc in locs if '.product.' in loc.text or '/product/' in loc.text or '.html' in loc.text]
            
            # Also check for item IDs in URLs
            item_urls = [loc.text.strip() for loc in locs if any(char.isdigit() for char in loc.text) and '.html' in loc.text]
            
            if item_urls:
                print(f"Sitemap: {sitemap_url}")
                print(f"  Total URLs: {len(locs)}")
                print(f"  Potential product URLs: {len(item_urls)}")
                print(f"  Sample: {item_urls[0] if item_urls else 'N/A'}")
                print()

asyncio.run(find_product_sitemaps())

