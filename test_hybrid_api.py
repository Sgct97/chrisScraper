"""
Test hybrid approach: new API key WITH pricing_store_id
"""
import asyncio
import httpx

async def test_hybrid():
    """Test new API key with pricing_store_id (what previous agent should have done)."""
    
    test_tcins = ['1000006800', '93138910']  # Known good products
    
    for tcin in test_tcins:
        print(f"\n{'='*80}")
        print(f"Testing TCIN: {tcin}")
        print('='*80)
        
        # Option 1: New key + old params
        url1 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=3991'
        print(f"\n[Test 1] New key + pricing_store_id=3991")
        
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            resp = await client.get(url1)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                has_product = 'product' in data.get('data', {})
                has_price = 'price' in data.get('data', {}).get('product', {})
                print(f"  [SUCCESS] Has product: {has_product}, Has price: {has_price}")
                if has_price:
                    print(f"  Price: {data['data']['product']['price']}")
            else:
                print(f"  [FAILED] {resp.text[:150]}")
        
        await asyncio.sleep(0.5)
        
        # Option 2: New key + old params + channel=WEB
        url2 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&pricing_store_id=3991&channel=WEB'
        print(f"\n[Test 2] New key + pricing_store_id=3991 + channel=WEB")
        
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            resp = await client.get(url2)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                has_product = 'product' in data.get('data', {})
                has_price = 'price' in data.get('data', {}).get('product', {})
                print(f"  [SUCCESS] Has product: {has_product}, Has price: {has_price}")
                if has_price:
                    print(f"  Price: {data['data']['product']['price']}")
            else:
                print(f"  [FAILED] {resp.text[:150]}")
        
        await asyncio.sleep(0.5)
        
        # Option 3: Old key (baseline)
        url3 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&pricing_store_id=3991'
        print(f"\n[Test 3 - BASELINE] Old key + pricing_store_id=3991")
        
        async with httpx.AsyncClient(timeout=30, http2=False) as client:
            resp = await client.get(url3)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                has_product = 'product' in data.get('data', {})
                has_price = 'price' in data.get('data', {}).get('product', {})
                print(f"  [SUCCESS] Has product: {has_product}, Has price: {has_price}")
                if has_price:
                    print(f"  Price: {data['data']['product']['price']}")
            else:
                print(f"  [FAILED] {resp.text[:150]}")

if __name__ == '__main__':
    asyncio.run(test_hybrid())

