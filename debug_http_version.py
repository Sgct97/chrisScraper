import httpx
import asyncio

async def test_http_versions():
    urls = [
        ('Target', 'https://www.target.com/robots.txt'),
        ('Costco', 'https://www.costco.com/robots.txt'),
    ]
    
    for name, url in urls:
        print(f"\n{'='*60}")
        print(f"{name}: {url}")
        print(f"{'='*60}")
        
        # Test with HTTP/2 disabled
        print("\nWith http2=False:")
        try:
            async with httpx.AsyncClient(timeout=10, http2=False) as client:
                response = await client.get(url)
                print(f"  Status: {response.status_code}")
                print(f"  HTTP Version: {response.http_version}")
                print(f"  Content length: {len(response.text)}")
        except asyncio.TimeoutError:
            print(f"  TIMEOUT")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")
        
        # Test with HTTP/2 enabled (default)
        print("\nWith http2=True (default):")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                print(f"  Status: {response.status_code}")
                print(f"  HTTP Version: {response.http_version}")
                print(f"  Content length: {len(response.text)}")
        except asyncio.TimeoutError:
            print(f"  TIMEOUT")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")

asyncio.run(test_http_versions())

