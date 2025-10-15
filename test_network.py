import httpx
import asyncio

async def test_site(name, url):
    print(f"\nTesting {name}: {url}")
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"  ✓ Status: {response.status_code}")
            print(f"  Content length: {len(response.text)}")
            return True
    except httpx.TimeoutException as e:
        print(f"  ✗ Timeout: {e}")
    except httpx.ConnectError as e:
        print(f"  ✗ Connection error: {e}")
    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    return False

async def main():
    # Test basic connectivity first
    print("=" * 80)
    print("TESTING NETWORK CONNECTIVITY")
    print("=" * 80)
    
    await test_site("Google", "https://www.google.com")
    await test_site("Target", "https://www.target.com/robots.txt")
    await test_site("Costco", "https://www.costco.com/robots.txt")
    await test_site("HomeGoods", "https://www.homegoods.com/robots.txt")
    await test_site("TJ Maxx", "https://www.tjmaxx.com/robots.txt")

asyncio.run(main())

