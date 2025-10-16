"""
Compare fulfillment API responses with different parameters to see which gets best data.
"""
import asyncio
import httpx
import json

async def test():
    tcins = ['93138910', '1000076655']  # One with data, one without
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.target.com/',
    }
    
    for tcin in tcins:
        print(f"\n{'='*80}")
        print(f"TCIN: {tcin}")
        print('='*80)
        
        # Try different parameter combinations
        configs = [
            {'name': 'Current (zip=50000)', 'params': f'&zip=50000'},
            {'name': 'With store_id', 'params': f'&store_id=2064&zip=90210'},
            {'name': 'With pricing_store_id', 'params': f'&pricing_store_id=2064&zip=90210'},
            {'name': 'Just TCIN', 'params': ''},
        ]
        
        for config in configs:
            url = f"https://redsky.target.com/redsky_aggregations/v1/web/product_fulfillment_and_variation_hierarchy_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}{config['params']}"
            
            print(f"\n  [{config['name']}]")
            async with httpx.AsyncClient(timeout=30, http2=False) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    product = data.get('data', {}).get('product', {})
                    
                    has_fulfillment = 'fulfillment' in product
                    services = product.get('fulfillment', {}).get('shipping_options', {}).get('services', [])
                    has_services = len(services) > 0
                    
                    print(f"    Has fulfillment key: {has_fulfillment}")
                    print(f"    Has services: {has_services} ({len(services)} services)")
                    
                    if has_services:
                        print(f"    [YES] Has shipping estimate!")
                else:
                    print(f"    ✗ HTTP {resp.status_code}")
            
            await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(test())

