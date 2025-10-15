import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def get_base_categories_only():
    """Get ONLY base category URLs without filter parameters"""
    
    playwright = await async_playwright().start()
    
    print("Getting BASE TJ Maxx categories (no filters)...\n")
    
    browser = await playwright.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
    )
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
    """)
    
    all_product_ids = set()
    page = await context.new_page()
    
    async def wait_challenge():
        for _ in range(15):
            await page.wait_for_timeout(1000)
            content = await page.content()
            if 'Challenge Validation' not in content and 'Processing your request' not in content:
                return True
        return False
    
    async def get_products():
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
        
        new = 0
        for link in links:
            m = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if m and m.group(1) not in all_product_ids:
                all_product_ids.add(m.group(1))
                new += 1
        return new
    
    try:
        # Main page
        print("1. Main shop page...")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)
        
        count = await get_products()
        print(f"   ✓ {count} products\n")
        
        # Get ALL links
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        base_categories = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Look for base category patterns: /store/shop/[category]/_/N-[id]
            # WITHOUT filter parameters (mm=, Nr=, etc.)
            match = re.search(r'/store/shop/([^/]+)/_/(N-\d+)', href)
            if match:
                category_name = match.group(1)
                category_id = match.group(2)
                
                # Build clean base URL without query parameters
                base_url = f'https://tjmaxx.tjx.com/store/shop/{category_name}/_/{category_id}'
                base_categories.add(base_url)
        
        print(f"2. Found {len(base_categories)} BASE categories (no filters)\n")
        
        # Crawl ALL base categories
        print(f"3. Crawling ALL {len(base_categories)} base categories...\n")
        
        for i, url in enumerate(base_categories):
            cat_name = url.split('/shop/')[-1].split('/_/')[0]
            print(f"[{i+1}/{len(base_categories)}] {cat_name}...", end=" ", flush=True)
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                
                if not await wait_challenge():
                    print("timeout")
                    continue
                
                new = await get_products()
                print(f"{new} new (total: {len(all_product_ids)})")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"error: {str(e)[:30]}")
            
            if (i + 1) % 10 == 0:
                print(f"\n>>> {len(all_product_ids):,} unique products <<<\n")
        
        print(f"\n{'='*60}")
        print(f"FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Base categories: {len(base_categories):,}")
        print(f"Unique products: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        await page.close()
        await browser.close()
        await playwright.stop()

asyncio.run(get_base_categories_only())

