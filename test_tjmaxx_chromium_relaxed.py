import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

async def test_with_chromium():
    """Test TJ Maxx with Chromium using relaxed loading and more human-like behavior"""
    
    playwright = await async_playwright().start()
    
    print("Launching Chromium with enhanced stealth...\n")
    
    # Launch with more realistic browser args
    browser = await playwright.chromium.launch(
        headless=False,  # Try with visible browser first
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-infobars',
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/Los_Angeles',
        extra_http_headers={
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }
    )
    
    # Enhanced stealth script
    await context.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Add chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    # Test URLs
    test_urls = [
        ('Main Shop', 'https://tjmaxx.tjx.com/store/shop'),
        ('New Arrivals', 'https://tjmaxx.tjx.com/store/shop/new-arrivals/_/N-842114098'),
    ]
    
    for name, url in test_urls:
        print(f"{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        try:
            page = await context.new_page()
            
            # Human-like behavior: wait before navigating
            await page.wait_for_timeout(1000 + (hash(url) % 2000))  # Random 1-3s
            
            # Navigate with 'domcontentloaded' instead of 'networkidle' to avoid HTTP/2 issues
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                print(f"Status: {response.status if response else 'N/A'}")
            except Exception as nav_error:
                print(f"Navigation error: {nav_error}")
                # Try continuing anyway
                await page.wait_for_timeout(5000)
            
            print(f"Final URL: {page.url}")
            
            # Wait for dynamic content
            await page.wait_for_timeout(3000)
            
            # Get page content
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            # Check for bot challenge
            if 'Challenge Validation' in content or 'cf-challenge' in content:
                print("❌ BOT CHALLENGE DETECTED")
                
                # Save for inspection
                with open(f'debug_{name.replace(" ", "_")}.html', 'w') as f:
                    f.write(content)
                print(f"   HTML saved to: debug_{name.replace(' ', '_')}.html")
            else:
                print("✅ No challenge detected!")
                
                # Count products
                soup = BeautifulSoup(content, 'html.parser')
                product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
                
                # Extract unique IDs
                product_ids = set()
                for link in product_links:
                    match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
                    if match:
                        product_ids.add(match.group(1))
                
                print(f"   Products found: {len(product_ids)} unique")
                
                if product_ids:
                    samples = list(product_ids)[:3]
                    print(f"   Sample IDs: {samples}")
            
            await page.close()
            print()
            
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}\n")
        
        # Human-like delay between requests
        await asyncio.sleep(5)
    
    await browser.close()
    await playwright.stop()
    print("\nBrowser test complete.")

asyncio.run(test_with_chromium())

