"""
Costco scraper - Stealth browser with Cloudflare bypass, public data only.
"""

from typing import List, Dict, Optional, Any, AsyncGenerator
from bs4 import BeautifulSoup
import json
import re
from .base import BaseScraper


class CostcoScraper(BaseScraper):
    """Costco.com scraper - public data only, no membership."""
    
    def __init__(self, config, database, browser_manager, rate_limiter, proxy_manager):
        super().__init__(config, database, browser_manager, rate_limiter, proxy_manager)
        self.retailer_name = 'costco'
        from config import RETAILERS
        self.base_url = RETAILERS['costco']['base_url']
        self.sitemap_url = RETAILERS['costco']['sitemap_url']
    
    async def enumerate_products(self) -> AsyncGenerator[Dict[str, str], None]:
        """
        Enumerate Costco products (streaming):
        1. Multiple sitemap indexes
        2. Category pagination validation
        """
        seen_ids = set()
        
        # Costco has multiple sitemap indexes - check both
        sitemap_indexes = [
            'https://www.costco.com/sitemap_index.xml',
            'https://www.costco.com/sitemap_lw_index.xml',
        ]
        
        print(f"\n[{self.retailer_name}] Method 1: Sitemap enumeration...")
        
        for index_url in sitemap_indexes:
            print(f"\n  Checking: {index_url}")
            self.sitemap_url = index_url
            
            # Dedupe across indexes
            async for product in self._enumerate_sitemap():
                if product['product_id'] not in seen_ids:
                    seen_ids.add(product['product_id'])
                    yield product
    
    async def _enumerate_sitemap(self) -> AsyncGenerator[Dict[str, str], None]:
        """Parse Costco sitemap (streaming)."""
        html = await self.fetch_html(self.sitemap_url)
        if not html:
            print(f"  ✗ Failed to fetch sitemap")
            return
        
        soup = BeautifulSoup(html, 'xml')
        
        # Check for sitemap index
        sitemaps = soup.find_all('sitemap')
        
        if sitemaps:
            # Multiple sitemaps
            print(f"  Found {len(sitemaps)} sitemap files...")
            for idx, sitemap_tag in enumerate(sitemaps):  # Parse ALL sitemaps
                loc = sitemap_tag.find('loc')
                if not loc:
                    continue
                
                sitemap_url = loc.text.strip()
                
                # Fetch sitemap (don't filter by URL - check contents instead)
                sitemap_html = await self.fetch_html(sitemap_url)
                if sitemap_html:
                    sitemap_soup = BeautifulSoup(sitemap_html, 'xml')
                    urls = sitemap_soup.find_all('url')
                    
                    for url_tag in urls:
                        loc_tag = url_tag.find('loc')
                        if loc_tag:
                            url = loc_tag.text.strip()
                            # Only include URLs with .product. in them
                            if '.product.' in url.lower():
                                item_id = self._extract_item_id(url)
                                if item_id:
                                    yield {
                                        'product_id': item_id,
                                        'product_url': url,
                                        'method': 'sitemap'
                                    }
                    
                    print(f"    Parsed sitemap {idx+1}: {len(urls)} URLs")
        else:
            # Single sitemap
            urls = soup.find_all('url')
            for url_tag in urls:
                loc = url_tag.find('loc')
                if loc:
                    url = loc.text.strip()
                    item_id = self._extract_item_id(url)
                    if item_id:
                        yield {
                            'product_id': item_id,
                            'product_url': url,
                            'method': 'sitemap'
                        }
    
    def _extract_item_id(self, url: str) -> Optional[str]:
        """Extract Costco item number from URL."""
        # URL format: https://www.costco.com/product-name.product.12345.html
        match = re.search(r'\.product\.(\d+)\.html', url)
        if match:
            return match.group(1)
        return None
    
    async def scrape_product(self, product_url: str, product_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Scrape Costco product page (public data only).
        Note: Uses browser to handle Cloudflare protection.
        """
        try:
            context = await self.browser_manager.create_context(self.retailer_name)
            page = await self.browser_manager.new_page(context)
            
            await self.rate_limiter.wait(self.retailer_name)
            
            response = await page.goto(product_url, wait_until='networkidle', timeout=45000)
            
            if not response or response.status in [403, 429]:
                self.proxy_manager.record_request(success=False, is_block=True)
                await self.browser_manager.close_context(context)
                return None
            
            if response.status == 404:
                await self.browser_manager.close_context(context)
                return {'status': 'not_found'}
            
            # Wait for content to load (Cloudflare check)
            await page.wait_for_timeout(2000)
            
            # Check for Cloudflare challenge
            page_content = await page.content()
            if 'cf-browser-verification' in page_content or 'Checking your browser' in page_content:
                print(f"  ⚠️  Cloudflare challenge detected")
                self.proxy_manager.record_request(success=False, is_block=True)
                await self.browser_manager.close_context(context)
                return None
            
            html = page_content
            await self.browser_manager.close_context(context)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Parse product data
            product = self._parse_html(soup, product_url, product_id)
            if product:
                self.proxy_manager.record_request(success=True, is_block=False)
            
            return product
            
        except Exception as e:
            print(f"  Error scraping {product_url}: {e}")
            return None
    
    def _parse_html(self, soup: BeautifulSoup, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse Costco product page HTML."""
        try:
            # Try JSON-LD first
            json_ld = self.parse_json_ld(soup)
            if json_ld and json_ld.get('@type') == 'Product':
                offers = json_ld.get('offers', {})
                price = offers.get('price')
                availability = offers.get('availability', '')
                
                return {
                    'product_id': product_id or json_ld.get('sku'),
                    'retailer': self.retailer_name,
                    'product_url': product_url,
                    'title': json_ld.get('name'),
                    'brand': json_ld.get('brand', {}).get('name') if isinstance(json_ld.get('brand'), dict) else json_ld.get('brand'),
                    'price_current': self.clean_price(str(price)) if price else None,
                    'currency': 'USD',
                    'availability': 'in_stock' if 'InStock' in availability else 'out_of_stock',
                    'description': json_ld.get('description'),
                    'image_urls': [json_ld.get('image')] if json_ld.get('image') else [],
                    'ratings_average': json_ld.get('aggregateRating', {}).get('ratingValue'),
                    'ratings_count': json_ld.get('aggregateRating', {}).get('reviewCount'),
                    'status': 'success'
                }
            
            # Fallback: Manual HTML parsing
            title_tag = soup.find('h1', {'itemprop': 'name'}) or soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else None
            
            # Price (may be hidden for members)
            price_tag = soup.find('span', {'class': re.compile('value|price', re.I)})
            price_text = price_tag.get_text(strip=True) if price_tag else None
            
            # Check if price is member-only
            member_only = soup.find(text=re.compile('sign in|member price', re.I))
            availability = 'member_only' if member_only else 'in_stock'
            
            # Images
            image_urls = self.extract_images(soup, [
                'img[itemprop="image"]',
                'img.product-image',
                'div.product-image-container img'
            ])
            
            # Description
            desc_tag = soup.find('div', {'itemprop': 'description'}) or soup.find('div', {'class': re.compile('description', re.I)})
            description = desc_tag.get_text(strip=True) if desc_tag else None
            
            return {
                'product_id': product_id,
                'retailer': self.retailer_name,
                'product_url': product_url,
                'title': title,
                'price_current': self.clean_price(price_text) if price_text else None,
                'currency': 'USD',
                'availability': availability,
                'description': description,
                'image_urls': image_urls,
                'status': 'success' if title else 'partial_data'
            }
            
        except Exception as e:
            print(f"  Error parsing HTML: {e}")
            return None

