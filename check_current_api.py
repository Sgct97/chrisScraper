from playwright.sync_api import sync_playwright
import json

print("Opening Target.com to see what API they're using NOW...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    api_calls = []
    
    # Capture all network requests
    def handle_request(request):
        if 'redsky' in request.url or 'api' in request.url:
            api_calls.append({
                'url': request.url,
                'method': request.method
            })
    
    page.on('request', handle_request)
    
    # Visit a product page
    print("Visiting product page...")
    page.goto('https://www.target.com/p/A-93138910', wait_until='networkidle')
    
    print(f"\nFound {len(api_calls)} API calls:")
    for call in api_calls[:10]:  # Show first 10
        print(f"  {call['method']} {call['url'][:120]}...")
    
    browser.close()

