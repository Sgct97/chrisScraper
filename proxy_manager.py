"""
Proxy management with automatic escalation and health checks.
"""

import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
import random


class ProxyManager:
    def __init__(self, config: Dict):
        self.config = config
        self.proxy_config = config['proxy']
        self.enabled = self.proxy_config['enabled']
        
        # Get proxy URL based on provider
        self.provider = self.proxy_config.get('provider', 'smartproxy')
        if self.provider in self.proxy_config:
            self.datacenter_pool = self.proxy_config[self.provider].get('url')
        else:
            self.datacenter_pool = None
        
        self.isp_pool = []  # Not using ISP pool rotation with Oxylabs/Smartproxy (they rotate internally)
        self.current_proxy_index = 0
        
        # Tracking for auto-escalation
        self.request_count = 0
        self.block_count = 0
        self.consecutive_failures = 0
        self.last_reset_time = datetime.now()
        self.window_duration = timedelta(minutes=5)
        
        # Log proxy configuration
        if self.datacenter_pool:
            print(f"✓ Proxy provider: {self.provider.upper()}")
            print(f"  Proxy mode: {'ENABLED' if self.enabled else 'STANDBY (will auto-enable if blocked)'}")
        
    def is_enabled(self) -> bool:
        """Check if proxy is currently enabled."""
        return self.enabled
    
    def get_proxy_url(self) -> Optional[str]:
        """Get proxy URL if enabled (rotates through ISP pool)."""
        if not self.enabled:
            return None
        
        # Prefer ISP pool over single datacenter proxy
        if self.isp_pool:
            proxy = self.isp_pool[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.isp_pool)
            return proxy
        elif self.datacenter_pool:
            return self.datacenter_pool
        
        return None
    
    def get_proxy_dict(self) -> Optional[Dict[str, str]]:
        """Get proxy dictionary for httpx/playwright."""
        proxy_url = self.get_proxy_url()
        if proxy_url:
            return {'server': proxy_url}
        return None
    
    def record_request(self, success: bool, is_block: bool = False):
        """Record a request outcome for auto-escalation tracking."""
        # Reset window if 5 minutes passed
        if datetime.now() - self.last_reset_time > self.window_duration:
            self.request_count = 0
            self.block_count = 0
            self.last_reset_time = datetime.now()
        
        self.request_count += 1
        
        if is_block:
            self.block_count += 1
            self.consecutive_failures += 1
        else:
            if success:
                self.consecutive_failures = 0
    
    def should_enable_proxy(self) -> bool:
        """Check if we should auto-enable proxies based on block rate."""
        if not self.proxy_config['auto_enable_on_blocks']:
            return False
        
        if self.enabled:
            return False  # Already enabled
        
        if not self.datacenter_pool and not self.isp_pool:
            return False  # No proxy configured
        
        # Check threshold conditions
        threshold_percent = self.proxy_config['switch_threshold_percent']
        threshold_count = self.proxy_config['switch_threshold_count']
        
        # Calculate block rate
        if self.request_count >= 50:  # Need at least 50 requests for meaningful stats
            block_rate = (self.block_count / self.request_count) * 100
            if block_rate >= threshold_percent:
                return True
        
        # Check consecutive failures
        if self.consecutive_failures >= threshold_count:
            return True
        
        return False
    
    def enable_proxy(self, reason: str = "Manual"):
        """Enable proxy mode."""
        self.enabled = True
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*80}")
        print(f"⚠️  PROXY ESCALATION: {reason} at {timestamp}")
        print(f"{'='*80}\n")
    
    def disable_proxy(self):
        """Disable proxy mode (return to home network)."""
        self.enabled = False
        print(f"\n✓ Returning to home network mode\n")
    
    def get_stats(self) -> Dict:
        """Get current proxy stats."""
        block_rate = (self.block_count / self.request_count * 100) if self.request_count > 0 else 0
        return {
            'enabled': self.enabled,
            'request_count': self.request_count,
            'block_count': self.block_count,
            'block_rate_percent': round(block_rate, 2),
            'consecutive_failures': self.consecutive_failures,
            'window_start': self.last_reset_time.strftime("%H:%M:%S")
        }
    
    async def test_proxy_health(self) -> bool:
        """Test if proxy is working with sample requests."""
        if not self.datacenter_pool:
            print("⚠️  No proxy configured, cannot test")
            return False
        
        print("Testing proxy connectivity...")
        test_urls = [
            'https://httpbin.org/ip',
            'https://www.google.com',
            'https://www.target.com',
        ]
        
        successes = 0
        async with httpx.AsyncClient(proxy=self.datacenter_pool, timeout=10) as client:
            for url in test_urls:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        successes += 1
                except Exception as e:
                    print(f"  ✗ Failed to reach {url}: {e}")
        
        success_rate = successes / len(test_urls)
        if success_rate >= 0.6:
            print(f"✓ Proxy health check passed ({successes}/{len(test_urls)} successful)")
            return True
        else:
            print(f"✗ Proxy health check failed ({successes}/{len(test_urls)} successful)")
            return False

