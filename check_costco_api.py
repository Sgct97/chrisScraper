import httpx
import asyncio
from bs4 import BeautifulSoup
import json

async def check_for_product_apis():
    """Check if Costco has product APIs or other enumeration methods"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers) as client:
        
        # 1. Check robots.txt thoroughly
        print("1. Checking robots.txt for hints...")
        r = await client.get('https://www.costco.com/robots.txt')
        robots = r.text
        
        # Look for any API or data endpoints
        lines = [line for line in robots.split('\n') if 'api' in line.lower() or 'json' in line.lower() or 'data' in line.lower()]
        if lines:
            print(f"  Found API-related lines: {lines}")
        else:
            print(f"  No API hints in robots.txt")
        
        # 2. Try common product API endpoints
        print("\n2. Testing common API endpoints...")
        api_tests = [
            'https://www.costco.com/api/products',
            'https://www.costco.com/api/catalog',
            'https://www.costco.com/api/search',
            'https://api.costco.com/products',
            'https://www.costco.com/rest/v2/products',
            'https://www.costco.com/catalog.json',
        ]
        
        for api_url in api_tests:
            try:
                r = await client.get(api_url)
                if r.status_code == 200:
                    print(f"  ✓ FOUND: {api_url} (Status: {r.status_code})")
                    print(f"    Content type: {r.headers.get('content-type')}")
                    print(f"    First 200 chars: {r.text[:200]}")
            except:
                pass
        
        # 3. Check main page for total product count
        print("\n3. Checking main page source...")
        r = await client.get('https://www.costco.com')
        if r.status_code == 200:
            import re
            # Look for JSON data with product counts
            json_patterns = [
                r'"totalProducts":\s*(\d+)',
                r'"productCount":\s*(\d+)',
                r'"total":\s*(\d+)',
                r'data-product-count="(\d+)"',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, r.text)
                if matches:
                    print(f"  Found potential counts: {matches}")
        
        # 4. Try search with wildcard
        print("\n4. Testing search functionality...")
        search_url = 'https://www.costco.com/CatalogSearch?keyword=*'
        try:
            r = await client.get(search_url)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # Look for result count
                text = r.text
                result_patterns = [
                    r'(\d{1,3}(?:,\d{3})*)\s+(?:results|products|items)',
                    r'of\s+(\d{1,3}(?:,\d{3})*)\s+(?:results|products|items)',
                ]
                
                for pattern in result_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"  Search results show: {matches}")
        except Exception as e:
            print(f"  Search error: {e}")

asyncio.run(check_for_product_apis())

