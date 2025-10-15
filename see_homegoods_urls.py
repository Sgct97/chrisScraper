import httpx
import asyncio
from bs4 import BeautifulSoup

async def see_urls():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers) as client:
        r = await client.get('https://www.homegoods.com/sitemap.xml')
        soup = BeautifulSoup(r.text, 'xml')
        locs = soup.find_all('loc')
        
        print(f"Total URLs: {len(locs)}\n")
        print("First 20 URLs:\n")
        
        for i, loc in enumerate(locs[:20]):
            url = loc.text.strip()
            print(f"{i+1}. {url}")
        
        print(f"\n{'='*60}")
        
        # Categorize URLs
        categories = {
            'store': 0,
            'category': 0,
            'product': 0,
            'other': 0
        }
        
        for loc in locs:
            url = loc.text.strip().lower()
            if '/store/' in url or '/stores/' in url:
                categories['store'] += 1
            elif '/category/' in url or '/c/' in url:
                categories['category'] += 1
            elif '/product/' in url or '/p/' in url or '.product.' in url:
                categories['product'] += 1
            else:
                categories['other'] += 1
        
        print("\nURL breakdown:")
        for cat, count in categories.items():
            print(f"  {cat}: {count}")

asyncio.run(see_urls())

