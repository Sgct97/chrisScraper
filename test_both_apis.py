"""
Test both old and new Target APIs to see which one works.
"""
import asyncio
import httpx
import json

async def test_api(api_url: str, label: str):
    """Test a single API URL."""
    print(f"\n{'='*80}")
    print(f"Testing: {label}")
    print(f"URL: {api_url}")
    print('='*80)
    
    try:
        async with httpx.AsyncClient(timeout=30, http2=False, follow_redirects=True) as client:
            response = await client.get(api_url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"[SUCCESS] Got JSON response")
                    print(f"  Top-level keys: {list(result.keys())}")
                    
                    if 'data' in result:
                        data = result['data']
                        print(f"  data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                        
                        if isinstance(data, dict) and 'product' in data:
                            product = data['product']
                            print(f"  [OK] product exists")
                            print(f"  Product keys: {list(product.keys())[:10]}...")  # First 10 keys
                            
                            # Check for price data
                            if 'price' in product:
                                print(f"  [OK] Has price data: {product['price']}")
                            else:
                                print(f"  [MISSING] No 'price' key")
                            
                            # Check item details
                            if 'item' in product:
                                item = product['item']
                                tcin = item.get('tcin', 'N/A')
                                title = item.get('product_description', {}).get('title', 'N/A')
                                print(f"  TCIN: {tcin}")
                                print(f"  Title: {title[:80]}...")
                            
                        else:
                            print(f"  [MISSING] No product in data")
                    else:
                        print(f"  [MISSING] No 'data' key in response")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"[FAILED] Invalid JSON: {e}")
                    print(f"  Response preview: {response.text[:200]}")
                    return False
            else:
                print(f"[FAILED] HTTP {response.status_code}")
                print(f"  Response preview: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return False

async def main():
    # Test products - mix of Target-sold and potentially marketplace
    test_tcins = [
        '1000006800',   # From test_api_direct.py
        '93138910',     # From test_product_93138910.py
        '54191097',     # Random product
        '13284429',     # Random product
        '17383597',     # Random product
    ]
    
    results = {}
    
    for tcin in test_tcins:
        print(f"\n\n{'#'*80}")
        print(f"# TESTING PRODUCT TCIN: {tcin}")
        print(f"{'#'*80}")
        
        # OLD API (working)
        old_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&pricing_store_id=3991'
        old_works = await test_api(old_api_url, "OLD API (ff457966...pricing_store_id=3991)")
        
        # NEW API (broken)
        new_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&channel=WEB&is_bot=false'
        new_works = await test_api(new_api_url, "NEW API (9f36aeaf...channel=WEB)")
        
        results[tcin] = {'old': old_works, 'new': new_works}
        
        await asyncio.sleep(1)  # Rate limit
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"{'TCIN':<15} {'OLD API':<15} {'NEW API':<15}")
    print('-'*45)
    for tcin, result in results.items():
        old_status = '[OK] WORKS' if result['old'] else '[X] FAILS'
        new_status = '[OK] WORKS' if result['new'] else '[X] FAILS'
        print(f"{tcin:<15} {old_status:<15} {new_status:<15}")
    
    old_success = sum(1 for r in results.values() if r['old'])
    new_success = sum(1 for r in results.values() if r['new'])
    
    print(f"\nOLD API: {old_success}/{len(results)} success ({old_success*100//len(results)}%)")
    print(f"NEW API: {new_success}/{len(results)} success ({new_success*100//len(results)}%)")

if __name__ == '__main__':
    asyncio.run(main())

