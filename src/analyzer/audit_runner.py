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
        """Run accessibility audit with proper completion tracking"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting accessibility audit for {len(urls)} URLs")
            self.logger.info(f"URLs to analyze: {urls}")
            
            # Run analysis and wait for ALL to complete
            self.logger.info("Starting analysis phase...")
            audit_results = await self.analyzer.analyze_multiple_pages(urls)
            
            # Verify we have results for all URLs
            analyzed_urls = {r.url for r in audit_results}
            missing_urls = set(urls) - analyzed_urls
            
            if missing_urls:
                self.logger.warning(f"Missing results for {len(missing_urls)} URLs: {missing_urls}")
                # Add missing URLs as failed results
                for url in missing_urls:
                    audit_results.append(PageAuditResult(
                        url=url,
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                        violations=[],
                        passes=[],
                        incomplete=[],
                        inapplicable=[],
                        error="Analysis never completed - timing issue",
                        load_time=0
                    ))
            
            # Generate report only after ALL results are collected
            self.logger.info("Generating audit report...")
            report = self.analyzer.generate_audit_report(audit_results)
            
            # Add duration to summary
            audit_duration = round(time.time() - start_time, 2)
            report['summary']['audit_duration'] = audit_duration
            
            successful_count = report['metadata']['successful_analyses']
            total_count = report['metadata']['total_pages_analyzed']
            total_violations = report['summary']['total_violations']
            
            self.logger.info(
                f"Audit completed: {successful_count}/{total_count} pages successful, "
                f"{total_violations} violations, duration: {audit_duration}s"
            )
            
            # Log detailed summary
            self._log_detailed_summary(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Audit failed: {e}")
            raise AnalysisException(f"Accessibility audit failed: {e}")
        finally:
            # Ensure proper cleanup
            self.analyzer.shutdown()
    
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
        
        # Log violations by severity
        violations_by_level = summary.get('violations_by_level', {})
        if violations_by_level:
            self.logger.info("Violations by severity:")
            for level, count in violations_by_level.items():
                self.logger.info(f"  - {level.upper()}: {count}")
        
        # Log top violating rules
        violations_by_rule = summary.get('violations_by_rule', {})
        if violations_by_rule:
            top_rules = sorted(violations_by_rule.items(), key=lambda x: x[1], reverse=True)[:5]
            self.logger.info("Top violating rules:")
            for rule_id, count in top_rules:
                self.logger.info(f"  - {rule_id}: {count}")
        
        self.logger.info("=" * 60)