"""
Test APIs with proper browser-like headers to avoid blocking.
"""
import asyncio
import httpx
import time

async def test_with_headers():
    """Test with full browser headers."""
    
    # Use browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.target.com/',
        'Origin': 'https://www.target.com',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
    }
    
    test_tcins = ['1000006800', '93138910']  # Known good products from earlier
    
    print("Waiting 5 seconds to avoid rate limit...")
    await asyncio.sleep(5)
    
    for tcin in test_tcins:
        print(f"\n{'='*80}")
        print(f"Testing TCIN: {tcin}")
        print('='*80)
        
        # Test OLD API with headers
        url_old = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&pricing_store_id=3991'
        print(f"\n[OLD API] ff457966...pricing_store_id=3991")
        
        async with httpx.AsyncClient(timeout=30, http2=False, follow_redirects=True) as client:
            resp = await client.get(url_old, headers=headers)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                has_product = 'product' in data.get('data', {})
                has_price = 'price' in data.get('data', {}).get('product', {})
                print(f"  [SUCCESS] Has product: {has_product}, Has price: {has_price}")
            else:
                print(f"  [FAILED] {resp.text[:200]}")
        
        await asyncio.sleep(2)  # Rate limit between requests
        
        # Test NEW API with pricing_store_id
        url_new = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=3991'
        print(f"\n[NEW API] 9f36aeaf...pricing_store_id=3991")
        
        async with httpx.AsyncClient(timeout=30, http2=False, follow_redirects=True) as client:
            resp = await client.get(url_new, headers=headers)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                has_product = 'product' in data.get('data', {})
                has_price = 'price' in data.get('data', {}).get('product', {})
                print(f"  [SUCCESS] Has product: {has_product}, Has price: {has_price}")
            else:
                print(f"  [FAILED] {resp.text[:200]}")
        
        await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(test_with_headers())

