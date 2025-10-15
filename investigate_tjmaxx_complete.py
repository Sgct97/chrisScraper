import httpx
import asyncio
from bs4 import BeautifulSoup

async def investigate_tjmaxx():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    print("="*60)
    print("TJ MAXX INVESTIGATION")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        
        # 1. Check robots.txt
        print("\n1. Checking robots.txt...")
        try:
            r = await client.get('https://www.tjmaxx.com/robots.txt')
            if r.status_code == 200:
                print(f"  ✓ robots.txt loaded ({len(r.text)} chars)")
                sitemaps = [line for line in r.text.split('\n') if 'sitemap' in line.lower()]
                if sitemaps:
                    print(f"  Sitemaps found:")
                    for sm in sitemaps[:10]:
                        print(f"    {sm}")
                else:
                    print(f"  ✗ No sitemap references in robots.txt")
            else:
                print(f"  ✗ Status: {r.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # 2. Try common sitemap URLs
        print("\n2. Testing common sitemap URLs...")
        sitemap_tests = [
            'https://www.tjmaxx.com/sitemap.xml',
            'https://www.tjmaxx.com/sitemap_index.xml',
            'https://www.tjmaxx.com/sitemap_products.xml',
            'https://www.tjmaxx.com/product-sitemap.xml',
            'https://www.tjmaxx.com/sitemaps/sitemap.xml',
            'https://tjmaxx.tjx.com/sitemap.xml',
        ]
        
        found_sitemaps = []
        for url in sitemap_tests:
            try:
                r = await client.get(url)
                if r.status_code == 200 and 'xml' in r.text.lower():
                    print(f"  ✓ FOUND: {url}")
                    print(f"    Size: {len(r.text)} chars")
                    found_sitemaps.append(url)
            except:
                pass
        
        if not found_sitemaps:
            print(f"  ✗ No standard sitemaps found")
        
        # 3. Check main shop page
        print("\n3. Checking main shop page...")
        try:
            r = await client.get('https://www.tjmaxx.com/store/shop/')
            print(f"  Final URL: {r.url}")
            print(f"  Status: {r.status_code}")
            
            if r.status_code == 200:
                print(f"  ✓ Page loaded ({len(r.text)} chars)")
                
                # Look for product links
                soup = BeautifulSoup(r.text, 'html.parser')
                product_links = soup.find_all('a', href=lambda x: x and ('/product/' in x or '.product.' in x))
                
                print(f"  Found {len(product_links)} product links on page")
                if product_links:
                    print(f"  Sample: {product_links[0]['href']}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

asyncio.run(investigate_tjmaxx())

