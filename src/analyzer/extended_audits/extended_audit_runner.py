# src/analyzer/extended_audits/extended_audit_runner.py
import asyncio
import time
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from ...core.exceptions import AnalysisException
from ...utils.logger import setup_logger
from ..models.extended_audit_models import ExtendedAuditResult

# Import the microservices
from .keyboard_audit import KeyboardAudit
from .screen_reader_audit import ScreenReaderAudit
from .landmark_audit import LandmarkAudit
from .skip_link_audit import SkipLinkAudit

class ExtendedAuditRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.driver = None
        self.audit_services = {}
    
    async def run_extended_audit(self, url: str) -> ExtendedAuditResult:
        """Run extended accessibility audits and return defects"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting extended audit for: {url}")
            
            # Setup browser
            await self._setup_browser()
            
            # Navigate to URL
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to stabilize
            self.logger.info("Waiting for page to stabilize...")
            await asyncio.sleep(5)
            
            # Initialize audit services
            self._initialize_audit_services()
            
            # Run all extended audits sequentially to avoid overload
            self.logger.info("Starting keyboard navigation audit...")
            keyboard_defects = await self._run_audit_service("keyboard")
            
            self.logger.info("Starting screen reader audit...")
            screen_reader_defects = await self._run_audit_service("screen_reader")
            
            self.logger.info("Starting landmark audit...")
            landmark_defects = await self._run_audit_service("landmark")
            
            self.logger.info("Starting skip link audit...")
            skip_link_defects = await self._run_audit_service("skip_link")
            
            # Create result object
            result = ExtendedAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                keyboard_defects=keyboard_defects,
                screen_reader_defects=screen_reader_defects,
                landmark_defects=landmark_defects,
                skip_link_defects=skip_link_defects
            )
            
            audit_duration = round(time.time() - start_time, 2)
            
            self.logger.info(
                f"Extended audit completed for {url} in {audit_duration}s: "
                f"Found {result.total_defects} defects "
                f"(Keyboard: {len(keyboard_defects)}, "
                f"Screen Reader: {len(screen_reader_defects)}, "
                f"Landmark: {len(landmark_defects)}, "
                f"Skip Links: {len(skip_link_defects)})"
            )
            
            # Log defects by severity
            severity_counts = result.defects_by_severity
            if severity_counts:
                self.logger.info("Defects by severity:")
                for severity, count in severity_counts.items():
                    if count > 0:
                        self.logger.info(f"  {severity.value.upper()}: {count} defects")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Extended audit failed for {url}: {e}")
            return ExtendedAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                keyboard_defects=[],
                screen_reader_defects=[],
                landmark_defects=[],
                skip_link_defects=[],
                error=str(e)
            )
        finally:
            await self._close_browser()
    
    def _initialize_audit_services(self):
        """Initialize all audit services"""
        self.audit_services = {
            "keyboard": KeyboardAudit(self.driver, self.config),
            "screen_reader": ScreenReaderAudit(self.driver, self.config),
            "landmark": LandmarkAudit(self.driver, self.config),
            "skip_link": SkipLinkAudit(self.driver, self.config)
        }
    
    async def _run_audit_service(self, service_name: str) -> List[Any]:
        """Run a specific audit service with error handling"""
        try:
            service = self.audit_services.get(service_name)
            if service:
                self.logger.debug(f"Running {service_name} audit...")
                return await service.run_audit()
            return []
        except Exception as e:
            self.logger.error(f"Audit service {service_name} failed: {e}")
            return []
    
    async def _setup_browser(self):
        """Setup Chrome browser for extended testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Set timeouts
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(30)
        self.driver.set_script_timeout(30)
        
        self.logger.info("Browser setup completed")
    
    async def _close_browser(self):
        """Close browser instance"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")