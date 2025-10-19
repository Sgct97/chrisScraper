"""
Base scraper class with common functionality.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import httpx
from bs4 import BeautifulSoup
import json
import re


class BaseScraper(ABC):
    """Abstract base class for all retailer scrapers."""
    
    def __init__(self, config: Dict, database, browser_manager, rate_limiter, proxy_manager):
        self.config = config
        self.database = database
        self.browser_manager = browser_manager
        self.rate_limiter = rate_limiter
        self.proxy_manager = proxy_manager
        self.retailer_name = None  # Set by subclass
        
    @abstractmethod
    async def enumerate_products(self) -> List[Dict[str, str]]:
        """
        Enumerate all products using multiple methods.
        Returns list of dicts with 'product_id', 'product_url', 'method'
        """
        pass
    
    @abstractmethod
    async def scrape_product(self, product_url: str, product_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Scrape a single product page.
        Returns product data dict or None if failed.
        """
        pass
    
    async def fetch_html(self, url: str, use_browser: bool = False) -> Optional[str]:
        """Fetch HTML content via httpx or Playwright."""
        await self.rate_limiter.wait(self.retailer_name)
        
        try:
            if use_browser:
                context = await self.browser_manager.create_context(self.retailer_name)
                page = await self.browser_manager.new_page(context)
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                html = await page.content()
                await self.browser_manager.close_context(context)
                return html
            else:
                # Use httpx for lighter requests (HTTP/1.1 to avoid protocol errors)
                proxy_url = self.proxy_manager.get_proxy_url() if self.proxy_manager.is_enabled() else None
                client_kwargs = {'timeout': 30, 'follow_redirects': True, 'http2': False}
                if proxy_url:
                    client_kwargs['proxy'] = proxy_url
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in [403, 429]:
                        print(f"  ⚠️  fetch_html blocked: HTTP {response.status_code}")
                        # Record as blocked
                        self.proxy_manager.record_request(success=False, is_block=True)
                        return None
                    else:
                        print(f"  ⚠️  fetch_html HTTP {response.status_code} from {url[:60]}")
                        return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    async def fetch_json(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Fetch JSON data via httpx."""
        await self.rate_limiter.wait(self.retailer_name)
        
        try:
            proxy_url = self.proxy_manager.get_proxy_url() if self.proxy_manager.is_enabled() else None
            client_kwargs = {'timeout': 30, 'follow_redirects': True, 'http2': False}
            if proxy_url:
                client_kwargs['proxy'] = proxy_url
            
            request_headers = self._get_headers()
            if headers:
                # Merge headers, with custom headers taking precedence
                # Handle case-insensitive header keys (HTTP standard)
                for key, value in headers.items():
                    # Remove any existing header with same key (case-insensitive)
                    keys_to_remove = [k for k in request_headers.keys() if k.lower() == key.lower()]
                    for k in keys_to_remove:
                        del request_headers[k]
                    # Add the new header
                    request_headers[key] = value
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url, headers=request_headers)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 407:
                    # Proxy authentication error - log details
                    proxy_used = client_kwargs.get('proxy', 'None')
                    if proxy_used and isinstance(proxy_used, str):
                        # Sanitize password from proxy URL for logging
                        import re
                        sanitized = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', proxy_used)
                    else:
                        sanitized = str(proxy_used)
                    print(f"\n{'='*80}")
                    print(f"🚨 PROXY AUTH ERROR (407)")
                    print(f"{'='*80}")
                    print(f"Proxy: {sanitized}")
                    print(f"URL: {url[:100]}")
                    print(f"Response: {response.text[:200] if response.text else 'No body'}")
                    print(f"{'='*80}\n")
                    self.proxy_manager.record_request(success=False, is_block=True)
                    return None
                elif response.status_code in [403, 429]:
                    print(f"  ⚠️  Blocked: HTTP {response.status_code} from {url[:80]}")
                    self.proxy_manager.record_request(success=False, is_block=True)
                    return None
                else:
                    print(f"  ⚠️  HTTP {response.status_code} from {url[:80]}")
                    return None
        except httpx.ProxyError as e:
            proxy_used = client_kwargs.get('proxy', 'None')
            if proxy_used and isinstance(proxy_used, str):
                import re
                sanitized = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', proxy_used)
            else:
                sanitized = str(proxy_used)
            print(f"\n{'='*80}")
            print(f"🚨 PROXY CONNECTION ERROR")
            print(f"{'='*80}")
            print(f"Proxy: {sanitized}")
            print(f"Error: {str(e)[:300]}")
            print(f"URL: {url[:100]}")
            print(f"{'='*80}\n")
            self.proxy_manager.record_request(success=False, is_block=True)
            return None
        except Exception as e:
            print(f"  ⚠️  Exception fetching JSON from {url[:80]}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def post_json(self, url: str, data: Dict, headers: Dict = None) -> Optional[Dict]:
        """POST JSON data and get response."""
        await self.rate_limiter.wait(self.retailer_name)
        
        try:
            proxy_url = self.proxy_manager.get_proxy_url() if self.proxy_manager.is_enabled() else None
            client_kwargs = {'timeout': 30, 'follow_redirects': True, 'http2': False}
            if proxy_url:
                client_kwargs['proxy'] = proxy_url
            
            request_headers = self._get_headers()
            request_headers['Content-Type'] = 'application/json'
            if headers:
                request_headers.update(headers)
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.post(url, json=data, headers=request_headers)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [403, 429]:
                    self.proxy_manager.record_request(success=False, is_block=True)
                    return None
                else:
                    return None
        except Exception as e:
            print(f"Error posting to {url}: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common HTTP headers with full browser fingerprint."""
        import random
        return {
            'User-Agent': random.choice(self.config['user_agents']),
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
    
    def extract_images(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extract image URLs from page using multiple selectors."""
        image_urls = []
        
        for selector in selectors:
            images = soup.select(selector)
            for img in images:
                url = img.get('src') or img.get('data-src') or img.get('data-original')
                if url and url.startswith('http'):
                    image_urls.append(url)
        
        return list(set(image_urls))  # Remove duplicates
    
    def clean_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price from string."""
        if not price_str:
            return None
        
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_str.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except:
                return None
        return None
    
    def parse_json_ld(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract JSON-LD structured data."""
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                return data
            except:
                continue
        return None

