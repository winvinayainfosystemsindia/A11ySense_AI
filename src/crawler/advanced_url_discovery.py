import re
import asyncio
from typing import Set, List
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page
from ..utils.logger import setup_logger

class AdvancedURLDiscovery:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    async def discover_urls_from_multiple_sources(self, page: Page, base_url: str) -> Set[str]:
        """Discover URLs from multiple sources on the page"""
        urls = set()
        
        # Discover from different sources concurrently
        tasks = [
            self._discover_from_links(page, base_url),
            self._discover_from_sitemap_links(page, base_url),
            self._discover_from_xml_sitemap(page, base_url),
            self._discover_from_scripts(page, base_url),
            self._discover_from_meta_tags(page, base_url),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, set):
                urls.update(result)
        
        return urls
    
    async def _discover_from_links(self, page: Page, base_url: str) -> Set[str]:
        """Discover URLs from all anchor tags"""
        return await page.eval_on_selector_all('a[href]', '''elements => {
            return elements.map(el => {
                try {
                    return new URL(el.href, window.location.origin).href;
                } catch {
                    return null;
                }
            }).filter(url => url !== null);
        }''')
    
    async def _discover_from_sitemap_links(self, page: Page, base_url: str) -> Set[str]:
        """Discover sitemap links from robots.txt and common locations"""
        sitemap_urls = set()
        
        # Check robots.txt
        robots_url = urljoin(base_url, '/robots.txt')
        try:
            await page.goto(robots_url, wait_until='domcontentloaded', timeout=10000)
            content = await page.content()
            
            # Extract sitemap URLs from robots.txt
            sitemap_pattern = r'Sitemap:\s*(https?://[^\s]+)'
            sitemap_urls.update(re.findall(sitemap_pattern, content, re.IGNORECASE))
        except:
            pass
        
        # Check common sitemap locations
        common_locations = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap/sitemap.xml',
            '/sitemap1.xml',
            '/post-sitemap.xml',
            '/page-sitemap.xml',
        ]
        
        for location in common_locations:
            sitemap_urls.add(urljoin(base_url, location))
        
        return sitemap_urls
    
    async def _discover_from_xml_sitemap(self, page: Page, base_url: str) -> Set[str]:
        """Parse XML sitemap if available"""
        # This would be implemented to parse actual sitemap content
        return set()
    
    async def _discover_from_scripts(self, page: Page, base_url: str) -> Set[str]:
        """Discover URLs from JavaScript and JSON-LD"""
        urls = set()
        
        # Extract from JSON-LD structured data
        json_ld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for script in json_ld_scripts:
            try:
                content = await script.text_content()
                # Simple URL extraction from JSON (basic implementation)
                url_pattern = r'"url"\s*:\s*"([^"]+)"'
                urls.update(re.findall(url_pattern, content))
            except:
                pass
        
        return urls
    
    async def _discover_from_meta_tags(self, page: Page, base_url: str) -> Set[str]:
        """Discover URLs from meta tags"""
        urls = set()
        
        # Check canonical links
        canonical = await page.query_selector('link[rel="canonical"]')
        if canonical:
            href = await canonical.get_attribute('href')
            if href:
                urls.add(urljoin(base_url, href))
        
        return urls