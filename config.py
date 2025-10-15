"""
Configuration settings for the retail scraper.
Optimized for 32GB RAM machine running on home network first.
"""

import os

CONFIG = {
    # Location settings for price/availability
    'zip_code': '90210',  # Default ZIP code - user should update this
    
    # Concurrency optimized for 2GB RAM on Render (each Playwright instance ~150-200MB)
    # 4 concurrent browsers × 150MB = 600MB, leaves 1.4GB for Python + safety margin
    'concurrency': {
        'target': 4,       # API calls + occasional browser for marketplace products
        'costco': 4,       # Cloudflare + anti-bot
        'homegoods': 4,    # Lighter protection
        'tjmaxx': 4        # Lighter protection
    },
    
    # Rate limiting - conservative for home IP
    'delays_ms': {
        'min': 150,
        'max': 500
    },
    
    # Proxy settings - DISABLED by default, only enable when blocked
    'proxy': {
        'enabled': False,  # Start on HOME NETWORK
        'auto_enable_on_blocks': True,  # Auto-switch when threshold hit
        'datacenter_pool': None,  # Set "http://user:pass@proxy:port" if you have credentials
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

