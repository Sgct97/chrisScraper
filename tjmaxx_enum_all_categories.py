import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def enumerate_all_categories():
    """Get ALL TJ Maxx categories without filtering"""
    
    playwright = await async_playwright().start()
    
    print("Enumerating ALL TJ Maxx categories (no filters)...\n")
    
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
        
        # Get ALL category URLs (no filtering!)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        all_category_urls = set()
        
        # Get ALL links with category patterns
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Full URL or relative
            if href.startswith('/store/shop/') or 'tjmaxx.tjx.com/store/shop/' in href:
                # Make absolute
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                
                # Any URL with the shop pattern
                if '/store/shop/' in href:
                    all_category_urls.add(href)
        
        print(f"2. Found {len(all_category_urls)} total category URLs (including filters)\n")
        
        # Crawl ALL of them - no limits, no slicing!
        urls_list = list(all_category_urls)
        
        print(f"3. Crawling ALL {len(urls_list)} category URLs...\n")
        
        for i, url in enumerate(urls_list):
            short_name = url.split('/')[-1][:30]
            print(f"[{i+1}/{len(urls_list)}] {short_name}...", end=" ", flush=True)
            
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
            
            if (i + 1) % 25 == 0:
                print(f"\n>>> {len(all_product_ids):,} unique products so far <<<\n")
        
        print(f"\n{'='*60}")
        print(f"FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Total category URLs: {len(all_category_urls):,}")
        print(f"Unique products found: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        await page.close()
        await browser.close()
        await playwright.stop()

asyncio.run(enumerate_all_categories())

