import httpx
import asyncio
from bs4 import BeautifulSoup

async def check_costco_sitemaps():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    url = 'https://www.costco.com/sitemap_lw_index.xml'
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers) as client:
        # Get index
        print(f"Fetching index: {url}")
        response = await client.get(url)
        print(f"Status: {response.status_code}\n")
        
        soup = BeautifulSoup(response.text, 'xml')
        locs = soup.find_all('loc')
        
        print(f"Found {len(locs)} sitemap URLs:\n")
        for i, loc in enumerate(locs[:5]):  # Check first 5
            sitemap_url = loc.text.strip()
            print(f"{i+1}. {sitemap_url}")
            
            # Fetch this sitemap
            r2 = await client.get(sitemap_url)
            soup2 = BeautifulSoup(r2.text, 'xml')
            
            # Check for product URLs
            urls = soup2.find_all('url')
            product_locs = soup2.find_all('loc')
            
            print(f"   - Contains {len(urls)} <url> tags")
            print(f"   - Contains {len(product_locs)} <loc> tags")
            
            if product_locs:
                sample = product_locs[0].text.strip()
                print(f"   - Sample URL: {sample}")
                print(f"   - Has '.product.' in URL: {'.product.' in sample.lower()}")
            print()

asyncio.run(check_costco_sitemaps())

