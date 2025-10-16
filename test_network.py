import requests

url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin=93138910&pricing_store_id=2064&store_id=2064&channel=WEB'

print("Testing Target API from your new network...")
try:
    r = requests.get(url, timeout=10)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if data.get('data', {}).get('product'):
            print("SUCCESS - API is working!")
            print(f"Product Title: {data['data']['product']['item']['product_description']['title']}")
        else:
            print("FAIL - Got 200 but no product data")
    elif r.status_code == 404:
        print("FAIL - Getting 404 errors")
        print(f"Response: {r.text[:200]}")
    else:
        print(f"FAIL - Unexpected status code: {r.status_code}")
except requests.exceptions.Timeout:
    print("FAIL - Request timed out (network issue)")
except requests.exceptions.ConnectionError as e:
    print(f"FAIL - Connection error: {e}")
except Exception as e:
    print(f"FAIL - Error: {e}")
