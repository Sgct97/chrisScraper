import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def exhaustive_search():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    # Test EVERY possible sitemap naming pattern
    base_urls = [
        'https://www.costco.com/sitemap',
        'https://www.costco.com/sitemap_index',
        'https://www.costco.com/sitemap_lw_index',
        'https://www.costco.com/sitemaps/sitemap',
        'https://www.costco.com/product-sitemap',
        'https://www.costco.com/sitemap_products',
        'https://www.costco.com/sitemap_product',
        'https://www.costco.com/sitemap-index',
    ]
    
    suffixes = ['', '.xml', '_index.xml', '_1.xml', '_001.xml']
    
    found_sitemaps = set()
    
    async with httpx.AsyncClient(timeout=10, http2=False, headers=headers) as client:
        print("Testing ALL possible sitemap URLs...\n")
        
        # Test combinations
        for base in base_urls:
            for suffix in suffixes:
                url = base + suffix
                try:
                    response = await client.get(url)
                    if response.status_code == 200 and ('xml' in response.text.lower() or 'sitemap' in response.text.lower()):
                        if url not in found_sitemaps:
                            found_sitemaps.add(url)
                            print(f"✓ FOUND: {url}")
                except:
                    pass
        
        print(f"\n{'='*60}")
        print(f"Total sitemap indexes found: {len(found_sitemaps)}")
        print(f"{'='*60}\n")
        
        # Now parse each one to find ALL sitemaps
        all_sitemap_files = set()
        
        for index_url in found_sitemaps:
            response = await client.get(index_url)
            soup = BeautifulSoup(response.text, 'xml')
            locs = [loc.text.strip() for loc in soup.find_all('loc')]
            
            print(f"\n{index_url}:")
            print(f"  Contains {len(locs)} sitemap files")
            
            for loc in locs:
                all_sitemap_files.add(loc)
        
        print(f"\n{'='*60}")
        print(f"Total unique sitemap FILES: {len(all_sitemap_files)}")
        print(f"{'='*60}\n")
        
        # Now count products in ALL files
        all_product_ids = set()
        
        for sitemap_url in all_sitemap_files:
            try:
                r = await client.get(sitemap_url)
                soup = BeautifulSoup(r.text, 'xml')
                locs = soup.find_all('loc')
                
                for loc in locs:
                    url = loc.text.strip()
                    if '.product.' in url.lower():
                        match = re.search(r'\.product\.(\d+)\.html', url)
                        if match:
                            all_product_ids.add(match.group(1))
            except Exception as e:
                print(f"Error with {sitemap_url}: {e}")
        
        print(f"\n{'='*60}")
        print(f"FINAL EXHAUSTIVE COUNT: {len(all_product_ids)} unique products")
        print(f"{'='*60}")

asyncio.run(exhaustive_search())

