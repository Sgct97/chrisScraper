import asyncio
from undetected_playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import random

async def uc_enumeration():
    """Use undetected-playwright to bypass TJ Maxx detection"""
    
    playwright = await async_playwright().start()
    
    # Launch with undetected-playwright
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
        ]
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    )
    
    page = await context.new_page()
    all_product_ids = set()
    all_urls = set()
    
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
        print("Loading with undetected-playwright...\n")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        
        await get_products()
        print(f"Main page: {len(all_product_ids)} products\n")
        
        # Get all category URLs
        soup = BeautifulSoup(await page.content(), 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/store/shop/' in href:
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                href = href.split('?')[0]
                all_urls.add(href)
        
        urls_list = list(all_urls)
        print(f"Found {len(urls_list)} URLs\n")
        
        # Test first 50 URLs with delays
        for i, url in enumerate(urls_list[:50]):
            name = url.split('/')[-1][:40]
            print(f"[{i+1}/50] {name}...", end=" ", flush=True)
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                await asyncio.sleep(random.uniform(3, 6))
                
                if not await wait_challenge():
                    print("BLOCKED")
                    print(f"\nGot blocked after {i+1} pages")
                    break
                
                new = await get_products()
                print(f"{new} new (total: {len(all_product_ids)})")
                
            except Exception as e:
                print(f"error")
            
            if (i + 1) % 10 == 0:
                print(f"\n{len(all_product_ids):,} products\n")
        
        print(f"\n{'='*60}")
        print(f"Total products: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    finally:
        await browser.close()
        await playwright.stop()

asyncio.run(uc_enumeration())

