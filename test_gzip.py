import httpx
import gzip
import asyncio

async def test_gzip():
    url = 'https://www.target.com/sitemap_pdp-index.xml.gz'
    print(f"Testing gzip: {url}\n")
    
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Content-Length: {len(response.content)} bytes")
            print(f"Content-Type: {response.headers.get('content-type')}")
            
            if response.status_code == 200:
                # Decompress
                decompressed = gzip.decompress(response.content)
                text = decompressed.decode('utf-8')
                print(f"\nDecompressed length: {len(text)} chars")
                print(f"\nFirst 1000 chars:")
                print(text[:1000])
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_gzip())

