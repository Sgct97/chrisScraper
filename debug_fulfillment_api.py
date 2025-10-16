"""
Debug the fulfillment API to see why shipping estimates aren't being captured.
"""
import asyncio
import httpx
import json

async def test_fulfillment():
    """Test the fulfillment API with products we've scraped."""
    
    # Test with a recently scraped product
    test_tcins = ['1000076655', '1000076686', '93138910']
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.target.com/',
    }
    
    for tcin in test_tcins:
        print(f"\n{'='*80}")
        print(f"Testing TCIN: {tcin}")
        print('='*80)
        
        # Test fulfillment API
        url = f'https://redsky.target.com/redsky_aggregations/v1/web/product_fulfillment_and_variation_hierarchy_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&zip=50000'
        
        print(f"\nFulfillment API URL:")
        print(f"  {url}")
        
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            resp = await client.get(url, headers=headers)
            print(f"\nStatus: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                
                # Check structure
                product = data.get('data', {}).get('product', {})
                fulfillment = product.get('fulfillment', {})
                
                print(f"\nTop-level keys: {list(data.keys())}")
                print(f"Product keys: {list(product.keys())[:15]}...")
                
                # Check shipping options
                shipping_opts = fulfillment.get('shipping_options', {})
                print(f"\nShipping options keys: {list(shipping_opts.keys())}")
                
                services = shipping_opts.get('services', [])
                print(f"Number of services: {len(services)}")
                
                if services:
                    print(f"\nFirst service:")
                    print(json.dumps(services[0], indent=2))
                
                # Check pay per order charges
                pay_charges = product.get('pay_per_order_charges', {})
                print(f"\nPay per order charges: {pay_charges}")
                
            else:
                print(f"[FAILED] {resp.text[:200]}")
        
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(test_fulfillment())

