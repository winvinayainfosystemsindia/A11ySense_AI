from abc import ABC, abstractmethod
from typing import Set, List, Dict, Any
from urllib.parse import urljoin, urlparse
import logging
from ..core.exceptions import CrawlerException
from ..utils.logger import setup_logger

class BaseCrawler(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        
    @abstractmethod
    async def crawl(self, start_url: str) -> List[str]:
        """Crawl website starting from given URL"""
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up resources"""
        pass
    
    def should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled based on configuration"""
        try:
            parsed_url = urlparse(url)
            
            # Check file extensions to avoid
            if any(parsed_url.path.lower().endswith(ext) 
                   for ext in self.config['crawler']['file_extensions_to_avoid']):
                return False
            
            # Check if already visited
            if url in self.visited_urls:
                return False
            
            # Check domain restrictions
            allowed_domains = self.config['crawler']['allowed_domains']
            if allowed_domains and parsed_url.netloc not in allowed_domains:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error checking URL {url}: {e}")
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')