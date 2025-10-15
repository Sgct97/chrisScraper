import httpx
import asyncio

async def test_with_better_headers():
    url = 'https://www.costco.com/robots.txt'
    
    # More complete browser-like headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    print(f"Testing Costco with full browser headers...")
    print(f"URL: {url}\n")
    
    try:
        # Try with limits to prevent hanging
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        
        async with httpx.AsyncClient(
            timeout=20,
            http2=False,
            limits=limits,
            follow_redirects=True,
            headers=headers
        ) as client:
            response = await client.get(url)
            print(f"✓ Status: {response.status_code}")
            print(f"✓ HTTP Version: {response.http_version}")
            print(f"✓ Content length: {len(response.text)}")
            print(f"\nFirst 500 chars:")
            print(response.text[:500])
            
    except asyncio.TimeoutError:
        print("✗ TIMEOUT after 20 seconds")
    except httpx.ReadTimeout:
        print("✗ READ TIMEOUT")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

asyncio.run(test_with_better_headers())

