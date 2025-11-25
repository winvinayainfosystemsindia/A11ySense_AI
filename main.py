# main.py
import yaml
import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any
from src.crawler.playwright_crawler import PlaywrightCrawler
from src.analyzer.audit_runner import AuditRunner
from src.analyzer.integrated_audit_runner import IntegratedAuditRunner
from src.analyzer.result_processor import ResultProcessor
from src.utils.logger import setup_logger

class AccessibilityAuditTool:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.config = self._replace_env_variables(self.config)
        self.logger = setup_logger(__name__, self.config['logging']['level'])
        self.crawler = None
        self.audit_runner = None
        self.result_processor = None
        
        # Validate configuration
        self._validate_config()
    
    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Failed to load config from {config_path}: {e}")
    
    def _replace_env_variables(self, config: dict) -> dict:
        load_dotenv()
        
        def replace_recursive(obj):
            if isinstance(obj, dict):
                return {k: replace_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_recursive(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                return os.getenv(obj[2:-1], obj)
            return obj
        
        return replace_recursive(config)
    
    def _validate_config(self):
        website_url = self.config['website']['url']
        
        if not website_url or website_url == "https://example.com":
            raise ValueError("Please update 'website.url' in config.yaml with your target website")
        
        if not website_url.startswith(('http://', 'https://')):
            raise ValueError("Website URL must start with http:// or https://")

    async def run_crawl(self) -> list:
        website_url = self.config['website']['url']
        max_pages = self.config['website']['max_pages']
        
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
        """Run basic accessibility audit using axe-core"""
        if not urls:
            return self._create_empty_report()
        
        try:
            self.audit_runner = AuditRunner(self.config)
            self.result_processor = ResultProcessor(self.config)
            
            audit_report = await self.audit_runner.run_audit(urls)
            
            # Save results using the enhanced report writer
            report_paths = self.result_processor.save_audit_results(audit_report)
            
            return {
                'report': audit_report,
                'output_paths': report_paths
            }
        
        except Exception as e:
            self.logger.error(f"Accessibility audit failed: {e}")
            return self._create_error_report(urls, str(e))
    
    async def run_comprehensive_audit(self, urls: List[str]) -> Dict[str, Any]:
        """Run comprehensive audit including extended tests"""
        if not urls:
            return self._create_empty_report()
        
        try:
            from src.analyzer.integrated_audit_runner import IntegratedAuditRunner
            self.result_processor = ResultProcessor(self.config)
            
            integrated_runner = IntegratedAuditRunner(self.config)
            comprehensive_results = await integrated_runner.run_comprehensive_audit(urls)
            
            # Save comprehensive results
            report_paths = self.result_processor.save_comprehensive_results(comprehensive_results)
            
            return {
                'report': comprehensive_results,
                'output_paths': report_paths
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive audit failed: {e}")
            # Fall back to basic audit
            self.logger.info("Falling back to basic axe-core audit...")
            return await self.run_accessibility_audit(urls)
    
    async def run_full_audit(self, audit_type: str = "comprehensive"):
        """Run full audit with crawling and specified audit type"""
        urls = await self.run_crawl()
        
        if audit_type == "comprehensive":
            audit_results = await self.run_comprehensive_audit(urls)
        else:
            audit_results = await self.run_accessibility_audit(urls)
            
        return {
            'crawled_urls': urls,
            'audit_results': audit_results,
            'audit_type': audit_type
        }
    
    def _create_empty_report(self) -> Dict[str, Any]:
        """Create empty report for no URLs"""
        return {
            'report': {
                'summary': {
                    'total_pages': 0,
                    'pages_audited': 0,
                    'total_violations': 0,
                    'average_score': 0,
                    'audit_duration': 0
                },
                'page_results': [],
                'metadata': {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_pages_analyzed': 0
                }
            },
            'output_paths': {}
        }
    
    def _create_error_report(self, urls: List[str], error: str) -> Dict[str, Any]:
        """Create error report when audit fails"""
        return {
            'report': {
                'summary': {
                    'total_pages': len(urls),
                    'pages_audited': 0,
                    'total_violations': 0,
                    'average_score': 0,
                    'audit_duration': 0,
                    'pages_with_errors': urls
                },
                'page_results': [],
                'metadata': {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_pages_analyzed': len(urls),
                    'error': error
                }
            },
            'output_paths': {}
        }

def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                 Accessibility Audit Tool                     ║
    ║           Phase 1 (Async Crawl) + Phase 2 (Sync Analysis)    ║
    ║                  With Extended Audits                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    print_banner()
    try:
        tool = AccessibilityAuditTool()
        
        # Ask user for audit type
        print("\nSelect audit type:")
        print("1. Basic Audit (axe-core only)")
        print("2. Comprehensive Audit (axe-core + extended tests)")
        
        choice = input("Enter choice (1 or 2, default 2): ").strip()
        
        if choice == "1":
            audit_type = "basic"
            print("🚀 Starting basic accessibility audit...")
        else:
            audit_type = "comprehensive"
            print("🚀 Starting comprehensive accessibility audit...")
        
        results = await tool.run_full_audit(audit_type)
        
        # Print summary
        report = results['audit_results']['report']
        summary = report['summary']
        output_paths = results['audit_results'].get('output_paths', {})
        
        print(f"\n📊 AUDIT COMPLETED:")
        print(f"   URLs Crawled: {len(results['crawled_urls'])}")
        print(f"   Pages Audited: {summary['pages_audited']}")
        
        if audit_type == "comprehensive":
            print(f"   Overall Score: {summary.get('overall_comprehensive_score', summary['average_score']):.1f}%")
            print(f"   - Axe-Core: {summary['average_score']:.1f}%")
            print(f"   Total Violations: {summary['total_violations']}")
            if 'total_extended_defects' in summary:
                print(f"   Extended Defects: {summary['total_extended_defects']}")
                
                # Show extended defects breakdown
                defects_by_category = summary.get('extended_defects_by_category', {})
                if defects_by_category:
                    print(f"   Extended Defects Breakdown:")
                    for category, count in defects_by_category.items():
                        if count > 0:
                            print(f"     - {category.replace('_', ' ').title()}: {count}")
        else:
            print(f"   Overall Score: {summary['average_score']:.1f}%")
            print(f"   Total Violations: {summary['total_violations']}")
        
        print(f"\n💾 REPORTS SAVED:")
        if output_paths.get('json'):
            print(f"   JSON Report: {output_paths['json']}")
        if output_paths.get('excel'):
            print(f"   Excel Report: {output_paths['excel']}")
        if output_paths.get('excel_basic'):
            print(f"   Excel Basic: {output_paths['excel_basic']}")
        if output_paths.get('excel_detailed'):
            print(f"   Excel Detailed: {output_paths['excel_detailed']}")
        
        # Show violations breakdown if any
        violations_by_level = summary.get('violations_by_level', {})
        if violations_by_level and any(count > 0 for count in violations_by_level.values()):
            print(f"\n🔴 VIOLATIONS BREAKDOWN:")
            for level, count in violations_by_level.items():
                if count > 0:
                    print(f"   - {level.upper()}: {count}")
        
        # Show pages with errors if any
        pages_with_errors = summary.get('pages_with_errors', [])
        if pages_with_errors:
            print(f"\n❌ PAGES WITH ERRORS ({len(pages_with_errors)}):")
            for url in pages_with_errors[:3]:  # Show first 3
                print(f"   - {url}")
            if len(pages_with_errors) > 3:
                print(f"   - ... and {len(pages_with_errors) - 3} more")
        
        print(f"\n⏱️  Audit Duration: {summary.get('audit_duration', 0):.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)