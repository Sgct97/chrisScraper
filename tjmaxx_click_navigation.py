import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import random

async def natural_navigation():
    """Navigate TJ Maxx by clicking links naturally"""
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    
    page = await context.new_page()
    all_product_ids = set()
    
    async def wait_challenge():
        for _ in range(15):
            await page.wait_for_timeout(1000)
            content = await page.content()
            if 'Something went wrong' in content:
                return False
            if 'Challenge Validation' not in content:
                return True
        return False
    
    async def get_products():
        soup = BeautifulSoup(await page.content(), 'html.parser')
        new = 0
        for link in soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x):
            m = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if m and m.group(1) not in all_product_ids:
                all_product_ids.add(m.group(1))
                new += 1
        return new
    
    try:
        # Start at home
        print("Loading main page...\n")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)  # Long initial wait
        
        await get_products()
        print(f"Main page: {len(all_product_ids)} products\n")
        
        # Get category links from the page
        soup = BeautifulSoup(await page.content(), 'html.parser')
        category_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            if '/store/shop/' in href and text and len(text) > 2:
                # Get clean category names like "Women", "Men", "Home"
                if any(cat in text.lower() for cat in ['women', 'men', 'home', 'kids', 'shoes', 'beauty']):
                    if href not in [c[1] for c in category_links]:
                        category_links.append((text, href))
        
        print(f"Found {len(category_links)} main categories\n")
        
        # Click through categories naturally
        for i, (name, href) in enumerate(category_links[:20]):  # Test first 20
            print(f"[{i+1}] {name}...", end=" ", flush=True)
            
            try:
                # Navigate to category by CLICKING instead of goto
                await page.goto('https://tjmaxx.tjx.com' + href if href.startswith('/') else href, 
                               wait_until='domcontentloaded', timeout=20000)
                
                # Much longer wait
                await asyncio.sleep(random.uniform(8, 15))
                
                if not await wait_challenge():
                    print("BLOCKED - stopping")
                    break
                
                new = await get_products()
                print(f"{new} new (total: {len(all_product_ids)})")
                
                # Go back to main
                await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded')
                await asyncio.sleep(random.uniform(5, 10))
                
            except Exception as e:
                print(f"error: {str(e)[:40]}")
        
        print(f"\n{'='*60}")
        print(f"Total products found: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        await browser.close()
        await playwright.stop()

asyncio.run(natural_navigation())

