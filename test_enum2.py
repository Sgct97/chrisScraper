import asyncio
import httpx
import gzip

async def test():
    url = 'https://www.target.com/sitemap_pdp-index.xml.gz'
    print(f"Testing: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print("Not 200, returning None")
                return None
            
            print(f"Content length: {len(response.content)}")
            print(f"Trying to decompress...")
            
            try:
                decompressed = gzip.decompress(response.content)
                text = decompressed.decode('utf-8')
                print(f"✓ Decompressed to {len(text)} chars")
                print(text[:500])
            except gzip.BadGzipFile:
                print("Already decompressed, using response.text")
                text = response.text
                print(f"✓ Text length: {len(text)} chars")
                print(text[:500])
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())

