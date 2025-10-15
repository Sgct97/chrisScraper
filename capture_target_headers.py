#!/usr/bin/env python3
"""Capture real browser headers for Target API."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    headers_captured = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture request headers
        async def capture_headers(request):
            if 'redsky.target.com' in request.url and 'pdp_client_v1' in request.url:
                print(f"\n✓ Captured API request!")
                print(f"URL: {request.url[:100]}")
                print(f"\nHeaders:")
                for key, value in request.headers.items():
                    print(f"  {key}: {value}")
                    headers_captured[key] = value
        
        page.on('request', capture_headers)
        
        # Navigate to a real Target product page to trigger API call
        print("Opening Target product page...")
        print("The browser will load and make an API call automatically...")
        await page.goto('https://www.target.com/p/item-locator-4pk-dealworthy-8482/-/A-93138910', 
                       wait_until='networkidle', timeout=60000)
        
        await asyncio.sleep(3)
        
        if headers_captured:
            print(f"\n\n{'='*80}")
            print("PYTHON DICT FORMAT:")
            print("{'='*80}")
            print("headers = {")
            for key, value in headers_captured.items():
                print(f"    '{key}': '{value}',")
            print("}")
        else:
            print("\n⚠️  No API call captured")
        
        await browser.close()

asyncio.run(main())

