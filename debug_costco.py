import httpx
import asyncio
from bs4 import BeautifulSoup

async def test_costco_sitemap():
    url = 'https://www.costco.com/sitemap_lw_index.xml'
    print(f"Fetching: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, http2=False) as client:
            response = await client.get(url)
            print(f"Status: {response.status_code}")
            print(f"Length: {len(response.text)} chars")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                sitemaps = soup.find_all('sitemap')
                locs = soup.find_all('loc')
                
                print(f"Found {len(sitemaps)} sitemap tags")
                print(f"Found {len(locs)} loc tags")
                
                print("\nFirst 10 URLs:")
                for i, loc in enumerate(locs[:10]):
                    print(f"  {i+1}. {loc.text.strip()}")
                    
                # Check if these are product URLs or more sitemap indexes
                if locs:
                    first_url = locs[0].text.strip()
                    print(f"\nTesting first sitemap: {first_url}")
                    r2 = await client.get(first_url)
                    print(f"  Status: {r2.status_code}")
                    print(f"  Length: {len(r2.text)} chars")
                    soup2 = BeautifulSoup(r2.text, 'xml')
                    urls2 = soup2.find_all('url')
                    print(f"  Contains {len(urls2)} product URLs")
                    if urls2:
                        print(f"  Sample URL: {urls2[0].find('loc').text if urls2[0].find('loc') else 'N/A'}")
                    
    except asyncio.TimeoutError:
        print("TIMEOUT after 15 seconds")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

asyncio.run(test_costco_sitemap())

