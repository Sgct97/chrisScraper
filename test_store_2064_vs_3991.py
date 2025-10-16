"""
Compare store 2064 (used by Target.com) vs store 3991 (used by old scraper).
Test if different stores give different product availability.
"""
import asyncio
import httpx
import gzip
from io import BytesIO

async def get_sitemap_products():
    """Get real product TCINs from Target sitemap."""
    print("Fetching Target sitemap to get real product TCINs...")
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Get sitemap index
        resp = await client.get('https://www.target.com/sitemap_pdp-index.xml.gz')
        
        # Try to decompress, or use as-is if not gzipped
        try:
            with gzip.GzipFile(fileobj=BytesIO(resp.content)) as f:
                sitemap_index = f.read().decode('utf-8')
        except gzip.BadGzipFile:
            sitemap_index = resp.text
        
        # Extract first sitemap URL
        import re
        sitemap_urls = re.findall(r'<loc>(.*?)</loc>', sitemap_index)
        first_sitemap = sitemap_urls[0] if sitemap_urls else None
        
        if not first_sitemap:
            print("No sitemap URLs found!")
            return []
        
        print(f"Fetching first sitemap: {first_sitemap}")
        
        # Get actual product URLs from first sitemap
        resp = await client.get(first_sitemap)
        try:
            with gzip.GzipFile(fileobj=BytesIO(resp.content)) as f:
                sitemap_content = f.read().decode('utf-8')
        except gzip.BadGzipFile:
            sitemap_content = resp.text
        
        # Extract product URLs
        product_urls = re.findall(r'<loc>https://www\.target\.com/p/[^<]+/A-(\d+)</loc>', sitemap_content)
        
        print(f"Found {len(product_urls)} products in first sitemap")
        return product_urls[:50]  # Return first 50 for testing

async def test_stores():
    """Compare store 2064 vs 3991."""
    
    tcins = await get_sitemap_products()
    
    if not tcins:
        print("No products found in sitemap!")
        return
    
    print(f"\nTesting {len(tcins)} products with both stores...\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    results_3991 = {'success': 0, 'fail': 0}
    results_2064 = {'success': 0, 'fail': 0}
    
    for i, tcin in enumerate(tcins[:20], 1):  # Test first 20
        print(f"\n[{i}/20] TCIN: {tcin}")
        
        # Test store 3991
        url_3991 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=3991'
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            try:
                resp = await client.get(url_3991, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data', {}).get('product'):
                        results_3991['success'] += 1
                        print(f"  Store 3991: [OK] {resp.status_code}")
                    else:
                        results_3991['fail'] += 1
                        print(f"  Store 3991: [EMPTY] No product")
                else:
                    results_3991['fail'] += 1
                    print(f"  Store 3991: [FAIL] {resp.status_code}")
            except Exception as e:
                results_3991['fail'] += 1
                print(f"  Store 3991: [ERROR] {e}")
        
        await asyncio.sleep(0.5)
        
        # Test store 2064
        url_2064 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=2064&store_id=2064&channel=WEB'
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            try:
                resp = await client.get(url_2064, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('data', {}).get('product'):
                        results_2064['success'] += 1
                        print(f"  Store 2064: [OK] {resp.status_code}")
                    else:
                        results_2064['fail'] += 1
                        print(f"  Store 2064: [EMPTY] No product")
                else:
                    results_2064['fail'] += 1
                    print(f"  Store 2064: [FAIL] {resp.status_code}")
            except Exception as e:
                results_2064['fail'] += 1
                print(f"  Store 2064: [ERROR] {e}")
        
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"Store 3991: {results_3991['success']}/20 success ({results_3991['success']*100//20}%)")
    print(f"Store 2064: {results_2064['success']}/20 success ({results_2064['success']*100//20}%)")
    print(f"\nDifference: {results_2064['success'] - results_3991['success']} more products with store 2064")

if __name__ == '__main__':
    asyncio.run(test_stores())

