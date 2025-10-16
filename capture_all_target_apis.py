#!/usr/bin/env python3
"""Capture ALL API calls Target makes when loading a product page."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    api_calls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture ALL network requests
        async def log_request(request):
            if 'target.com' in request.url and ('api' in request.url.lower() or 'redsky' in request.url):
                api_calls.append({
                    'url': request.url,
                    'method': request.method
                })
                print(f"API: {request.method} {request.url[:120]}")
        
        page.on('request', log_request)
        
        print("Loading Target product page and capturing ALL API calls...")
        print("=" * 80)
        await page.goto('https://www.target.com/p/-/A-91715302', 
                       wait_until='networkidle', timeout=60000)
        
        await asyncio.sleep(5)
        
        print("\n" + "=" * 80)
        print(f"Total API calls captured: {len(api_calls)}")
        print("=" * 80)
        
        # Look for fulfillment/shipping APIs
        for call in api_calls:
            if any(word in call['url'].lower() for word in ['fulfill', 'ship', 'deliv', 'availab']):
                print(f"\n🎯 SHIPPING RELATED:")
                print(f"  {call['url']}")
        
        await browser.close()

asyncio.run(main())

