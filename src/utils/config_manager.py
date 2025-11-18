import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigManager:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Load environment variables
        load_dotenv()
        
        # Replace environment variable placeholders
        config = self._replace_env_variables(config)
        
        # Validate required settings
        self._validate_config(config)
        
        return config
    
    def _replace_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Replace environment variable placeholders in config"""
        def replace_recursive(obj):
            if isinstance(obj, dict):
                return {k: replace_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_recursive(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                return os.getenv(env_var, f"MISSING_{env_var}")
            return obj
        
        return replace_recursive(config)
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration parameters"""
        # Validate website URL
        website_url = config.get('website', {}).get('url', '')
        if not website_url or website_url == "https://example.com":
            raise ValueError("Please update 'website.url' in config.yaml with your target website")
        
        if not website_url.startswith(('http://', 'https://')):
            raise ValueError("Website URL must start with http:// or https://")
        
        # Validate max pages
        max_pages = config.get('website', {}).get('max_pages', 1000)
        if not isinstance(max_pages, int) or max_pages <= 0:
            raise ValueError("website.max_pages must be a positive integer")
    
    def get_website_url(self) -> str:
        """Get target website URL"""
        return self.config['website']['url']
    
    def get_website_name(self) -> str:
        """Get website display name"""
        return self.config['website'].get('name', self.get_website_url())
    
    def get_max_pages(self) -> int:
        """Get maximum pages to crawl"""
        return self.config['website']['max_pages']
    
    def is_sitemap_validation_enabled(self) -> bool:
        """Check if sitemap validation is enabled"""
        return self.config['website'].get('enable_sitemap_validation', True)