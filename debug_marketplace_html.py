"""Debug script to inspect marketplace product HTML structure."""
import asyncio
from playwright.async_api import async_playwright
import json

async def inspect_marketplace_product():
    """Load a marketplace product and dump the __NEXT_DATA__ structure."""
    
    # Known marketplace product with "/" title
    url = 'https://www.target.com/p//-/A-1002431260'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Loading: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        
        # Wait a bit for content to load
        await page.wait_for_timeout(3000)
        
        # Extract __NEXT_DATA__
        script = await page.query_selector('script#__NEXT_DATA__')
        if script:
            content = await script.inner_text()
            data = json.loads(content)
            
            # Save full structure for inspection
            with open('marketplace_next_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            print("\n✓ Saved full __NEXT_DATA__ to marketplace_next_data.json")
            
            # Try to navigate to product data
            print("\nAttempting to extract product data:")
            props = data.get('props', {})
            print(f"  props keys: {list(props.keys())}")
            
            page_props = props.get('pageProps', {})
            print(f"  pageProps keys: {list(page_props.keys())}")
            
            initial_data = page_props.get('initialData', {})
            print(f"  initialData keys: {list(initial_data.keys())}")
            
            if 'data' in initial_data:
                data_obj = initial_data.get('data', {})
                print(f"  data keys: {list(data_obj.keys())}")
                
                if 'product' in data_obj:
                    product = data_obj.get('product', {})
                    print(f"  product keys: {list(product.keys())}")
                    print(f"\n  Title: {product.get('item', {}).get('product_description', {}).get('title')}")
                    print(f"  Price: {product.get('price', {}).get('current_retail')}")
        else:
            print("✗ No __NEXT_DATA__ found")
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(inspect_marketplace_product())

