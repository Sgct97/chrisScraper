"""
Rate limiter with jitter for polite scraping.
"""

import asyncio
import random
from typing import Dict
from datetime import datetime


class RateLimiter:
    def __init__(self, config: Dict):
        self.config = config
        self.delays = config['delays_ms']
        self.min_delay = self.delays['min'] / 1000  # Convert to seconds
        self.max_delay = self.delays['max'] / 1000
        
        # Per-domain tracking
        self.last_request_time = {}
    
    async def wait(self, domain: str = 'default'):
        """Wait with random jitter before next request."""
        # Calculate random delay with jitter
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # Ensure minimum time between requests for this domain
        if domain in self.last_request_time:
            elapsed = datetime.now().timestamp() - self.last_request_time[domain]
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        else:
            await asyncio.sleep(delay)
        
        # Update last request time
        self.last_request_time[domain] = datetime.now().timestamp()
    
    def get_delay_range(self) -> tuple:
        """Get current delay range in ms."""
        return (self.delays['min'], self.delays['max'])

