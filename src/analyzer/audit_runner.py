# src/analyzer/audit_runner.py
import asyncio
import time
from typing import List, Dict, Any
from ..core.exceptions import AnalysisException
from ..utils.logger import setup_logger
from .working_axe_analyzer import WorkingAxeAnalyzer
from .models.audit_models import PageAuditResult

class AuditRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.analyzer = WorkingAxeAnalyzer(config)
    
    async def run_audit(self, urls: List[str]) -> Dict[str, Any]:
        """Run accessibility audit with enhanced error handling"""
        start_time = time.time()
        
        if not urls:
            self.logger.warning("No URLs provided for audit")
            return self._create_empty_report()
        
        try:
            self.logger.info(f"Starting accessibility audit for {len(urls)} URLs")
            
            # Run analysis
            audit_results = await self.analyzer.analyze_multiple_pages(urls)
            
            # Generate report
            report = self.analyzer.generate_audit_report(audit_results)
            
            # Add duration to summary
            audit_duration = round(time.time() - start_time, 2)
            report['summary']['audit_duration'] = audit_duration
            
            # Log comprehensive summary
            self._log_detailed_summary(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Audit failed: {e}")
            return self._create_error_report(urls, str(e))
        finally:
            self.analyzer.shutdown()
    
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
            'output_path': None
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
            'output_path': None
        }
    
    def _log_detailed_summary(self, report: Dict[str, Any]):
        """Log detailed summary of the audit results"""
        summary = report['summary']
        metadata = report['metadata']
        
        self.logger.info("=" * 60)
        self.logger.info("AUDIT SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total URLs: {summary['total_pages']}")
        self.logger.info(f"Successfully analyzed: {summary['pages_audited']}")
        self.logger.info(f"Failed analyses: {len(summary['pages_with_errors'])}")
        self.logger.info(f"Total violations: {summary['total_violations']}")
        self.logger.info(f"Average score: {summary['average_score']:.1f}%")
        self.logger.info(f"Best score: {summary['best_score']:.1f}%")
        self.logger.info(f"Worst score: {summary['worst_score']:.1f}%")
        self.logger.info(f"Audit duration: {summary['audit_duration']}s")
        
        # Log detailed failure reasons if any
        if summary['pages_with_errors']:
            self.logger.info("Failed URLs:")
            for result in report['page_results']:
                if result.get('error'):
                    self.logger.info(f"  - {result['url']}: {result['error']}")
        
        self.logger.info("=" * 60)