import xml.etree.ElementTree as ET
from typing import List, Set
from urllib.parse import urlparse, urljoin
import requests
from ..core.exceptions import SitemapParseException
from ..utils.logger import setup_logger

class SitemapParser:
    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logger(__name__)
    
    def discover_sitemap(self, base_url: str) -> str:
        """Discover sitemap location for a website"""
        sitemap_locations = [
            urljoin(base_url, 'sitemap.xml'),
            urljoin(base_url, 'sitemap_index.xml'),
            urljoin(base_url, 'sitemap/sitemap.xml'),
        ]
        
        for location in sitemap_locations:
            try:
                response = requests.head(location, timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"Found sitemap at: {location}")
                    return location
            except requests.RequestException:
                continue
        
        raise SitemapParseException(f"No sitemap found for {base_url}")
    
    def parse_sitemap(self, sitemap_url: str) -> Set[str]:
        """Parse sitemap and extract all URLs"""
        try:
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            urls = set()
            
            # Check if it's a sitemap index
            if root.tag.endswith('sitemapindex'):
                for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                    loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None and loc.text:
                        urls.update(self.parse_sitemap(loc.text))
            else:
                # It's a regular sitemap
                for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None and loc.text:
                        urls.add(loc.text)
            
            self.logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            raise SitemapParseException(f"Failed to parse sitemap {sitemap_url}: {e}")
    
    def compare_with_crawled_urls(self, sitemap_urls: Set[str], crawled_urls: Set[str]) -> dict:
        """Compare sitemap URLs with crawled URLs"""
        sitemap_set = set(sitemap_urls)
        crawled_set = set(crawled_urls)
        
        return {
            'sitemap_only': list(sitemap_set - crawled_set),
            'crawled_only': list(crawled_set - sitemap_set),
            'common_urls': list(sitemap_set & crawled_set),
            'sitemap_total': len(sitemap_set),
            'crawled_total': len(crawled_set),
            'coverage_percentage': len(sitemap_set & crawled_set) / len(sitemap_set) * 100 if sitemap_set else 0
        }