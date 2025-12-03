# main.py
import asyncio
from typing import List, Dict, Any
from src.crawler.playwright_crawler import PlaywrightCrawler
from src.analyzer.audit_runner import AuditRunner
from src.analyzer.result_processor import ResultProcessor
from src.utils.logger import setup_logger
from src.utils.config_manager import ConfigManager
from src.utils.report_utils import create_empty_report, create_error_report
from src.utils.ui_utils import print_banner

class AccessibilityAuditTool:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.logger = setup_logger(__name__, self.config['logging']['level'])
        self.crawler = None
        self.audit_runner = None
        self.result_processor = None
    
    async def run_crawl(self) -> list:
        website_url = self.config['website']['url']
        
        try:
            self.crawler = PlaywrightCrawler(self.config)
            crawl_result = await self.crawler.crawl(website_url)

            if isinstance(crawl_result, dict) and 'urls' in crawl_result:
                return crawl_result['urls']
            elif isinstance(crawl_result, list):
                return crawl_result
            return []
        
        except Exception as e:
            self.logger.error(f"Crawling failed: {e}")
            raise
        finally:
            if self.crawler:
                await self.crawler.close()

    async def run_accessibility_audit(self, urls: List[str]) -> Dict[str, Any]:
        if not urls:
            return create_empty_report()
        
        try:
            self.audit_runner = AuditRunner(self.config)
            self.result_processor = ResultProcessor(self.config)
            
            audit_report = await self.audit_runner.run_audit(urls)
            report_paths = self.result_processor.save_audit_results(audit_report)
            
            return {
                'report': audit_report,
                'output_paths': report_paths
            }
        
        except Exception as e:
            self.logger.error(f"Accessibility audit failed: {e}")
            return create_error_report(urls, str(e))
    
    async def run_comprehensive_audit(self, urls: List[str]) -> Dict[str, Any]:
        if not urls:
            return create_empty_report()
        
        try:
            from src.analyzer.integrated_audit_runner import IntegratedAuditRunner
            self.result_processor = ResultProcessor(self.config)
            
            integrated_runner = IntegratedAuditRunner(self.config)
            comprehensive_results = await integrated_runner.run_comprehensive_audit(urls)
            
            report_paths = self.result_processor.save_comprehensive_results(comprehensive_results)
            
            return {
                'report': comprehensive_results,
                'output_paths': report_paths
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive audit failed: {e}")
            return await self.run_accessibility_audit(urls)
    
    async def run_full_audit(self, audit_type: str = "comprehensive"):
        urls = await self.run_crawl()
        
        if audit_type == "comprehensive":
            audit_results = await self.run_comprehensive_audit(urls)
        else:
            audit_results = await self.run_accessibility_audit(urls)
            
        return

async def main():
    print_banner()
    try:
        tool = AccessibilityAuditTool()
        
        choice = input("Enter audit type (1 for basic, 2 for comprehensive, default=2): ").strip()
        audit_type = "basic" if choice == "1" else "comprehensive"
        
        results = await tool.run_full_audit(audit_type)
        
        # No print statements — returning results instead
        return results
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
