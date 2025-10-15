import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def enumerate_tjmaxx():
    """Enumerate TJ Maxx products using Playwright with stealth"""
    
    playwright = await async_playwright().start()
    
    print("Launching browser for TJ Maxx enumeration...\n")
    
    # Launch browser
    browser = await playwright.chromium.launch(
        headless=False,  # Visible browser bypasses bot detection
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-first-run',
            '--no-default-browser-check',
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/Los_Angeles',
    )
    
    # Stealth script
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
        };
    """)
    
    all_product_ids = set()
    page = await context.new_page()
    
    try:
        # 1. Get main shop page
        print("Step 1: Loading main shop page...")
        await page.goto('https://tjmaxx.tjx.com/store/shop', wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(3000)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract products from main page
        product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
        for link in product_links:
            match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
            if match:
                all_product_ids.add(match.group(1))
        
        print(f"  Found {len(all_product_ids)} products on main page\n")
        
        # 2. Find category links
        print("Step 2: Finding category pages...")
        all_links = soup.find_all('a', href=True)
        category_urls = []
        
        for link in all_links:
            href = link['href']
            # Look for category patterns
            if '/_/N-' in href and 'tjmaxx.tjx.com' in href:
                if href not in category_urls:
                    category_urls.append(href)
            elif href.startswith('/store/shop/') and '/_/N-' in href:
                full_url = 'https://tjmaxx.tjx.com' + href
                if full_url not in category_urls:
                    category_urls.append(full_url)
        
        print(f"  Found {len(category_urls)} category URLs\n")
        
        # 3. Crawl categories (sample first 20 to estimate)
        print("Step 3: Crawling category pages...")
        categories_to_test = min(20, len(category_urls))
        
        for i, cat_url in enumerate(category_urls[:categories_to_test]):
            print(f"  [{i+1}/{categories_to_test}] {cat_url.split('/')[-1][:50]}...")
            
            try:
                await page.goto(cat_url, wait_until='domcontentloaded', timeout=15000)
                
                # Wait for challenge to complete (up to 15 seconds)
                for attempt in range(15):
                    await page.wait_for_timeout(1000)  # Wait 1 second
                    content = await page.content()
                    
                    # Check if challenge is still running
                    if 'Challenge Validation' not in content and 'Processing your request' not in content:
                        # Challenge completed!
                        break
                else:
                    # Timeout waiting for challenge
                    print(f"      ⏱️  Challenge timeout")
                    continue
                
                # Double-check we have real content
                if 'Challenge Validation' in content or 'Processing your request' in content:
                    print(f"      ❌ Challenge didn't complete")
                    continue
                
                soup = BeautifulSoup(content, 'html.parser')
                product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
                
                page_products = 0
                for link in product_links:
                    match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
                    if match:
                        if match.group(1) not in all_product_ids:
                            all_product_ids.add(match.group(1))
                            page_products += 1
                
                print(f"      ✓ {page_products} new products (total: {len(all_product_ids)})")
                
                # Human-like delay
                await asyncio.sleep(2 + (hash(cat_url) % 3))
                
            except Exception as e:
                print(f"      ✗ Error: {str(e)[:60]}")
                continue
        
        print(f"\n{'='*60}")
        print(f"ENUMERATION RESULTS")
        print(f"{'='*60}")
        print(f"Categories crawled: {categories_to_test} out of {len(category_urls)}")
        print(f"Unique products found: {len(all_product_ids)}")
        
        if categories_to_test < len(category_urls):
            estimated_total = int(len(all_product_ids) * len(category_urls) / categories_to_test)
            print(f"Estimated total products: ~{estimated_total:,}")
        
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\nFatal error: {e}")
    
    finally:
        await page.close()
        await browser.close()
        await playwright.stop()
        print("\nEnumeration complete.")

asyncio.run(enumerate_tjmaxx())

