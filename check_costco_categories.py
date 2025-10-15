import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def check_category_counts():
    """Check major category pages for product counts"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    # Major Costco departments
    categories = [
        'https://www.costco.com/grocery-household.html',
        'https://www.costco.com/appliances.html',
        'https://www.costco.com/home-improvement.html',
        'https://www.costco.com/sports-fitness.html',
        'https://www.costco.com/furniture.html',
        'https://www.costco.com/clothing.html',
        'https://www.costco.com/jewelry.html',
        'https://www.costco.com/health-beauty.html',
        'https://www.costco.com/electronics.html',
        'https://www.costco.com/toys-baby.html',
        'https://www.costco.com/office-products.html',
        'https://www.costco.com/mattresses.html',
        'https://www.costco.com/optical.html',
        'https://www.costco.com/pharmacy.html',
        'https://www.costco.com/tires.html',
    ]
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers) as client:
        print("Checking major category pages...\n")
        
        total_from_categories = 0
        
        for cat_url in categories:
            try:
                r = await client.get(cat_url)
                if r.status_code == 200:
                    # Look for pagination info like "1-24 of 5,234 results"
                    text = r.text
                    
                    # Multiple patterns to catch different formats
                    patterns = [
                        r'of\s+(\d{1,3}(?:,\d{3})*)\s+(?:results|products|items)',
                        r'(\d{1,3}(?:,\d{3})*)\s+(?:results|products|items)\s+found',
                        r'"totalNumRecs":\s*(\d+)',
                        r'"totalResults":\s*(\d+)',
                        r'data-total-products="(\d+)"',
                    ]
                    
                    found_count = None
                    for pattern in patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            # Take the largest number found (most likely the total)
                            numbers = [int(m.replace(',', '')) for m in matches]
                            found_count = max(numbers) if numbers else None
                            break
                    
                    if found_count:
                        total_from_categories += found_count
                        print(f"✓ {cat_url.split('/')[-1]}: {found_count:,} products")
                    else:
                        # Count product links on page
                        soup = BeautifulSoup(text, 'html.parser')
                        product_links = soup.find_all('a', href=lambda x: x and '.product.' in x)
                        print(f"? {cat_url.split('/')[-1]}: {len(product_links)} visible products (no total shown)")
                
                await asyncio.sleep(0.3)  # Be polite
            except Exception as e:
                print(f"✗ {cat_url}: {e}")
        
        print(f"\n{'='*60}")
        print(f"Total from category counts: {total_from_categories:,}")
        print(f"Note: This may have overlap between categories")
        print(f"Sitemap count: 14,860 unique products")
        print(f"{'='*60}")

asyncio.run(check_category_counts())

