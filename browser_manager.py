"""
Browser manager with Playwright and stealth patches.
"""

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict
import random
from config import CONFIG


class BrowserManager:
    def __init__(self, proxy_manager=None):
        self.proxy_manager = proxy_manager
        self.playwright = None
        self.browser = None
        self.contexts = []
        self.user_agents = CONFIG['user_agents']
        
    async def initialize(self):
        """Initialize Playwright and browser."""
        self.playwright = await async_playwright().start()
        
        # Launch browser with appropriate settings
        launch_options = {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        }
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        print("✓ Browser initialized")
    
    async def create_context(self, retailer: str = None) -> BrowserContext:
        """Create a new browser context with stealth settings."""
        if not self.browser:
            await self.initialize()
        
        # Get random user agent
        user_agent = random.choice(self.user_agents)
        
        context_options = {
            'user_agent': user_agent,
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'en-US',
            'timezone_id': 'America/Los_Angeles',
            'permissions': ['geolocation'],
            'geolocation': {'latitude': 34.0522, 'longitude': -118.2437},  # LA coordinates
            'ignore_https_errors': True,
        }
        
        # Add proxy if enabled
        if self.proxy_manager and self.proxy_manager.is_enabled():
            proxy_dict = self.proxy_manager.get_proxy_dict()
            if proxy_dict:
                context_options['proxy'] = proxy_dict
        
        context = await self.browser.new_context(**context_options)
        
        # Apply stealth patches to bypass detection
        await self._apply_stealth_patches(context)
        
        self.contexts.append(context)
        return context
    
    async def _apply_stealth_patches(self, context: BrowserContext):
        """Apply stealth JavaScript patches to context."""
        # Add init script to mask automation
        await context.add_init_script("""
            // Overwrite the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Overwrite the navigator.plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Overwrite the navigator.languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Pass the chrome test
            window.chrome = {
                runtime: {},
            };
            
            // Pass the permissions test
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    async def new_page(self, context: BrowserContext) -> Page:
        """Create a new page in the given context."""
        page = await context.new_page()
        
        # Set additional page properties
        await page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return page
    
    async def close_context(self, context: BrowserContext):
        """Close a browser context."""
        try:
            await context.close()
            if context in self.contexts:
                self.contexts.remove(context)
        except Exception as e:
            print(f"Error closing context: {e}")
    
    async def cleanup(self):
        """Close all contexts and browser."""
        for context in self.contexts:
            try:
                await context.close()
            except:
                pass
        
        if self.browser:
            await self.browser.close()
        
        if self.playwright:
            await self.playwright.stop()
        
        print("✓ Browser cleanup complete")

