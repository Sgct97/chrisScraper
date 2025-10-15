import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def analyze_homegoods():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        
        # Get sitemap
        print("Fetching HomeGoods sitemap...")
        r = await client.get('https://www.homegoods.com/sitemap.xml')
        print(f"Status: {r.status_code}\n")
        
        soup = BeautifulSoup(r.text, 'xml')
        
        # Check if it's an index or direct sitemap
        sitemap_tags = soup.find_all('sitemap')
        url_tags = soup.find_all('url')
        loc_tags = soup.find_all('loc')
        
        print(f"Structure:")
        print(f"  <sitemap> tags: {len(sitemap_tags)}")
        print(f"  <url> tags: {len(url_tags)}")
        print(f"  <loc> tags: {len(loc_tags)}")
        print()
        
        if sitemap_tags:
            # It's an index
            print("This is a sitemap INDEX. Sub-sitemaps:")
            for i, tag in enumerate(sitemap_tags[:10]):
                loc = tag.find('loc')
                if loc:
                    print(f"  {i+1}. {loc.text.strip()}")
            
            print(f"\nAnalyzing sub-sitemaps...")
            all_product_ids = set()
            
            for tag in sitemap_tags:
                loc = tag.find('loc')
                if not loc:
                    continue
                    
                sitemap_url = loc.text.strip()
                print(f"\n  {sitemap_url.split('/')[-1]}:")
                
                r2 = await client.get(sitemap_url)
                soup2 = BeautifulSoup(r2.text, 'xml')
                locs = soup2.find_all('loc')
                
                print(f"    Total URLs: {len(locs)}")
                
                # Check for product URLs
                product_urls = []
                for loc2 in locs:
                    url = loc2.text.strip()
                    # HomeGoods/TJX product URL patterns
                    if any(pattern in url.lower() for pattern in ['/product/', '/p/', '/item/']):
                        product_urls.append(url)
                        # Extract ID
                        id_match = re.search(r'/(?:product|p|item)/[^/]+/(\d+)', url)
                        if id_match:
                            all_product_ids.add(id_match.group(1))
                
                if product_urls:
                    print(f"    Product URLs: {len(product_urls)}")
                    print(f"    Sample: {product_urls[0]}")
                else:
                    # Show sample URL to understand structure
                    if locs:
                        print(f"    Sample URL: {locs[0].text.strip()}")
            
            print(f"\n{'='*60}")
            print(f"TOTAL UNIQUE PRODUCTS: {len(all_product_ids)}")
            print(f"{'='*60}")
            
        else:
            # Direct sitemap
            print("This is a DIRECT sitemap with URLs")
            product_urls = []
            for loc in loc_tags:
                url = loc.text.strip()
                if any(pattern in url.lower() for pattern in ['/product/', '/p/', '/item/']):
                    product_urls.append(url)
            
            print(f"Product URLs: {len(product_urls)}")
            if product_urls:
                print(f"Sample: {product_urls[0]}")

asyncio.run(analyze_homegoods())

