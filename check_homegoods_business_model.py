import httpx
import asyncio

async def check():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Sec-Fetch-Dest': 'document',
    }
    
    async with httpx.AsyncClient(timeout=15, http2=False, headers=headers, follow_redirects=True) as client:
        r = await client.get('https://www.homegoods.com')
        text = r.text.lower()
        
        print("Checking HomeGoods business model...")
        print(f"Final URL after redirects: {r.url}\n")
        
        indicators = {
            'online shopping': 'shop online' in text or 'buy online' in text or 'add to cart' in text,
            'in-store only': 'in store only' in text or 'stores only' in text,
            'ecommerce': 'checkout' in text or 'shopping cart' in text or 'add to bag' in text,
        }
        
        for indicator, found in indicators.items():
            print(f"  {indicator}: {'✓' if found else '✗'}")
        
        # Check if they mention online shopping
        if 'does not sell online' in text or 'store only' in text:
            print("\n⚠️  HomeGoods appears to be IN-STORE ONLY")

asyncio.run(check())

