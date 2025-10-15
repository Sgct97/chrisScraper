import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import random

async def stealth_enumeration():
    """Enumerate TJ Maxx with human-like behavior to avoid detection"""
    
    all_product_ids = set()
    all_urls = set()
    
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    async def create_fresh_session():
        """Create a new browser session"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080},
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page = await context.new_page()
        return playwright, browser, page
    
    async def wait_challenge(page):
        for _ in range(15):
            await page.wait_for_timeout(1000)
            content = await page.content()
            if 'Challenge Validation' not in content and 'Something went wrong' not in content:
                return True
        return False
    
    async def get_products(page):
        soup = BeautifulSoup(await page.content(), 'html.parser')
        new = 0
        for link in soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x):
            m = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if m and m.group(1) not in all_product_ids:
                all_product_ids.add(m.group(1))
                new += 1
        return new
    
    try:
        # Initial session to get URLs
        print("Getting all category URLs...")
        playwright, browser, page = await create_fresh_session()
        
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)
        await get_products(page)
        print(f"Main page: {len(all_product_ids)} products\n")
        
        # Get all URLs
        soup = BeautifulSoup(await page.content(), 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/store/shop/' in href:
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                href = href.split('?')[0]
                all_urls.add(href)
        
        await browser.close()
        await playwright.stop()
        
        urls_list = list(all_urls)
        print(f"Found {len(urls_list)} URLs to crawl\n")
        
        # Crawl with fresh sessions every 15 pages
        session_size = 15
        
        for batch_start in range(0, len(urls_list), session_size):
            batch_end = min(batch_start + session_size, len(urls_list))
            batch = urls_list[batch_start:batch_end]
            
            print(f"\n=== Session {batch_start//session_size + 1}: Crawling URLs {batch_start+1}-{batch_end} ===\n")
            
            playwright, browser, page = await create_fresh_session()
            
            for i, url in enumerate(batch):
                global_idx = batch_start + i + 1
                name = url.split('/')[-1][:40]
                print(f"[{global_idx}/{len(urls_list)}] {name}...", end=" ", flush=True)
                
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    
                    if not await wait_challenge(page):
                        print("blocked/timeout")
                        continue
                    
                    new = await get_products(page)
                    print(f"{new} new (total: {len(all_product_ids)})")
                    
                    # Random human-like delay: 2-7 seconds
                    await asyncio.sleep(random.uniform(2, 7))
                    
                except Exception as e:
                    print(f"error: {str(e)[:30]}")
                
                if global_idx % 50 == 0:
                    print(f"\n>>> {len(all_product_ids):,} products <<<\n")
            
            await browser.close()
            await playwright.stop()
            
            # Cooldown between sessions: 10-20 seconds
            if batch_end < len(urls_list):
                cooldown = random.uniform(10, 20)
                print(f"\n--- Session cooldown: {cooldown:.1f}s ---\n")
                await asyncio.sleep(cooldown)
        
        print(f"\n{'='*60}")
        print(f"URLs crawled: {len(urls_list):,}")
        print(f"Total products: {len(all_product_ids):,}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nFatal error: {e}")

asyncio.run(stealth_enumeration())

