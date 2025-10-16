import requests
import json

tcin = '93138910'
store_id = '2064'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Testing NEW Target API endpoints...\n")

# Test 1: pdp_personalized_v1
print("Test 1: pdp_personalized_v1")
url1 = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_personalized_v1?pricing_store_id={store_id}&tcin={tcin}&key=9f36aeafbe60771e321a7cc95a78140772ab3e96'
r1 = requests.get(url1, headers=headers, timeout=10)
print(f"  Status: {r1.status_code}")
if r1.status_code == 200:
    data = r1.json()
    print(f"  SUCCESS! Got {len(str(data))} bytes of data")
    # Save for inspection
    with open('test_personalized_api.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("  Saved to test_personalized_api.json")
else:
    print(f"  Failed: {r1.text[:100]}")

print()

# Test 2: product_fulfillment_and_variation_hierarchy_v1
print("Test 2: product_fulfillment_and_variation_hierarchy_v1")
url2 = f'https://redsky.target.com/redsky_aggregations/v1/web/product_fulfillment_and_variation_hierarchy_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&store_id={store_id}'
r2 = requests.get(url2, headers=headers, timeout=10)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print(f"  SUCCESS! Got {len(str(data))} bytes of data")
    with open('test_fulfillment_api.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("  Saved to test_fulfillment_api.json")
else:
    print(f"  Failed: {r2.text[:100]}")

