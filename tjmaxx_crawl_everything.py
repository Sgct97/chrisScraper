import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def crawl_everything():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        viewport={'width': 1920, 'height': 1080},
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    
    all_product_ids = set()
    page = await context.new_page()
    
    async def wait_challenge():
        for _ in range(15):
            await page.wait_for_timeout(1000)
            if 'Challenge Validation' not in await page.content():
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
        print("Main page...")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)
        await get_products()
        print(f"Main: {len(all_product_ids)} products\n")
        
        # Get ALL URLs - no filtering whatsoever
        soup = BeautifulSoup(await page.content(), 'html.parser')
        all_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/store/shop/' in href:
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                href = href.split('?')[0]  # Remove query params only
                all_urls.add(href)
        
        print(f"Found {len(all_urls)} total URLs\n")
        print(f"Crawling ALL {len(all_urls)} URLs...\n")
        
        for i, url in enumerate(all_urls):
            name = url.split('/')[-1][:40]
            print(f"[{i+1}/{len(all_urls)}] {name}...", end=" ", flush=True)
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                if not await wait_challenge():
                    print("timeout")
                    continue
                new = await get_products()
                print(f"{new} new (total: {len(all_product_ids)})")
                await asyncio.sleep(0.5)
            except:
                print("error")
            
            if (i + 1) % 50 == 0:
                print(f"\n>>> {len(all_product_ids):,} products <<<\n")
        
        print(f"\n{'='*60}")
        print(f"URLs crawled: {len(all_urls):,}")
        print(f"Total products: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        await page.close()
        await browser.close()
        await playwright.stop()

asyncio.run(crawl_everything())

