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
                'output_path': None
            }
        
        try:
            self.audit_runner = AuditRunner(self.config)
            self.result_processor = ResultProcessor(self.config)
            
            audit_report = await self.audit_runner.run_audit(urls)
            
            output_dir = Path("storage/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "accessibility_audit.json"

            self.result_processor.save_audit_results(audit_report, str(output_path))
            
            return {
                'report': audit_report,
                'output_path': str(output_path)
            }
        
        except Exception as e:
            self.logger.error(f"Accessibility audit failed: {e}")
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
                        'error': str(e)
                    }
                },
                'output_path': None
            }
    
    async def run_comprehensive_audit(self, urls: List[str]) -> Dict[str, Any]:
        """Run comprehensive audit including extended tests"""
        if not urls:
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
                'output_path': None
            }
        
        try:
            from src.analyzer.integrated_audit_runner import IntegratedAuditRunner
            self.result_processor = ResultProcessor(self.config)
            
            integrated_runner = IntegratedAuditRunner(self.config)
            comprehensive_results = await integrated_runner.run_comprehensive_audit(urls)
            
            output_dir = Path("storage/reports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "comprehensive_accessibility_audit.json"

            self.result_processor.save_audit_results(comprehensive_results, str(output_path))
            
            return {
                'report': comprehensive_results,
                'output_path': str(output_path)
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
        
        print(f"\n📊 AUDIT COMPLETED:")
        print(f"   URLs Crawled: {len(results['crawled_urls'])}")
        print(f"   Pages Audited: {summary['pages_audited']}")
        
        if audit_type == "comprehensive":
            print(f"   Overall Score: {summary.get('overall_comprehensive_score', summary['average_score']):.1f}%")
            print(f"   - Axe-Core: {summary['average_score']:.1f}%")
            print(f"   - Keyboard: {summary.get('average_keyboard_score', 0):.1f}%")
            print(f"   - Screen Reader: {summary.get('average_screen_reader_score', 0):.1f}%")
            print(f"   - Structure: {summary.get('average_structure_score', 0):.1f}%")
        else:
            print(f"   Overall Score: {summary['average_score']:.1f}%")
        
        print(f"   Total Violations: {summary['total_violations']}")
        print(f"   Report saved to: {results['audit_results']['output_path']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)