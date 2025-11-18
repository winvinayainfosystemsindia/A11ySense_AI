# src/analyzer/working_axe_analyzer.py
import time
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from axe_selenium_python import Axe
from ..core.exceptions import AnalysisException
from ..utils.logger import setup_logger
from .models.audit_models import PageAuditResult, Violation
from .violation_categorizer import ViolationCategorizer

class WorkingAxeAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.categorizer = ViolationCategorizer()
        
        # Enhanced configuration with retry settings
        self.max_workers = config.get('analysis', {}).get('max_workers', 3)
        self.timeout_per_page = config.get('analysis', {}).get('timeout_per_page', 90)
        self.max_retries = config.get('analysis', {}).get('max_retries', 2)
        self.retry_delay = config.get('analysis', {}).get('retry_delay', 5)
        
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self._shutdown_registered = False
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        
        # Essential options
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Disable images for faster loading
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        # Timeout settings
        chrome_options.add_argument('--page-load-strategy=eager')  # Don't wait for full page load
        
        # Initialize driver with service
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
        
        # Set timeouts
        driver.set_page_load_timeout(30)  # 30 seconds for page load
        driver.implicitly_wait(10)  # 10 seconds for element finding
        
        return driver
    
    def _run_selenium_axe_analysis(self, url: str, retry_count: int = 0) -> PageAuditResult:
        """Run axe analysis with retry logic"""
        start_time = time.time()
        driver = None
        
        try:
            self.logger.info(f"Starting analysis for: {url} (attempt {retry_count + 1})")
            
            driver = self._setup_driver()
            
            # Navigate to URL with timeout
            self.logger.info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to be interactive
            time.sleep(2)  # Reduced wait time
            
            # Initialize and run axe
            self.logger.info(f"Running axe-core analysis for: {url}")
            axe = Axe(driver)
            axe.inject()
            results = axe.run()
            
            load_time = time.time() - start_time
            
            # Parse results
            violations = self._parse_violations(results.get('violations', []))
            passes = results.get('passes', [])
            incomplete = results.get('incomplete', [])
            inapplicable = results.get('inapplicable', [])
            
            audit_result = PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=violations,
                passes=passes,
                incomplete=incomplete,
                inapplicable=inapplicable,
                load_time=load_time
            )
            
            self.logger.info(
                f"Analysis completed for {url}: "
                f"{len(violations)} violations, "
                f"score: {audit_result.score:.1f}, "
                f"time: {load_time:.2f}s"
            )
            
            return audit_result
            
        except TimeoutException:
            self.logger.warning(f"Page load timeout for {url} (attempt {retry_count + 1})")
            
            # Retry logic
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying {url} after {self.retry_delay}s delay...")
                time.sleep(self.retry_delay + random.uniform(1, 3))  # Add jitter
                return self._run_selenium_axe_analysis(url, retry_count + 1)
            else:
                return PageAuditResult(
                    url=url,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    violations=[],
                    passes=[],
                    incomplete=[],
                    inapplicable=[],
                    error=f"Page load timeout after {self.max_retries + 1} attempts",
                    load_time=time.time() - start_time
                )
                
        except WebDriverException as e:
            self.logger.error(f"WebDriver error for {url}: {e}")
            
            if retry_count < self.max_retries:
                self.logger.info(f"Retrying {url} after WebDriver error...")
                time.sleep(self.retry_delay)
                return self._run_selenium_axe_analysis(url, retry_count + 1)
            else:
                return PageAuditResult(
                    url=url,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    violations=[],
                    passes=[],
                    incomplete=[],
                    inapplicable=[],
                    error=f"WebDriver error: {str(e)}",
                    load_time=time.time() - start_time
                )
                
        except Exception as e:
            self.logger.error(f"Unexpected error analyzing {url}: {e}")
            return PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=[],
                passes=[],
                incomplete=[],
                inapplicable=[],
                error=f"Analysis failed: {str(e)}",
                load_time=time.time() - start_time
            )
            
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error quitting driver: {e}")
    
    def _parse_violations(self, axe_violations: List[Dict[str, Any]]) -> List[Violation]:
        """Convert axe violations to our Violation model"""
        violations = []
        
        for violation in axe_violations:
            try:
                violation_obj = Violation(
                    id=violation.get('id', ''),
                    impact=violation.get('impact', 'minor'),
                    description=violation.get('description', ''),
                    help=violation.get('help', ''),
                    help_url=violation.get('helpUrl', ''),
                    tags=violation.get('tags', []),
                    nodes=violation.get('nodes', [])
                )
                violations.append(violation_obj)
            except Exception as e:
                self.logger.warning(f"Failed to parse violation: {e}")
                continue
        
        return violations
    
    async def analyze_page(self, url: str) -> PageAuditResult:
        """Analyze a single page with timeout protection"""
        loop = asyncio.get_event_loop()
        
        try:
            # Use run_in_executor with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.thread_pool, 
                    self._run_selenium_axe_analysis, 
                    url
                ),
                timeout=self.timeout_per_page
            )
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Analysis timed out for {url} (overall timeout)")
            return PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=[],
                passes=[],
                incomplete=[],
                inapplicable=[],
                error=f"Analysis timed out after {self.timeout_per_page}s",
                load_time=0
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in analyze_page for {url}: {e}")
            return PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=[],
                passes=[],
                incomplete=[],
                inapplicable=[],
                error=f"Analysis failed: {str(e)}",
                load_time=0
            )
    
    async def analyze_multiple_pages(self, urls: List[str]) -> List[PageAuditResult]:
        """Analyze multiple pages with improved concurrency control"""
        self.logger.info(f"Starting analysis for {len(urls)} pages with {self.max_workers} workers")
        
        # Process URLs in batches to avoid overwhelming the system
        batch_size = self.max_workers * 2
        all_results = []
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1} ({len(batch)} URLs)")
            
            # Create tasks for current batch
            tasks = [self.analyze_page(url) for url in batch]
            
            # Wait for all tasks in batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    self.logger.error(f"Analysis task failed for {batch[j]}: {result}")
                    all_results.append(PageAuditResult(
                        url=batch[j],
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                        violations=[],
                        passes=[],
                        incomplete=[],
                        inapplicable=[],
                        error=str(result),
                        load_time=0
                    ))
                else:
                    all_results.append(result)
            
            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < len(urls):
                await asyncio.sleep(1)
        
        # Final statistics
        successful = len([r for r in all_results if not r.error])
        failed = len([r for r in all_results if r.error])
        
        self.logger.info(
            f"Completed analysis for {len(all_results)} pages: "
            f"{successful} successful, {failed} failed"
        )
        
        return all_results
    
    def generate_audit_report(self, audit_results: List[PageAuditResult]) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        successful_results = [r for r in audit_results if not r.error]
        failed_results = [r for r in audit_results if r.error]
        
        summary = self.categorizer.generate_summary(audit_results)
        
        # Get detailed categorization
        all_violations = []
        for result in successful_results:
            all_violations.extend(result.violations)
        
        categorization = self.categorizer.categorize_violations(all_violations)
        
        report = {
            'summary': summary.to_dict(),
            'categorization': categorization,
            'page_results': [
                {
                    'url': result.url,
                    'score': result.score,
                    'violation_count': len(result.violations),
                    'error': result.error,
                    'load_time': round(result.load_time, 2),
                    'violations': [
                        {
                            'id': v.id,
                            'impact': v.impact,
                            'level': v.level.value,
                            'description': v.description,
                            'help': v.help,
                            'help_url': v.help_url,
                            'nodes_count': len(v.nodes)
                        } for v in result.violations
                    ]
                } for result in audit_results
            ],
            'metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_pages_analyzed': len(audit_results),
                'successful_analyses': len(successful_results),
                'failed_analyses': len(failed_results),
                'analysis_config': {
                    'max_workers': self.max_workers,
                    'timeout_per_page': self.timeout_per_page,
                    'max_retries': self.max_retries
                }
            }
        }
        
        return report
    
    def shutdown(self):
        """Properly shutdown the thread pool"""
        if hasattr(self, 'thread_pool') and self.thread_pool:
            self.thread_pool.shutdown(wait=True)
            self._shutdown_registered = True
    
    def __del__(self):
        """Clean up thread pool"""
        if hasattr(self, 'thread_pool') and self.thread_pool and not self._shutdown_registered:
            try:
                self.thread_pool.shutdown(wait=False)
            except Exception:
                pass