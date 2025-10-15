import httpx
import asyncio

async def test_sitemap():
    url = 'https://www.target.com/sitemap_products.xml'
    print(f"Testing: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"\nFirst 1000 chars:")
            print(response.text[:1000])
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == '__main__':
    asyncio.run(test_sitemap())

