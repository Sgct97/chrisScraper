import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_costco():
    print("=" * 80)
    print("TESTING COSTCO")
    print("=" * 80)
    
    # Test robots.txt first
    url = 'https://www.costco.com/robots.txt'
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"robots.txt Status: {response.status_code}")
            if response.status_code == 200:
                sitemaps = [line for line in response.text.split('\n') if 'sitemap' in line.lower()]
                print(f"Found sitemaps: {sitemaps[:5]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

async def test_homegoods():
    print("=" * 80)
    print("TESTING HOMEGOODS")  
    print("=" * 80)
    
    url = 'https://www.homegoods.com/robots.txt'
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"robots.txt Status: {response.status_code}")
            if response.status_code == 200:
                sitemaps = [line for line in response.text.split('\n') if 'sitemap' in line.lower()]
                print(f"Found sitemaps: {sitemaps[:5]}")
                
                # Try main page
                response2 = await client.get('https://www.homegoods.com')
                print(f"Homepage Status: {response2.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

async def test_tjmaxx():
    print("=" * 80)
    print("TESTING TJ MAXX")
    print("=" * 80)
    
    url = 'https://www.tjmaxx.com/robots.txt'
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"robots.txt Status: {response.status_code}")
            if response.status_code == 200:
                sitemaps = [line for line in response.text.split('\n') if 'sitemap' in line.lower()]
                print(f"Found sitemaps: {sitemaps[:5]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

async def main():
    await test_costco()
    await test_homegoods()
    await test_tjmaxx()

asyncio.run(main())

