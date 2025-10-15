import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def full_enumeration():
    """Comprehensive TJ Maxx enumeration with pagination"""
    
    playwright = await async_playwright().start()
    
    print("Starting comprehensive TJ Maxx enumeration...\n")
    
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
    )
    
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        window.chrome = { runtime: {}, loadTimes: function() {} };
    """)
    
    all_product_ids = set()
    page = await context.new_page()
    
    async def wait_for_challenge_complete():
        """Wait for TJ Maxx challenge to complete"""
        for attempt in range(15):
            await page.wait_for_timeout(1000)
            content = await page.content()
            if 'Challenge Validation' not in content and 'Processing your request' not in content:
                return True
        return False
    
    async def extract_products_from_page():
        """Extract product IDs from current page"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
        
        new_products = 0
        for link in product_links:
            match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if match:
                if match.group(1) not in all_product_ids:
                    all_product_ids.add(match.group(1))
                    new_products += 1
        
        return new_products
    
    try:
        # Main shop page
        print("Loading main shop page...")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)
        
        initial_count = await extract_products_from_page()
        print(f"✓ Main page: {initial_count} products\n")
        
        # Get all category URLs from main page
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        # Focus on unique base category URLs (without filters)
        base_categories = set()
        for link in all_links:
            href = link['href']
            # Match category patterns like /store/shop/women/_/N-1854576536
            match = re.search(r'/store/shop/[^/]+/_/N-(\d+)', href)
            if match:
                cat_id = match.group(1)
                base_url = f'https://tjmaxx.tjx.com/store/shop/_/N-{cat_id}'
                base_categories.add(base_url)
        
        print(f"Found {len(base_categories)} unique base categories\n")
        
        # Crawl categories
        categories_list = list(base_categories)
        categories_to_crawl = min(100, len(categories_list))  # Crawl up to 100 categories
        
        print(f"Crawling {categories_to_crawl} categories...\n")
        
        for i, cat_url in enumerate(categories_list[:categories_to_crawl]):
            cat_name = cat_url.split('N-')[-1][:20]
            print(f"[{i+1}/{categories_to_crawl}] Category {cat_name}...", end=" ", flush=True)
            
            try:
                await page.goto(cat_url, wait_until='domcontentloaded', timeout=15000)
                
                if not await wait_for_challenge_complete():
                    print("⏱️ timeout")
                    continue
                
                new_products = await extract_products_from_page()
                print(f"✓ {new_products} new (total: {len(all_product_ids)})")
                
                # Human-like delay
                await asyncio.sleep(1 + (i % 3))
                
            except Exception as e:
                print(f"✗ {str(e)[:40]}")
                continue
            
            # Progress update every 20 categories
            if (i + 1) % 20 == 0:
                print(f"\n--- Progress: {len(all_product_ids)} unique products so far ---\n")
        
        print(f"\n{'='*60}")
        print(f"FINAL ENUMERATION RESULTS")
        print(f"{'='*60}")
        print(f"Total base categories: {len(base_categories)}")
        print(f"Categories crawled: {categories_to_crawl}")
        print(f"Unique products found: {len(all_product_ids):,}")
        
        if categories_to_crawl < len(base_categories):
            estimated_total = int(len(all_product_ids) * len(base_categories) / categories_to_crawl)
            print(f"Estimated full catalog: ~{estimated_total:,} products")
        
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nError: {e}")
    
    finally:
        await page.close()
        await browser.close()
        await playwright.stop()
        print("\nEnumeration complete.")

asyncio.run(full_enumeration())

