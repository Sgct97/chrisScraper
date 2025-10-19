"""
Configuration settings for the retail scraper.
Optimized for 32GB RAM machine running on home network first.
"""

import os

CONFIG = {
    # Location settings for price/availability
    'zip_code': '90210',  # Default ZIP code - user should update this
    
    # Concurrency optimized for 64GB RAM (AWS Spot r6i.4xlarge: 128GB, 16 vCPU)
    # Target uses lightweight API calls (~5MB RAM each) = can handle 100-150 concurrent
    # Others use browser automation (~150-200MB each) = 4-8 concurrent safe
    'concurrency': {
        'target': int(os.getenv('TARGET_CONCURRENCY', '100')),  # High concurrency for API-based scraping
        'costco': int(os.getenv('COSTCO_CONCURRENCY', '6')),    # Browser-heavy, Cloudflare protection
        'homegoods': int(os.getenv('HOMEGOODS_CONCURRENCY', '6')),  # Browser-heavy
        'tjmaxx': int(os.getenv('TJMAXX_CONCURRENCY', '6'))     # Browser-heavy, residential proxy needed
    },
    
    # Rate limiting - conservative for home IP
    'delays_ms': {
        'min': 150,
        'max': 500
    },
    
    # Proxy settings - Support multiple providers
    'proxy': {
        'enabled': os.getenv('USE_PROXIES', 'false').lower() == 'true',  # Set USE_PROXIES=true to enable
        'auto_enable_on_blocks': True,  # Auto-switch when threshold hit
        'provider': os.getenv('PROXY_PROVIDER', 'smartproxy'),  # 'smartproxy' or 'oxylabs'
        
        # Smartproxy (Decodo) - UK-based, KYC required
        'smartproxy': {
            'url': f"http://{os.getenv('PROXY_USER', '')}:{os.getenv('PROXY_PASS', '')}@us.decodo.com:10000" if os.getenv('PROXY_USER') and os.getenv('PROXY_PASS') else None,
        },
        
        # Oxylabs - US-based alternative
        'oxylabs': {
            'url': f"http://{os.getenv('OXYLABS_USER', '')}:{os.getenv('OXYLABS_PASS', '')}@pr.oxylabs.io:7777" if os.getenv('OXYLABS_USER') and os.getenv('OXYLABS_PASS') else None,
        },
        
        'switch_threshold_percent': 2.0,  # Switch if >2% blocks in 5min
        'switch_threshold_count': 10  # Or 10+ consecutive failures
    },
    
    # Retry and timeout settings
    'retries': 3,
    'timeout_seconds': 30,
    
    # Memory management for 32GB machine
    'max_memory_percent': 75,  # Use max 75% of RAM (~24GB)
    'browser_pool_size': 80,   # Max concurrent browser instances
    'cleanup_interval_minutes': 15,  # Restart contexts to prevent memory leaks
    
    # Database settings (use env var for Render, local path otherwise)
    'database_path': os.getenv('DATABASE_PATH', 'scraper_data.db'),
    
    # Export settings (use env vars for Render, local paths otherwise)
    'export_dir': os.getenv('EXPORT_DIR', 'exports'),
    'manifests_dir': os.getenv('MANIFEST_DIR', 'manifests'),
    
    # User agents for requests (rotated)
    'user_agents': [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    ]
}

# Retailer-specific settings
RETAILERS = {
    'target': {
        'name': 'Target',
        'base_url': 'https://www.target.com',
        'sitemap_url': 'https://www.target.com/sitemap_pdp-index.xml.gz',
        'graphql_endpoint': 'https://api.target.com/products/graphql/pdp_client_v1',
        'requires_proxy': False,
    },
    'costco': {
        'name': 'Costco',
        'base_url': 'https://www.costco.com',
        'sitemap_url': 'https://www.costco.com/sitemap_lw_index.xml',
        'requires_proxy': False,
    },
    'homegoods': {
        'name': 'HomeGoods',
        'base_url': 'https://www.homegoods.com',
        'online_shopping': False,  # In-store only
    },
    'tjmaxx': {
        'name': 'TJ Maxx',
        'base_url': 'https://www.tjmaxx.com',
        'requires_proxy': True,  # Requires residential proxies
        'proxy_type': 'residential',
    }
}

