import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def find_categories():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        
        print("Finding TJ Maxx product categories...\n")
        
        # Get main shop page
        r = await client.get('https://tjmaxx.tjx.com/store/shop')
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for navigation/menu with categories
        # TJX sites typically have category nav
        
        # Method 1: Look in navigation
        nav_elements = soup.find_all(['nav', 'div'], class_=re.compile('nav|menu|category', re.I))
        
        print("Navigation elements found:", len(nav_elements))
        
        # Method 2: Look for links with "shop" in them that have product indicators
        all_links = soup.find_all('a', href=True)
        
        potential_categories = {}
        
        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Look for department/category links
            if '/store/shop/' in href or '_/N-' in href:
                if text and len(text) > 2 and len(text) < 50:  # Reasonable category name length
                    if href.startswith('/'):
                        href = 'https://tjmaxx.tjx.com' + href
                    potential_categories[text] = href
        
        print(f"\nFound {len(potential_categories)} potential product categories:\n")
        
        for i, (name, url) in enumerate(list(potential_categories.items())[:15]):
            print(f"{i+1}. {name}")
            print(f"   {url}")
        
        # Now test a few to see if they have products
        print(f"\n{'='*60}")
        print("Testing categories for products...")
        print(f"{'='*60}\n")
        
        all_product_ids = set()
        
        for i, (name, url) in enumerate(list(potential_categories.items())[:10]):
            try:
                r2 = await client.get(url)
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                
                # Count products
                product_links = soup2.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
                
                if product_links:
                    print(f"{name}: {len(product_links)} products on page")
                    
                    # Extract IDs
                    for link in product_links:
                        match = re.search(r'/store/jump/product/[^/]+/(\d+)', link['href'])
                        if match:
                            all_product_ids.add(match.group(1))
                
                await asyncio.sleep(0.3)
                
            except Exception as e:
                print(f"{name}: Error - {e}")
        
        print(f"\n{'='*60}")
        print(f"Found {len(all_product_ids)} unique products from first 10 categories")
        print(f"Total potential categories: {len(potential_categories)}")
        print(f"{'='*60}")

asyncio.run(find_categories())

