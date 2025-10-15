import asyncio
import sys
sys.path.insert(0, '/Users/spensercourville-taylor/htmlfiles/chrisScrapper')

from scrapers.target import TargetScraper
from config import CONFIG
from database import Database
from proxy_manager import ProxyManager  
from browser_manager import BrowserManager
from rate_limiter import RateLimiter

async def test():
    import httpx
    
    api_url = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin=1000006800&pricing_store_id=3991'
    
    print("Testing API call...")
    print(f"URL: {api_url}\n")
    
    async with httpx.AsyncClient(timeout=30, http2=False) as client:
        response = await client.get(api_url)
        print(f"Status: {response.status_code}")
        result = response.json()
    
    if result:
        print(f"✓ Got result, keys: {list(result.keys())}")
        if 'data' in result:
            print(f"  data.product exists: {'product' in result.get('data', {})}")
    else:
        print("✗ No result")

asyncio.run(test())

