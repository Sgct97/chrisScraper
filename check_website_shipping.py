"""
Check if shipping estimates are visible on the actual Target website
for products that don't have it in the API.
"""
import asyncio
from playwright.async_api import async_playwright

async def check():
    tcins = [
        ('93138910', 'Has API shipping data'),
        ('1000076655', 'NO API shipping data'),
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        for tcin, desc in tcins:
            print(f"\n{'='*80}")
            print(f"TCIN: {tcin} ({desc})")
            print('='*80)
            
            page = await context.new_page()
            url = f'https://www.target.com/p/A-{tcin}'
            
            print(f"Loading: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)  # Let everything load
            
            # Look for shipping/delivery text
            shipping_selectors = [
                'text=/Get it by/',
                'text=/Arrives by/',
                'text=/Shipping/',
                'text=/Delivery/',
                '[data-test*="shipping"]',
                '[data-test*="delivery"]',
                'text=/day shipping/',
            ]
            
            print("\nSearching for shipping info on page...")
            found_shipping = []
            
            for selector in shipping_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for elem in elements[:3]:  # First 3 matches
                        text = await elem.inner_text()
                        if text and len(text) < 100:
                            found_shipping.append(text.strip())
                except:
                    pass
            
            if found_shipping:
                print(f"\n[FOUND] Shipping info on page:")
                for info in set(found_shipping):
                    print(f"  - {info}")
            else:
                print(f"\n[NOT FOUND] No shipping info visible")
            
            # Check __NEXT_DATA__ JSON
            try:
                next_data = await page.evaluate('''() => {
                    const script = document.getElementById('__NEXT_DATA__');
                    return script ? script.textContent : null;
                }''')
                
                if next_data:
                    import json
                    data = json.loads(next_data)
                    # Search for shipping/delivery in the JSON
                    data_str = json.dumps(data)
                    if 'delivery' in data_str.lower() or 'shipping' in data_str.lower():
                        print(f"\n[YES] __NEXT_DATA__ contains shipping/delivery keywords")
                    else:
                        print(f"\n[NO] __NEXT_DATA__ doesn't have shipping keywords")
            except Exception as e:
                print(f"\n[ERROR] Checking __NEXT_DATA__: {e}")
            
            await page.close()
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check())

