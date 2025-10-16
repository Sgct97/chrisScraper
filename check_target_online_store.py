"""
Check what store ID Target.com uses for online browsing (not logged in).
"""
import asyncio
import httpx
from playwright.async_api import async_playwright

async def check_website():
    """Visit Target.com and capture API calls to see what store_id they use."""
    print("Opening Target.com to see what store_id is used for online browsing...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track API calls
        api_calls = []
        
        async def handle_request(request):
            if 'redsky.target.com' in request.url and 'pdp_client' in request.url:
                api_calls.append(request.url)
                print(f"\n[CAPTURED API CALL]")
                print(f"URL: {request.url}")
        
        page.on('request', handle_request)
        
        # Visit a product page
        print("\nVisiting product page...")
        await page.goto('https://www.target.com/p/item-locator-4pk-dealworthy-8482/-/A-93138910', timeout=30000)
        
        # Wait for page to load
        await asyncio.sleep(5)
        
        print(f"\n{'='*80}")
        print(f"Captured {len(api_calls)} API calls")
        print('='*80)
        
        for url in api_calls:
            print(f"\n{url}")
            
            # Extract parameters
            if 'pricing_store_id=' in url:
                import re
                match = re.search(r'pricing_store_id=(\d+)', url)
                if match:
                    store_id = match.group(1)
                    print(f"  --> Uses pricing_store_id={store_id}")
            
            if 'store_id=' in url:
                import re
                match = re.search(r'store_id=(\d+)', url)
                if match:
                    store_id = match.group(1)
                    print(f"  --> Uses store_id={store_id}")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_website())

