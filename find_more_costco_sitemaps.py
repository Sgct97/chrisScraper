import httpx
import asyncio

async def check_for_more_sitemaps():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    # Common sitemap naming patterns
    sitemap_urls_to_test = [
        'https://www.costco.com/sitemap.xml',
        'https://www.costco.com/sitemap_index.xml',
        'https://www.costco.com/sitemap_products.xml',
        'https://www.costco.com/sitemap_product.xml',
        'https://www.costco.com/product-sitemap.xml',
        'https://www.costco.com/sitemap_lw_index.xml',  # We know this one
        'https://www.costco.com/sitemap_index_v2.xml',
    ]
    
    async with httpx.AsyncClient(timeout=10, http2=False, headers=headers) as client:
        print("Testing common sitemap URLs:\n")
        
        for url in sitemap_urls_to_test:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✓ FOUND: {url}")
                    print(f"  Size: {len(response.text)} chars")
                    print(f"  First 200 chars: {response.text[:200]}")
                    print()
                else:
                    print(f"✗ {response.status_code}: {url}")
            except:
                print(f"✗ ERROR: {url}")

asyncio.run(check_for_more_sitemaps())

