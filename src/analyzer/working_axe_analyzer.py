#src\analyzer\working_axe_analyzer.py
import time
import asyncio
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from axe_selenium_python import Axe
from bs4 import BeautifulSoup
from ..core.exceptions import AnalysisException
from ..utils.logger import setup_logger
from .models.audit_models import PageAuditResult, Violation
from .violation_categorizer import ViolationCategorizer

class WorkingAxeAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.categorizer = ViolationCategorizer()
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        self._shutdown_registered = False
    
    def _run_selenium_axe_analysis(self, url: str) -> PageAuditResult:
        """Run axe analysis using Selenium (PROVEN WORKING APPROACH)"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting Selenium axe analysis for: {url}")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Initialize driver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            try:
                # Navigate to URL
                self.logger.info(f"Navigating to: {url}")
                driver.get(url)
                
                # Wait for page to load
                driver.implicitly_wait(10)
                time.sleep(3)  # Additional wait for stability
                
                # Initialize and run axe
                self.logger.info("Running axe-core analysis...")
                axe = Axe(driver)
                axe.inject()  # Inject axe-core into the page
                results = axe.run()  # Run analysis
                
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
                    f"Selenium analysis completed for {url}: "
                    f"{len(violations)} violations, "
                    f"score: {audit_result.score:.1f}"
                )
                
                return audit_result
                
            except Exception as e:
                self.logger.error(f"Selenium analysis failed for {url}: {e}")
                return PageAuditResult(
                    url=url,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    violations=[],
                    passes=[],
                    incomplete=[],
                    inapplicable=[],
                    error=str(e),
                    load_time=time.time() - start_time
                )
            finally:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error quitting driver: {e}")
                
        except Exception as e:
            self.logger.error(f"Browser initialization failed for {url}: {e}")
            return PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=[],
                passes=[],
                incomplete=[],
                inapplicable=[],
                error=str(e),
                load_time=time.time() - start_time
            )
    
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
        """Analyze a single page using Selenium in thread pool"""
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(self.thread_pool, self._run_selenium_axe_analysis, url),
                timeout=120  # 2 minute timeout
            )
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Analysis timed out for {url}")
            return PageAuditResult(
                url=url,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                violations=[],
                passes=[],
                incomplete=[],
                inapplicable=[],
                error="Analysis timed out (120 seconds)",
                load_time=0
            )
    
    async def analyze_multiple_pages(self, urls: List[str]) -> List[PageAuditResult]:
        """Analyze multiple pages - FIXED to ensure all complete before returning"""
        self.logger.info(f"Starting Selenium analysis for {len(urls)} pages")
        
        # Create all tasks
        tasks = [self.analyze_page(url) for url in urls]
        
        # Wait for ALL tasks to complete (even if some fail)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results after ALL are complete
        processed_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Analysis task failed for {urls[i]}: {result}")
                failed_count += 1
                # Create a failed result for the URL
                processed_results.append(PageAuditResult(
                    url=urls[i],
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    violations=[],
                    passes=[],
                    incomplete=[],
                    inapplicable=[],
                    error=str(result),
                    load_time=0
                ))
            else:
                processed_results.append(result)
        
        self.logger.info(f"Completed Selenium analysis for {len(processed_results)} pages "
                        f"({failed_count} failed, {len(processed_results) - failed_count} successful)")
        
        # Verify we have results for all URLs
        if len(processed_results) != len(urls):
            self.logger.warning(f"Result count mismatch: expected {len(urls)}, got {len(processed_results)}")
            # Add missing URLs as failed results
            processed_urls = {r.url for r in processed_results if hasattr(r, 'url')}
            for url in urls:
                if url not in processed_urls:
                    self.logger.error(f"Missing result for URL: {url}")
                    processed_results.append(PageAuditResult(
                        url=url,
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                        violations=[],
                        passes=[],
                        incomplete=[],
                        inapplicable=[],
                        error="Analysis result missing - possible race condition",
                        load_time=0
                    ))
        
        return processed_results
    
    def generate_audit_report(self, audit_results: List[PageAuditResult]) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        # Filter out failed analyses
        successful_results = [r for r in audit_results if not r.error]
        failed_results = [r for r in audit_results if r.error]
        
        # Generate summary using the categorizer
        summary = self.categorizer.generate_summary(audit_results)
        
        # Get detailed categorization from successful results
        all_violations = []
        for result in successful_results:
            all_violations.extend(result.violations)
        
        categorization = self.categorizer.categorize_violations(all_violations)
        
        # Build the report
        report = {
            'summary': summary.to_dict() if hasattr(summary, 'to_dict') else {
                'total_pages': len(audit_results),
                'pages_audited': len(successful_results),
                'total_violations': sum(len(r.violations) for r in successful_results),
                'violations_by_level': {},
                'violations_by_rule': {},
                'average_score': sum(r.score for r in successful_results) / len(successful_results) if successful_results else 0,
                'worst_score': min(r.score for r in successful_results) if successful_results else 0,
                'best_score': max(r.score for r in successful_results) if successful_results else 100,
                'pages_with_errors': [r.url for r in failed_results],
                'audit_duration': 0  # Will be set by audit runner
            },
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
                'axe_rules_used': self.config['axe']['rules']['tags'],
                'total_pages_analyzed': len(audit_results),
                'successful_analyses': len(successful_results),
                'failed_analyses': len(failed_results)
            }
        }
        
        return report
    
    def shutdown(self):
        """Properly shutdown the thread pool"""
        if hasattr(self, 'thread_pool') and self.thread_pool:
            self.thread_pool.shutdown(wait=False)
            self._shutdown_registered = True
    
    def __del__(self):
        """Clean up thread pool - FIXED VERSION"""
        if hasattr(self, 'thread_pool') and self.thread_pool and not self._shutdown_registered:
            try:
                # Don't wait for threads to complete during destruction
                self.thread_pool.shutdown(wait=False)
            except Exception as e:
                # Ignore errors during destruction
                pass