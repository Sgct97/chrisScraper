"""
TJ Maxx scraper - Similar to HomeGoods (TJX Companies).
"""

from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import json
import re
from .base import BaseScraper


class TJMaxxScraper(BaseScraper):
    """TJMaxx.com scraper - category pagination approach."""
    
    def __init__(self, config, database, browser_manager, rate_limiter, proxy_manager):
        super().__init__(config, database, browser_manager, rate_limiter, proxy_manager)
        self.retailer_name = 'tjmaxx'
        self.base_url = 'https://www.tjmaxx.com'
    
    async def enumerate_products(self) -> List[Dict[str, str]]:
        """
        Enumerate TJ Maxx products via category crawling.
        High churn expected - many 404s normal for discount retailer.
        """
        products = []
        
        print(f"\n[{self.retailer_name}] Method 1: Category crawl...")
        category_products = await self._enumerate_categories()
        products.extend(category_products)
        self.database.insert_enumeration_count(
            self.retailer_name,
            'category_crawl',
            len(category_products),
            "Crawled all category pages - high churn expected"
        )
        print(f"  ✓ Found {len(category_products):,} products from categories")
        
        return products
    
    async def _enumerate_categories(self) -> List[Dict[str, str]]:
        """Crawl category pages to enumerate products."""
        products = []
        
        shop_url = f"{self.base_url}/store/shop"
        
        try:
            html = await self.fetch_html(shop_url, use_browser=True)
            if not html:
                print(f"  ✗ Failed to fetch shop page")
                return products
            
            soup = BeautifulSoup(html, 'html.parser')
            
            category_links = self._extract_category_links(soup)
            print(f"  Found {len(category_links)} categories to crawl")
            
            for idx, cat_url in enumerate(category_links):  # Parse ALL categories
                print(f"    Crawling category {idx+1}/{len(category_links)}: {cat_url}")
                cat_products = await self._crawl_category_page(cat_url)
                products.extend(cat_products)
            
        except Exception as e:
            print(f"  Error enumerating categories: {e}")
        
        return products
    
    def _extract_category_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract category links from page."""
        links = []
        
        nav_links = soup.select('a[href*="/category/"], a[href*="/shop/"]')
        for link in nav_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    href = self.base_url + href
                if href not in links:
                    links.append(href)
        
        return links
    
    async def _crawl_category_page(self, category_url: str, max_pages: int = 10) -> List[Dict[str, str]]:
        """Crawl a category page and all pagination."""
        products = []
        
        for page_num in range(1, max_pages + 1):
            page_url = f"{category_url}?page={page_num}" if '?' not in category_url else f"{category_url}&page={page_num}"
            
            html = await self.fetch_html(page_url, use_browser=True)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            
            product_cards = soup.select('div[data-product-id], article.product, div.product-tile')
            
            if not product_cards:
                break
            
            for card in product_cards:
                link = card.find('a', href=True)
                product_id_attr = card.get('data-product-id') or card.get('data-sku')
                
                if link:
                    href = link['href']
                    if href.startswith('/'):
                        href = self.base_url + href
                    
                    product_id = product_id_attr or self._extract_id_from_url(href)
                    
                    if product_id:
                        products.append({
                            'product_id': product_id,
                            'product_url': href,
                            'method': 'category_crawl'
                        })
        
        return products
    
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        """Extract product ID from URL."""
        patterns = [
            r'/product/(\d+)',
            r'/p/(\d+)',
            r'pid=(\d+)',
            r'/(\d{6,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def scrape_product(self, product_url: str, product_id: str = None) -> Optional[Dict[str, Any]]:
        """Scrape TJ Maxx product page."""
        try:
            context = await self.browser_manager.create_context(self.retailer_name)
            page = await self.browser_manager.new_page(context)
            
            await self.rate_limiter.wait(self.retailer_name)
            
            response = await page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
            
            if not response or response.status in [403, 429]:
                self.proxy_manager.record_request(success=False, is_block=True)
                await self.browser_manager.close_context(context)
                return None
            
            if response.status == 404:
                # Expected for discount retailer with high inventory churn
                await self.browser_manager.close_context(context)
                return {'status': 'not_found'}
            
            await page.wait_for_timeout(1000)
            
            html = await page.content()
            await self.browser_manager.close_context(context)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            product = self._parse_html(soup, product_url, product_id)
            if product:
                self.proxy_manager.record_request(success=True, is_block=False)
            
            return product
            
        except Exception as e:
            print(f"  Error scraping {product_url}: {e}")
            return None
    
    def _parse_html(self, soup: BeautifulSoup, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse TJ Maxx product page."""
        try:
            # Try JSON-LD
            json_ld = self.parse_json_ld(soup)
            if json_ld and json_ld.get('@type') == 'Product':
                offers = json_ld.get('offers', {})
                return {
                    'product_id': product_id or json_ld.get('sku'),
                    'retailer': self.retailer_name,
                    'product_url': product_url,
                    'title': json_ld.get('name'),
                    'brand': json_ld.get('brand', {}).get('name') if isinstance(json_ld.get('brand'), dict) else json_ld.get('brand'),
                    'price_current': self.clean_price(str(offers.get('price'))),
                    'currency': 'USD',
                    'availability': 'in_stock' if 'InStock' in offers.get('availability', '') else 'out_of_stock',
                    'description': json_ld.get('description'),
                    'image_urls': [json_ld.get('image')] if json_ld.get('image') else [],
                    'category': json_ld.get('category'),
                    'status': 'success'
                }
            
            # Fallback: HTML parsing
            title_tag = soup.find('h1', {'class': re.compile('product-title|product-name', re.I)}) or soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else None
            
            price_tag = soup.find('span', {'class': re.compile('price|product-price', re.I)})
            price_text = price_tag.get_text(strip=True) if price_tag else None
            
            brand_tag = soup.find('span', {'class': re.compile('brand', re.I)})
            brand = brand_tag.get_text(strip=True) if brand_tag else None
            
            image_urls = self.extract_images(soup, [
                'img.product-image',
                'div.product-images img',
                'img[itemprop="image"]'
            ])
            
            desc_tag = soup.find('div', {'class': re.compile('description', re.I)})
            description = desc_tag.get_text(strip=True) if desc_tag else None
            
            breadcrumbs = soup.select('nav.breadcrumb a, ol.breadcrumb a')
            category = ' > '.join([b.get_text(strip=True) for b in breadcrumbs])
            
            return {
                'product_id': product_id,
                'retailer': self.retailer_name,
                'product_url': product_url,
                'title': title,
                'brand': brand,
                'category': category,
                'price_current': self.clean_price(price_text) if price_text else None,
                'currency': 'USD',
                'description': description,
                'image_urls': image_urls,
                'status': 'success' if title else 'partial_data'
            }
            
        except Exception as e:
            print(f"  Error parsing HTML: {e}")
            return None

