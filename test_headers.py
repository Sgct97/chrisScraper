import requests

url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin=93138910&pricing_store_id=2064&store_id=2064&channel=WEB'

# Test 1: No special headers
print("Test 1: Basic request (no special headers)")
r1 = requests.get(url, timeout=10)
print(f"  Status: {r1.status_code}\n")

# Test 2: With browser-like headers
print("Test 2: With browser headers")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.target.com/',
    'Origin': 'https://www.target.com'
}
r2 = requests.get(url, headers=headers, timeout=10)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    if data.get('data', {}).get('product'):
        print("  SUCCESS! Headers fixed it!")
else:
    print(f"  Still failing: {r2.text[:100]}\n")

# Test 3: Try a different product that we KNOW worked before
print("Test 3: Try product 1000006800 (first test product)")
url3 = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin=1000006800&pricing_store_id=2064&store_id=2064&channel=WEB'
r3 = requests.get(url3, headers=headers, timeout=10)
print(f"  Status: {r3.status_code}")
if r3.status_code == 200:
    print("  This product works!")
else:
    print(f"  Also failing: {r3.text[:100]}")

