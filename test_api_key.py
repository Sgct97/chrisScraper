import requests

# Test if Target.com is reachable at all
print("Test 1: Can we reach Target.com at all?")
try:
    r = requests.get('https://www.target.com/', timeout=10)
    print(f"  Target.com: {r.status_code} - {'REACHABLE' if r.status_code == 200 else 'ISSUE'}\n")
except Exception as e:
    print(f"  FAIL: {e}\n")

# Test with OLD API key (the one that worked before)
print("Test 2: Try OLD API key (ff457966...)")
old_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=93138910&pricing_store_id=2064&store_id=2064&channel=WEB'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}
try:
    r = requests.get(old_url, headers=headers, timeout=10)
    print(f"  Old Key Status: {r.status_code}")
    if r.status_code == 200:
        print("  OLD KEY STILL WORKS!")
    else:
        print(f"  Response: {r.text[:150]}\n")
except Exception as e:
    print(f"  Error: {e}\n")

# Test with NEW API key
print("Test 3: Try NEW API key (9f36aeaf...)")
new_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin=93138910&pricing_store_id=2064&store_id=2064&channel=WEB'
try:
    r = requests.get(new_url, headers=headers, timeout=10)
    print(f"  New Key Status: {r.status_code}")
    if r.status_code == 200:
        print("  NEW KEY WORKS!")
    else:
        print(f"  Response: {r.text[:150]}\n")
except Exception as e:
    print(f"  Error: {e}\n")

# Test without store_id and pricing_store_id
print("Test 4: Try without store params (maybe Target changed requirements?)")
simple_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin=93138910'
try:
    r = requests.get(simple_url, headers=headers, timeout=10)
    print(f"  Simple URL Status: {r.status_code}")
    print(f"  Response: {r.text[:150]}")
except Exception as e:
    print(f"  Error: {e}")

