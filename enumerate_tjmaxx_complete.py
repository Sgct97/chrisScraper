import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def enumerate_tjmaxx():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        
        print("Enumerating TJ Maxx products...\n")
        
        # Get main shop page
        r = await client.get('https://tjmaxx.tjx.com/store/shop')
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find all category links
        category_patterns = [
            r'/store/shop/_/N-\d+',
            r'/store/jump/topic/[^/]+/\d+',
        ]
        
        all_links = soup.find_all('a', href=True)
        category_urls = set()
        
        for link in all_links:
            href = link['href']
            if any(re.search(pattern, href) for pattern in category_patterns):
                if href.startswith('/'):
                    href = 'https://tjmaxx.tjx.com' + href
                category_urls.add(href)
        
        print(f"Found {len(category_urls)} category URLs\n")
        
        # Sample a few categories to understand pagination and product counts
        all_product_ids = set()
        
        sample_cats = list(category_urls)[:5]  # Sample first 5
        
        for i, cat_url in enumerate(sample_cats):
            print(f"\n{i+1}. Checking: {cat_url}")
            
            try:
                r = await client.get(cat_url)
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Look for product count in page
                text = r.text
                count_patterns = [
                    r'(\d{1,3}(?:,\d{3})*)\s+(?:products|items|results)',
                    r'of\s+(\d{1,3}(?:,\d{3})*)\s+(?:products|items|results)',
                    r'"totalNumRecs":\s*(\d+)',
                ]
                
                for pattern in count_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"   Found count indicator: {matches}")
                        break
                
                # Count products on this page
                product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
                
                for link in product_links:
                    href = link['href']
                    # Extract product ID
                    match = re.search(r'/store/jump/product/[^/]+/(\d+)', href)
                    if match:
                        all_product_ids.add(match.group(1))
                
                print(f"   Products on page: {len(product_links)}")
                print(f"   Running unique total: {len(all_product_ids)}")
                
                await asyncio.sleep(0.5)  # Be polite
                
            except Exception as e:
                print(f"   Error: {e}")
        
        print(f"\n{'='*60}")
        print(f"Sample enumeration: {len(all_product_ids)} unique products from 5 categories")
        print(f"Total categories: {len(category_urls)}")
        print(f"Estimated total: ~{len(all_product_ids) * len(category_urls) // 5:,} products")
        print(f"{'='*60}")

asyncio.run(enumerate_tjmaxx())

