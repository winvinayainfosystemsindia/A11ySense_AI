import asyncio
from typing import List, Set, Dict, Any
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Page, Response
from .base_crawler import BaseCrawler
from .url_filter import URLFilter
from .sitemap_parser import SitemapParser
from .anti_blocking.cloudflare_bypass import CloudFlareBypass
from .anti_blocking.stealth_handler import StealthHandler
from .error_handler import retry_on_failure, ErrorHandler
from ..core.exceptions import CrawlerException, CloudFlareBlockedException
from ..utils.logger import setup_logger

class PlaywrightCrawler(BaseCrawler):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url_filter = URLFilter(config['crawler'])
        self.sitemap_parser = SitemapParser(config['crawler'])
        self.cloudflare_bypass = CloudFlareBypass(config['anti_blocking'])
        self.stealth_handler = StealthHandler(config['crawler'])
        self.error_handler = ErrorHandler(config)
        self.playwright = None
        self.browser = None
        self.context = None
        
    async def crawl(self, start_url: str) -> List[str]:
        """Crawl website using Playwright"""
        try:
            self.logger.info(f"Starting crawl from: {start_url}")
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser with stealth options
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.config['crawler']['user_agent']
            )
            
            # Apply stealth mode if enabled
            if self.config['anti_blocking']['enable_stealth_mode']:
                page = await self.context.new_page()
                await self.stealth_handler.apply_stealth_mode(page)
                await page.close()
            
            # Get sitemap URLs for comparison
            sitemap_urls = await self._get_sitemap_urls(start_url)
            
            # Start crawling
            crawled_urls = await self._crawl_urls(start_url)
            
            # Compare with sitemap
            comparison = self.sitemap_parser.compare_with_crawled_urls(
                sitemap_urls, set(crawled_urls)
            )
            
            self.logger.info(f"Crawling completed. Found {len(crawled_urls)} URLs")
            self.logger.info(f"Coverage: {comparison['coverage_percentage']:.2f}%")
            
            if comparison['sitemap_only']:
                self.logger.warning(f"Missed {len(comparison['sitemap_only'])} URLs from sitemap")
            
            return crawled_urls
            
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            raise CrawlerException(f"Crawling failed: {e}")
    
    async def _get_sitemap_urls(self, start_url: str) -> Set[str]:
        """Get URLs from sitemap"""
        try:
            sitemap_location = self.sitemap_parser.discover_sitemap(start_url)
            return self.sitemap_parser.parse_sitemap(sitemap_location)
        except Exception as e:
            self.logger.warning(f"Could not get sitemap URLs: {e}")
            return set()
    
    async def _crawl_urls(self, start_url: str) -> List[str]:
        """Crawl URLs starting from base URL"""
        base_domain = urlparse(start_url).netloc
        queue = [start_url]
        crawled_urls = []
        
        max_pages = self.config['website']['max_pages']
        max_depth = self.config['crawler']['max_depth']
        
        current_depth = 0
        pages_crawled = 0
        
        self.logger.info(f"Crawling limits - Max pages: {max_pages}, Max depth: {max_depth}")
        
        while queue and pages_crawled < max_pages and current_depth < max_depth:
            current_batch = queue[:]
            queue = []
            
            for url in current_batch:
                if pages_crawled >= max_pages:
                    break
                    
                if not self.should_crawl_url(url):
                    continue
                
                try:
                    page_urls = await self._crawl_single_page(url, base_domain)
                    new_urls = [u for u in page_urls if self.should_crawl_url(u)]
                    queue.extend(new_urls)
                    
                    crawled_urls.append(url)
                    self.visited_urls.add(url)
                    pages_crawled += 1
                    
                    self.logger.info(f"Crawled {url} (Depth: {current_depth}, Total: {pages_crawled})")
                    
                    # Respect delay between requests
                    delay = self.config['crawler']['delay_between_requests']
                    if delay > 0:
                        await asyncio.sleep(delay)
                        
                except CloudFlareBlockedException as e:
                    self.logger.error(f"CloudFlare blocked crawling: {e}")
                    raise
                except Exception as e:
                    self.logger.warning(f"Failed to crawl {url}: {e}")
                    continue
            
            current_depth += 1
            self.logger.info(f"Completed depth {current_depth}. Found {len(queue)} new URLs for next depth")
        
        return crawled_urls
    
    @retry_on_failure(max_retries=3, delay=1.0)
    async def _crawl_single_page(self, url: str, base_domain: str) -> List[str]:
        """Crawl a single page and extract URLs"""
        page = await self.context.new_page()
        
        try:
            # Set up event handlers for CloudFlare
            page.on('response', lambda response: asyncio.create_task(
                self.cloudflare_bypass.handle_cloudflare(page, response)
            ))
            
            # Navigate to page with error handling
            response = await self.error_handler.handle_navigation_errors(page, url)
            
            if not response:
                raise CrawlerException(f"No response from {url}")
            
            # Wait for CloudFlare if needed
            if self.config['anti_blocking']['enable_stealth_mode']:
                await self.cloudflare_bypass.wait_for_cloudflare(page)
            
            # Extract all links from the page
            links = await page.eval_on_selector_all('a[href]', '''elements => {
                return elements.map(el => el.href);
            }''')
            
            # Filter and normalize links
            filtered_links = []
            for link in links:
                if link:
                    full_url = urljoin(url, link)
                    normalized_url = self.normalize_url(full_url)
                    if self.url_filter.is_allowed_domain(normalized_url, base_domain):
                        filtered_links.append(normalized_url)
            
            return list(set(filtered_links))
            
        finally:
            await page.close()
    
    async def close(self):
        """Clean up resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()