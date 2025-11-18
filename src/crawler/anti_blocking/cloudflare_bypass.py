import asyncio
import time
from typing import Optional
from playwright.async_api import Page, Response
from ...core.exceptions import CloudFlareBlockedException
from ...utils.logger import setup_logger

class CloudFlareBypass:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def wait_for_cloudflare(self, page: Page, timeout: int = 60) -> bool:
        """Wait for CloudFlare challenge to be resolved"""
        self.logger.info("Checking for CloudFlare protection...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for CloudFlare challenge elements
            cloudflare_selectors = [
                '#cf-content',
                '.cf-browser-verification',
                '#challenge-form',
                '#trk_jschal_js'
            ]
            
            for selector in cloudflare_selectors:
                if await page.query_selector(selector):
                    self.logger.info("CloudFlare challenge detected, waiting...")
                    await asyncio.sleep(5)
                    break
            else:
                # No CloudFlare challenge found
                if await self._is_page_loaded(page):
                    self.logger.info("CloudFlare challenge resolved")
                    return True
            
            await asyncio.sleep(2)
        
        raise CloudFlareBlockedException("CloudFlare challenge not resolved within timeout")
    
    async def _is_page_loaded(self, page: Page) -> bool:
        """Check if page is loaded and not blocked"""
        try:
            # Check if we're still on a challenge page
            title = await page.title()
            if any(term in title.lower() for term in ['checking', 'verifying', 'challenge']):
                return False
            
            # Check page content
            content = await page.content()
            if any(term in content.lower() for term in ['ddos protection', 'please wait', 'checking your browser']):
                return False
            
            return True
        except:
            return False
    
    async def handle_cloudflare(self, page: Page, response: Optional[Response] = None):
        """Handle CloudFlare protection"""
        if response and response.status in [403, 503]:
            self.logger.warning(f"Received {response.status}, possible CloudFlare block")
            await self.wait_for_cloudflare(page)