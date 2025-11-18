import re
from typing import Set, List
from urllib.parse import urlparse
from ..core.constants import FileExtensions

class URLFilter:
    def __init__(self, config: dict):
        self.config = config
        self.file_extensions = set(ext.value for ext in FileExtensions)
        self.file_extensions.update(config.get('file_extensions_to_avoid', []))
        
    def is_file_url(self, url: str) -> bool:
        """Check if URL points to a file that should be avoided"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Check for file extensions
        if any(path.endswith(ext) for ext in self.file_extensions):
            return True
            
        # Check for common file patterns
        file_patterns = [
            r'.*\.pdf(\?.*)?$',
            r'.*\.docx?(\?.*)?$',
            r'.*\.pptx?(\?.*)?$',
            r'.*\.xlsx?(\?.*)?$',
        ]
        
        return any(re.match(pattern, path) for pattern in file_patterns)
    
    def is_allowed_domain(self, url: str, base_domain: str) -> bool:
        """Check if URL belongs to allowed domains"""
        parsed = urlparse(url)
        url_domain = parsed.netloc
        
        allowed_domains = self.config.get('allowed_domains', [])
        if not allowed_domains:
            return url_domain == base_domain
            
        return any(url_domain == domain or url_domain.endswith(f".{domain}") 
                  for domain in allowed_domains)
    
    def filter_urls(self, urls: Set[str], base_domain: str) -> List[str]:
        """Filter URLs based on configuration"""
        filtered_urls = []
        
        for url in urls:
            if (not self.is_file_url(url) and 
                self.is_allowed_domain(url, base_domain)):
                filtered_urls.append(url)
                
        return filtered_urls