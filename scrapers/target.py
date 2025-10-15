"""
Target scraper - GraphQL API interception strategy.
"""

from typing import List, Dict, Optional, Any, AsyncGenerator
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import gzip
from io import BytesIO
import httpx
from .base import BaseScraper


class TargetScraper(BaseScraper):
    """Target.com scraper using GraphQL API and sitemap enumeration."""
    
    def __init__(self, config, database, browser_manager, rate_limiter, proxy_manager):
        super().__init__(config, database, browser_manager, rate_limiter, proxy_manager)
        self.retailer_name = 'target'
        from config import RETAILERS
        self.base_url = RETAILERS['target']['base_url']
        self.sitemap_url = RETAILERS['target']['sitemap_url']
    
    async def enumerate_products(self) -> AsyncGenerator[Dict[str, str], None]:
        """
        Enumerate products using multiple methods (streaming).
        Yields products one-by-one instead of loading all into memory.
        """
        # Method 1: Sitemap enumeration
        print(f"\n[{self.retailer_name}] Method 1: Sitemap enumeration...")
        
        async for product in self._enumerate_sitemap():
            yield product
        
        # Method 2: Category validation (lighter check)
        # This would require exploring Target's category API
        # For now, we'll rely on sitemap as primary source
    
    async def _enumerate_sitemap(self) -> AsyncGenerator[Dict[str, str], None]:
        """Parse Target's sitemap index and extract all product URLs (streaming)."""
        # Fetch main sitemap index (gzipped)
        print(f"  Fetching sitemap from: {self.sitemap_url}")
        html = await self._fetch_gzipped_sitemap(self.sitemap_url)
        if not html:
            print(f"  ✗ Failed to fetch sitemap index")
            return
        
        print(f"  ✓ Fetched sitemap: {len(html)} chars")
        
        soup = BeautifulSoup(html, 'xml')
        
        # Target may have sitemap index with multiple sitemaps
        sitemaps = soup.find_all('loc')
        
        if not sitemaps:
            # Single sitemap, parse directly
            urls = soup.find_all('url')
            for url_tag in urls:
                loc = url_tag.find('loc')
                if loc:
                    url = loc.text.strip()
                    # Extract TCIN from URL
                    tcin = self._extract_tcin_from_url(url)
                    if tcin:
                        yield {
                            'product_id': tcin,
                            'product_url': url,
                            'method': 'sitemap'
                        }
        else:
            # Multiple sitemaps, fetch each one
            print(f"  Found {len(sitemaps)} sitemap files to parse...")
            for idx, sitemap_loc in enumerate(sitemaps):  # Parse ALL sitemaps
                sitemap_url = sitemap_loc.text.strip()
                
                if 'pdp' not in sitemap_url.lower():  # Target uses 'pdp' for product pages
                    continue
                
                # Fetch individual sitemap (also gzipped)
                sitemap_html = await self._fetch_gzipped_sitemap(sitemap_url)
                if sitemap_html:
                    sitemap_soup = BeautifulSoup(sitemap_html, 'xml')
                    urls = sitemap_soup.find_all('url')
                    
                    for url_tag in urls:
                        loc = url_tag.find('loc')
                        if loc:
                            url = loc.text.strip()
                            tcin = self._extract_tcin_from_url(url)
                            if tcin:
                                yield {
                                    'product_id': tcin,
                                    'product_url': url,
                                    'method': 'sitemap'
                                }
                    
                    print(f"    Parsed sitemap {idx+1}/{len(sitemaps)}: {len(urls)} URLs")
    
    async def _fetch_gzipped_sitemap(self, url: str) -> Optional[str]:
        """Fetch and decompress gzipped sitemap."""
        await self.rate_limiter.wait(self.retailer_name)
        
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    return None
                
                # Try to decompress if actually gzipped, otherwise return as-is
                if url.endswith('.gz'):
                    try:
                        decompressed = gzip.decompress(response.content)
                        return decompressed.decode('utf-8')
                    except gzip.BadGzipFile:
                        # Already decompressed by server
                        return response.text
                else:
                    return response.text
        except Exception as e:
            print(f"  Error fetching sitemap {url}: {e}")
            return None
    
    def _extract_tcin_from_url(self, url: str) -> Optional[str]:
        """Extract TCIN (Target product ID) from URL."""
        # URL format: https://www.target.com/p/product-name/-/A-12345678
        match = re.search(r'/A-(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    async def scrape_product(self, product_url: str, product_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Scrape Target product using GraphQL API.
        Target loads product data via API after page load.
        """
        try:
            # Extract TCIN from URL if not provided
            if not product_id:
                import re
                match = re.search(r'/A-(\d+)', product_url)
                if match:
                    product_id = match.group(1)
                else:
                    return None
            
            await self.rate_limiter.wait(self.retailer_name)
            
            # Call Target's internal API
            product_data = await self._fetch_product_api(product_id)
            
            # Check if product needs browser (marketplace seller)
            if product_data and product_data.get('status') == 'needs_browser':
                # Fallback to browser scraping for marketplace products
                context = await self.browser_manager.create_context(self.retailer_name)
                page = await self.browser_manager.new_page(context)
                await page.goto(product_url, wait_until='networkidle', timeout=30000)
                
                # Wait for price element to ensure content is loaded
                try:
                    await page.wait_for_selector('span[data-test="product-price"]', timeout=10000)
                except:
                    pass  # Continue anyway if selector not found
                
                # Scrape from live page before closing
                result = await self._parse_browser_fallback_live(page, product_url, product_id)
                await self.browser_manager.close_context(context)
                return result
            
            # Check if product not found
            if product_data and product_data.get('status') == 'not_found':
                return {'status': 'not_found'}
            
            if not product_data:
                # Try page load as fallback
                context = await self.browser_manager.create_context(self.retailer_name)
                page = await self.browser_manager.new_page(context)
                response = await page.goto(product_url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status == 404:
                    await self.browser_manager.close_context(context)
                    return {'status': 'not_found'}
                
                await self.browser_manager.close_context(context)
                return None
            
            # Parse API response
            product = self._parse_api_response(product_data, product_url, product_id)
            
            # Note: Marketplace products (sold by 3rd parties) don't have prices in API
            # They would need browser scraping, but that's unreliable on Render
            # So we save them with price_current=None for now
            
            if product:
                self.proxy_manager.record_request(success=True, is_block=False)
            
            return product
            
        except Exception as e:
            import traceback
            print(f"  ❌ EXCEPTION scraping {product_url}: {e}")
            traceback.print_exc()
            return None
    
    async def _fetch_product_api(self, tcin: str) -> Optional[Dict]:
        """Fetch product data from Target's internal API."""
        product_url = f'https://www.target.com/p/-/A-{tcin}'
        
        try:
            # Use browser-like headers (captured from real browser)
            api_headers = {
                'accept': 'application/json',
                'referer': product_url,
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Not=A?Brand";v="24", "Chromium";v="140"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
            }
            
            # 1. Get main product data
            # Use channel=WEB for national online pricing (not store-specific)
            pdp_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&channel=WEB&is_bot=false'
            product_data = await self.fetch_json(pdp_api_url, headers=api_headers)
            
            # If API returns no data, product might be marketplace seller - try browser fallback
            if not product_data or not product_data.get('data', {}).get('product'):
                return {'status': 'needs_browser'}  # Signal to use browser scraping
            
            # 2. Get fulfillment data (shipping estimate & cost)
            # Use central US ZIP for consistent nationwide estimates (50000 = Des Moines, IA)
            fulfillment_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/product_fulfillment_and_variation_hierarchy_v1?key=ff457966e64d5e877fdbad070f276d18ecec4a01&tcin={tcin}&zip=50000'
            fulfillment_data = await self.fetch_json(fulfillment_api_url, headers=api_headers)
            
            # Merge fulfillment data into product data
            if fulfillment_data and fulfillment_data.get('data', {}).get('product'):
                product_data['data']['product']['fulfillment_data'] = fulfillment_data['data']['product']
            
            return product_data
        except Exception as e:
            print(f"  API fetch error for {tcin}: {e}")
            return None
    
    def _parse_api_response(self, data: Dict, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse Target API response."""
        try:
            if not data:
                return None
            
            product = data.get('data', {}).get('product', {})
            if not product:
                return None
            
            tcin = product.get('tcin', product_id)
            
            # Extract nested item data
            item = product.get('item', {})
            if not item:
                return None
            
            prod_desc = item.get('product_description', {})
            title = prod_desc.get('title')
            
            # Skip only if title is completely missing
            if not title:
                return {'status': 'not_found'}
            
            # Brand is in primary_brand, not product_brand
            brand = item.get('primary_brand', {}).get('name')
            
            # Price
            price_obj = product.get('price', {})
            price_current = price_obj.get('current_retail')
            price_compare = price_obj.get('reg_retail') or price_obj.get('comparison_price')
            
            # Images
            images = product.get('item', {}).get('enrichment', {}).get('images', {})
            # Handle both dict and string formats for primary_image
            primary_img_data = images.get('primary_image')
            if isinstance(primary_img_data, dict):
                primary_image = primary_img_data.get('url')
            elif isinstance(primary_img_data, str):
                primary_image = primary_img_data
            else:
                primary_image = None
            
            # Handle alternate images
            alt_imgs_data = images.get('alternate_images', [])
            alternate_images = []
            for img in alt_imgs_data:
                if isinstance(img, dict):
                    url = img.get('url')
                    if url:
                        alternate_images.append(url)
                elif isinstance(img, str):
                    alternate_images.append(img)
            
            all_images = [primary_image] + alternate_images if primary_image else alternate_images
            
            # Description
            desc_obj = product.get('item', {}).get('product_description', {})
            description = desc_obj.get('downstream_description') or desc_obj.get('soft_bullets', {}).get('bullets', [])
            if isinstance(description, list):
                description = ' | '.join(description)
            
            # Category - use category.name directly
            category_obj = product.get('category', {})
            category = category_obj.get('name', '')
            
            # Ratings
            ratings = product.get('ratings_and_reviews', {}).get('statistics', {})
            ratings_avg = ratings.get('rating', {}).get('average')
            ratings_count = ratings.get('rating', {}).get('count')
            
            # Availability
            fulfillment = product.get('fulfillment_fiats', {})
            is_available = fulfillment.get('is_out_of_stock_in_all_store_locations') == False
            availability = 'in_stock' if is_available else 'out_of_stock'
            
            # Specifications
            specs_list = product.get('item', {}).get('product_description', {}).get('soft_bullets', {}).get('bullets', [])
            specifications = ' | '.join(specs_list) if specs_list else None
            
            # Shipping from fulfillment API
            fulfillment_data = product.get('fulfillment_data', {})
            shipping_options = fulfillment_data.get('fulfillment', {}).get('shipping_options', {})
            
            # Extract shipping cost (standard shipping)
            pay_charges = fulfillment_data.get('pay_per_order_charges', {})
            shipping_cost = pay_charges.get('one_day') or pay_charges.get('scheduled_delivery')
            
            # Extract delivery estimate
            services = shipping_options.get('services', [])
            shipping_estimate = None
            if services:
                standard_service = services[0]  # Get first/standard shipping
                min_date = standard_service.get('min_delivery_date')
                max_date = standard_service.get('max_delivery_date')
                if min_date:
                    # Convert "2025-10-18" to "Sat, Oct 18"
                    date_obj = datetime.strptime(min_date, '%Y-%m-%d')
                    shipping_estimate = f"{date_obj.strftime('%a, %b %d')}"
            
            return {
                'product_id': tcin,
                'retailer': 'target',
                'product_url': product_url,
                'title': title,
                'brand': brand,
                'category': category,
                'price_current': price_current,
                'price_compare_at': price_compare,
                'currency': 'USD',
                'availability': availability,
                'description': description,
                'specifications': specifications,
                'image_urls': all_images[:10] if all_images else None,
                'ratings_average': ratings_avg,
                'ratings_count': ratings_count,
                'shipping_cost': shipping_cost,
                'shipping_estimate': shipping_estimate,
                'variants': None,  # Complex, can add if needed
                'seller': 'Target',
                'scraped_at': datetime.now().isoformat(),
                'status': 'success'
            }
        except Exception as e:
            print(f"  ❌ PARSE EXCEPTION for {product_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract __NEXT_DATA__ JSON from page."""
        script = soup.find('script', id='__NEXT_DATA__')
        if script and script.string:
            try:
                return json.loads(script.string)
            except:
                pass
        return None
    
    async def _parse_browser_fallback_live(self, page, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse marketplace/third-party seller products from live page."""
        try:
            # Scrape price from live DOM (loaded dynamically)
            price_current = None
            try:
                price_elem = await page.query_selector('span[data-test="product-price"]')
                if price_elem:
                    price_text = await price_elem.inner_text()
                    price_text = price_text.strip().replace('$', '').replace(',', '')
                    try:
                        price_current = float(price_text)
                    except:
                        pass
            except:
                pass
            
            # Scrape shipping estimate
            shipping_estimate = None
            try:
                # Look for "Arrives by" text
                shipping_elem = await page.query_selector('text=/Arrives by/')
                if shipping_elem:
                    shipping_text = await shipping_elem.inner_text()
                    shipping_estimate = shipping_text.strip()
            except:
                pass
            
            # Now get full HTML for remaining data
            html = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract __NEXT_DATA__ for full details
            script = soup.find('script', id='__NEXT_DATA__')
            if script and script.string:
                data = json.loads(script.string)
                props = data.get('props', {}).get('pageProps', {}).get('initialData', {}).get('data', {}).get('product', {})
                
                if props:
                    # Extract from __NEXT_DATA__ structure
                    item = props.get('item', {})
                    title = item.get('product_description', {}).get('title', 'Unknown')
                    brand = item.get('primary_brand', {}).get('name')
                    category = props.get('category', {}).get('name')
                    
                    # Description
                    description = item.get('product_description', {}).get('downstream_description')
                    if description:
                        from bs4 import BeautifulSoup as BS
                        description = BS(description, 'html.parser').get_text(strip=True, separator=' ')
                    
                    # Images
                    images = item.get('enrichment', {}).get('images', {})
                    image_urls = [images.get('primary_image', '')] if images.get('primary_image') else []
                    image_urls.extend(images.get('alternate_images', []))
                    
                    # Ratings
                    ratings = props.get('ratings_and_reviews', {}).get('statistics', {}).get('rating', {})
                    ratings_avg = ratings.get('average')
                    ratings_count = ratings.get('count')
                    
                    # Seller
                    seller = 'Marketplace'
                    
                    return {
                        'product_id': product_id,
                        'retailer': 'target',
                        'product_url': product_url,
                        'title': title,
                        'brand': brand,
                        'category': category,
                        'price_current': price_current,  # From live DOM
                        'price_compare_at': None,
                        'currency': 'USD',
                        'availability': 'in_stock',
                        'description': description,
                        'specifications': None,
                        'image_urls': image_urls,
                        'ratings_average': ratings_avg,
                        'ratings_count': ratings_count,
                        'shipping_cost': None,
                        'shipping_estimate': shipping_estimate,  # From live DOM
                        'variants': None,
                        'seller': seller,
                        'scraped_at': datetime.now().isoformat(),
                        'status': 'success'
                    }
            
            # Fallback to simple DOM scraping if __NEXT_DATA__ not available
            title = None
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)
            
            return {
                'product_id': product_id,
                'retailer': 'target',
                'product_url': product_url,
                'title': title or 'Unknown',
                'brand': None,
                'category': None,
                'price_current': price_current,
                'price_compare_at': None,
                'currency': 'USD',
                'availability': 'in_stock',
                'description': None,
                'specifications': None,
                'image_urls': None,
                'ratings_average': None,
                'ratings_count': None,
                'shipping_cost': None,
                'shipping_estimate': shipping_estimate,
                'variants': None,
                'seller': 'Marketplace',
                'scraped_at': datetime.now().isoformat(),
                'status': 'success'
            }
        except Exception as e:
            print(f"  Browser fallback failed for {product_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_next_data(self, data: Dict, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Parse product data from __NEXT_DATA__ JSON."""
        try:
            # Navigate through the nested structure
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            product_data = page_props.get('product', {}) or page_props.get('initialData', {}).get('product', {})
            
            if not product_data:
                return None
            
            # Extract fields
            tcin = product_data.get('tcin') or product_id
            title = product_data.get('title') or product_data.get('item', {}).get('product_description', {}).get('title')
            brand = product_data.get('brand') or product_data.get('item', {}).get('product_brand', {}).get('brand')
            
            # Price
            price_data = product_data.get('price', {})
            price_current = price_data.get('current_retail') or price_data.get('current_price')
            price_compare = price_data.get('reg_retail') or price_data.get('regular_price')
            
            # Images
            images_data = product_data.get('images', []) or product_data.get('item', {}).get('enrichment', {}).get('images', [])
            image_urls = [img.get('base_url') or img.get('url') for img in images_data if img.get('base_url') or img.get('url')]
            
            # Description
            description = product_data.get('description') or product_data.get('item', {}).get('product_description', {}).get('downstream_description')
            
            # Category/breadcrumbs
            breadcrumbs = product_data.get('breadcrumbs', [])
            category = ' > '.join([b.get('name', '') for b in breadcrumbs if b.get('name')])
            
            # Ratings
            ratings = product_data.get('ratings_and_reviews', {}) or product_data.get('ratings', {})
            ratings_avg = ratings.get('average_rating') or ratings.get('average')
            ratings_count = ratings.get('count') or ratings.get('total_reviews')
            
            # Availability
            availability = 'in_stock' if product_data.get('available', False) else 'out_of_stock'
            
            return {
                'product_id': tcin,
                'retailer': self.retailer_name,
                'product_url': product_url,
                'title': title,
                'brand': brand,
                'category': category,
                'price_current': self.clean_price(str(price_current)) if price_current else None,
                'price_compare_at': self.clean_price(str(price_compare)) if price_compare else None,
                'currency': 'USD',
                'availability': availability,
                'description': description,
                'image_urls': image_urls,
                'ratings_average': ratings_avg,
                'ratings_count': ratings_count,
                'specifications': {},
                'status': 'success'
            }
            
        except Exception as e:
            print(f"  Error parsing __NEXT_DATA__: {e}")
            return None
    
    def _parse_html(self, soup: BeautifulSoup, product_url: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Fallback HTML parsing for Target."""
        try:
            # Try JSON-LD
            json_ld = self.parse_json_ld(soup)
            if json_ld and json_ld.get('@type') == 'Product':
                return {
                    'product_id': product_id or json_ld.get('sku'),
                    'retailer': self.retailer_name,
                    'product_url': product_url,
                    'title': json_ld.get('name'),
                    'brand': json_ld.get('brand', {}).get('name') if isinstance(json_ld.get('brand'), dict) else json_ld.get('brand'),
                    'price_current': self.clean_price(str(json_ld.get('offers', {}).get('price'))),
                    'image_urls': [json_ld.get('image')] if json_ld.get('image') else [],
                    'description': json_ld.get('description'),
                    'ratings_average': json_ld.get('aggregateRating', {}).get('ratingValue'),
                    'ratings_count': json_ld.get('aggregateRating', {}).get('reviewCount'),
                    'availability': 'in_stock' if 'InStock' in json_ld.get('offers', {}).get('availability', '') else 'out_of_stock',
                    'currency': 'USD',
                    'status': 'success'
                }
            
            # Basic HTML extraction
            title = soup.find('h1')
            return {
                'product_id': product_id,
                'retailer': self.retailer_name,
                'product_url': product_url,
                'title': title.get_text(strip=True) if title else None,
                'status': 'partial_data'
            }
            
        except Exception as e:
            print(f"  Error parsing HTML: {e}")
            return None

