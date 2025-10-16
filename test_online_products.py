"""
Test if pricing_store_id filters out online-only products.
Goal: Find the right API parameters for ALL online products (Target + marketplace).
"""
import asyncio
import httpx

async def test_product(tcin: str, product_type: str):
    """Test different API configurations for a product."""
    print(f"\n{'='*80}")
    print(f"Testing TCIN {tcin} ({product_type})")
    print('='*80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://www.target.com/p/A-{tcin}',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    configs = [
        {
            'name': 'Old key + pricing_store_id=3991',
            'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&pricing_store_id=3991'
        },
        {
            'name': 'New key + pricing_store_id=3991',
            'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=3991'
        },
        {
            'name': 'New key + NO store (just tcin)',
            'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}'
        },
        {
            'name': 'New key + store_id=0 (online)',
            'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&store_id=0'
        },
        {
            'name': 'New key + pricing_store_id=0',
            'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=0'
        },
    ]
    
    for config in configs:
        print(f"\n  [{config['name']}]")
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            try:
                resp = await client.get(config['url'], headers=headers)
                print(f"    Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    product = data.get('data', {}).get('product', {})
                    if product:
                        has_price = 'price' in product
                        has_item = 'item' in product
                        print(f"    [OK] Has product: item={has_item}, price={has_price}")
                        
                        if has_item:
                            item = product['item']
                            title = item.get('product_description', {}).get('title', 'N/A')
                            print(f"    Title: {title[:60]}...")
                        
                        if has_price:
                            price_info = product['price']
                            print(f"    Price: {price_info.get('formatted_current_price', 'N/A')}")
                    else:
                        print(f"    [EMPTY] Response has no product")
                elif resp.status_code == 400:
                    error = resp.json().get('errors', [{}])[0].get('message', 'Unknown')
                    print(f"    [ERROR 400] {error[:100]}")
                elif resp.status_code == 404:
                    error = resp.json().get('errors', [{}])[0].get('message', 'Not found')
                    print(f"    [NOT FOUND] {error[:100]}")
                else:
                    print(f"    [FAILED] {resp.text[:100]}")
                    
            except Exception as e:
                print(f"    [EXCEPTION] {e}")
        
        await asyncio.sleep(0.5)

async def main():
    print("="*80)
    print("TESTING: Do we need pricing_store_id or does it filter out online products?")
    print("="*80)
    
    # Test with known good products from earlier
    await test_product('1000006800', 'Known good - Outdoor Rug')
    await asyncio.sleep(2)
    
    await test_product('93138910', 'Known good - Item Locator')
    await asyncio.sleep(2)
    
    # Now test products that might be online-only or marketplace
    # We need to find some TCINs from Target's sitemap to test
    print("\n\n" + "="*80)
    print("If you have TCINs that were giving 404 with old API, add them here!")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(main())

