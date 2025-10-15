import httpx
import asyncio
from bs4 import BeautifulSoup

async def debug_category():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    # Test a specific category URL
    test_url = 'https://tjmaxx.tjx.com/store/shop/new-arrivals/_/N-842114098'
    
    async with httpx.AsyncClient(timeout=20, http2=False, headers=headers, follow_redirects=True) as client:
        print(f"Testing: {test_url}\n")
        
        try:
            r = await client.get(test_url)
            print(f"Status: {r.status_code}")
            print(f"Final URL: {r.url}")
            print(f"Content length: {len(r.text)}")
            print(f"\nFirst 1000 chars of content:")
            print(r.text[:1000])
            print(f"\n{'='*60}\n")
            
            # Look for product links
            soup = BeautifulSoup(r.text, 'html.parser')
            product_links = soup.find_all('a', href=lambda x: x and '/store/jump/product/' in x)
            
            print(f"Product links found: {len(product_links)}")
            
            if product_links:
                print("\nFirst 5 product links:")
                for link in product_links[:5]:
                    print(f"  {link['href']}")
            else:
                # Show what links ARE there
                all_links = soup.find_all('a', href=True)[:10]
                print(f"\nSample of all links found ({len(soup.find_all('a', href=True))} total):")
                for link in all_links:
                    print(f"  {link['href']}")
                    
        except asyncio.TimeoutError:
            print("TIMEOUT - request took > 20 seconds")
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

asyncio.run(debug_category())

