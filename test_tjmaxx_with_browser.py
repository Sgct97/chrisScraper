import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from config import CONFIG
from proxy_manager import ProxyManager
from browser_manager import BrowserManager
from bs4 import BeautifulSoup
import re

async def test_with_browser():
    """Test TJ Maxx with full Playwright browser + stealth"""
    
    # Try with Firefox instead of Chromium to avoid HTTP/2 issues
    from playwright.async_api import async_playwright
    
    playwright = await async_playwright().start()
    
    print("Launching Firefox with stealth settings...\n")
    
    browser = await playwright.firefox.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
        ]
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-US',
        timezone_id='America/Los_Angeles',
    )
    
    # Add stealth script
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        window.chrome = {
            runtime: {},
        };
    """)
    
    print("Testing TJ Maxx with Playwright + Stealth...\n")
    
    # Test URLs
    test_urls = [
        ('Main Shop', 'https://tjmaxx.tjx.com/store/shop'),
        ('New Arrivals', 'https://tjmaxx.tjx.com/store/shop/new-arrivals/_/N-842114098'),
        ('Women Category', 'https://tjmaxx.tjx.com/store/shop/women/_/N-1854576536'),
    ]
    
    for name, url in test_urls:
        print(f"{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        try:
            page = await context.new_page()
            
            # Set headers
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            # Add extra delays to seem more human
            await page.wait_for_timeout(2000)  # 2 second delay before navigation
            
            # Navigate to page
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            print(f"Status: {response.status}")
            print(f"Final URL: {page.url}")
            
            # Wait for content to load
            await page.wait_for_timeout(3000)
            
            # Get page content
            content = await page.content()
            print(f"Content length: {len(content)}")
            
            # Check for bot challenge
            if 'Challenge Validation' in content or 'challenge' in content.lower():
                print("❌ BOT CHALLENGE DETECTED\n")
                
                # Take screenshot for debugging
                await page.screenshot(path=f'debug_tjmaxx_{name.replace(" ", "_")}.png')
                print(f"   Screenshot saved: debug_tjmaxx_{name.replace(' ', '_')}.png")
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
        
        # Be polite - wait between requests
        await asyncio.sleep(3)
    
    await browser.close()
    await playwright.stop()
    print("\nBrowser test complete.")

asyncio.run(test_with_browser())

