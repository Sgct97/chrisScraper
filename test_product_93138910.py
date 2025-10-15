#!/usr/bin/env python3
"""Direct test of product 93138910 to see what's being parsed."""

import asyncio
import json
import httpx

async def main():
    # Direct API call
    api_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=93138910&pricing_store_id=3991'
    
    print("Fetching API data...")
    async with httpx.AsyncClient(timeout=30, http2=False) as client:
        response = await client.get(api_url)
        api_data = response.json()
    
    print(f"\nStatus: {response.status_code}")
    print(f"API data keys: {list(api_data.keys())}")
    
    if 'errors' in api_data:
        print(f"\n⚠️  Errors present: {len(api_data['errors'])} errors")
        print(f"  First error: {api_data['errors'][0]['message']}")
    
    if 'data' in api_data:
        print(f"\ndata keys: {list(api_data['data'].keys())}")
        if 'product' in api_data['data']:
            product = api_data['data']['product']
            print(f"\nproduct keys ({len(product)} total): {list(product.keys())[:15]}")
            print(f"\n'item' in product: {'item' in product}")
            print(f"product.get('item') type: {type(product.get('item'))}")
            
            if product.get('item'):
                item = product['item']
                print(f"\nitem keys ({len(item)} total): {list(item.keys())[:15]}")
                
                # Check for product_description
                if 'product_description' in item:
                    desc = item['product_description']
                    print(f"\nproduct_description keys: {list(desc.keys())}")
                    print(f"Title: {desc.get('title')}")
                else:
                    print("\n✗ No 'product_description' in item")
                    print(f"  Checking for 'enrichment' instead...")
                    if 'enrichment' in item:
                        enrich = item['enrichment']
                        print(f"  enrichment keys: {list(enrich.keys())[:10]}")
            else:
                print("\n✗ No 'item' field in product!")
                print(f"  Available product fields suggest structure:")
                for key in product.keys():
                    val = product[key]
                    if isinstance(val, dict) and len(val) > 0:
                        print(f"    {key}: {list(val.keys())[:5]}")

asyncio.run(main())
