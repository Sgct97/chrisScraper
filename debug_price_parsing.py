"""
Debug price parsing to see what the API actually returns.
"""
import asyncio
import httpx
import json

async def debug_prices():
    """Check API responses for products that showed no price."""
    
    test_tcins = [
        ('1000000076', 'Product with no price #1'),
        ('1000006800', 'Rug with variant pricing'),
        ('93138910', 'Item Locator - HAS price'),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    for tcin, desc in test_tcins:
        print(f"\n{'='*80}")
        print(f"{desc} (TCIN: {tcin})")
        print('='*80)
        
        url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=2064&store_id=2064&channel=WEB'
        
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            resp = await client.get(url, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                product = data.get('data', {}).get('product', {})
                price_obj = product.get('price', {})
                
                print(f"\nPrice object keys: {list(price_obj.keys())}")
                print(f"\nFull price object:")
                print(json.dumps(price_obj, indent=2))
                
                # Check what we can extract
                current_retail = price_obj.get('current_retail')
                formatted_price = price_obj.get('formatted_current_price')
                current_retail_min = price_obj.get('current_retail_min')
                current_retail_max = price_obj.get('current_retail_max')
                
                print(f"\nExtracted values:")
                print(f"  current_retail: {current_retail}")
                print(f"  formatted_current_price: {formatted_price}")
                print(f"  current_retail_min: {current_retail_min}")
                print(f"  current_retail_max: {current_retail_max}")
            else:
                print(f"[FAILED] HTTP {resp.status_code}")
        
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(debug_prices())

