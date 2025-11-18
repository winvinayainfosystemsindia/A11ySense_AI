import random
from playwright.async_api import Page
from ...utils.logger import setup_logger

class StealthHandler:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def apply_stealth_mode(self, page: Page):
        """Apply stealth techniques to avoid detection"""
        
        # Set random viewport
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
        ]
        viewport = random.choice(viewports)
        await page.set_viewport_size(viewport)
        
        # Set user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]
        user_agent = self.config.get('user_agent') or random.choice(user_agents)
        await page.set_extra_http_headers({'User-Agent': user_agent})
        
        # Block unnecessary resources
        await page.route("**/*", self._route_handler)
        
        # Remove webdriver property
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
    
    async def _route_handler(self, route, request):
        """Route handler to block unnecessary resources"""
        resource_type = request.resource_type
        if resource_type in ["image", "media", "font"]:
            await route.abort()
        else:
            await route.continue_()