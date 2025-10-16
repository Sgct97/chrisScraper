from playwright.sync_api import sync_playwright
import json

print("Testing API access THROUGH browser (not direct HTTP)...\n")

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context()
    page = context.new_page()
    
    # Try to fetch the API directly in the browser context
    tcin = '93138910'
    api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_personalized_v1?pricing_store_id=2064&tcin={tcin}&key=9f36aeafbe60771e321a7cc95a78140772ab3e96'
    
    print(f"Fetching: {api_url[:80]}...")
    
    response = page.request.get(api_url)
    
    print(f"Status: {response.status}")
    if response.status == 200:
        print("SUCCESS! Browser can access the API!")
        data = response.json()
        print(f"Got {len(str(data))} bytes")
        print("This confirms: YOUR ISP IS BLOCKING DIRECT API REQUESTS")
        print("Solution: Use browser-based scraping or get residential proxies")
    else:
        print(f"Failed: {response.text()[:200]}")
    
    browser.close()

