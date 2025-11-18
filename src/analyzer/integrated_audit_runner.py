# src/analyzer/integrated_audit_runner.py
import asyncio
import time
from typing import List, Dict, Any
from ..utils.logger import setup_logger
from .audit_runner import AuditRunner
from .extended_audits.extended_audit_runner import ExtendedAuditRunner
from .working_axe_analyzer import WorkingAxeAnalyzer
from .models.audit_models import PageAuditResult
from .models.extended_audit_models import ExtendedAuditResult

class IntegratedAuditRunner:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.axe_runner = WorkingAxeAnalyzer(config)
        self.extended_runner = ExtendedAuditRunner(config)
    
    async def run_comprehensive_audit(self, urls: List[str]) -> Dict[str, Any]:
        """Run both axe-core and extended audits"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting comprehensive audit for {len(urls)} URLs")
            
            # Run axe-core audits
            axe_results = await self.axe_runner.analyze_multiple_pages(urls)
            axe_report = self.axe_runner.generate_audit_report(axe_results)
            
            # Run extended audits for each URL
            extended_results = []
            for url in urls:
                try:
                    extended_result = await self.extended_runner.run_extended_audit(url)
                    extended_results.append(extended_result)
                except Exception as e:
                    self.logger.error(f"Extended audit failed for {url}: {e}")
                    extended_results.append(ExtendedAuditResult(
                        url=url,
                        timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                        keyboard_defects=[],
                        screen_reader_defects=[],
                        landmark_defects=[],
                        skip_link_defects=[],
                        error=str(e)
                    ))
            
            # Combine results
            combined_report = self._combine_reports(axe_report, extended_results)
            
            # Add duration
            audit_duration = round(time.time() - start_time, 2)
            combined_report['summary']['audit_duration'] = audit_duration
            
            self._log_comprehensive_summary(combined_report)
            
            return combined_report
            
        except Exception as e:
            self.logger.error(f"Comprehensive audit failed: {e}")
            raise
        finally:
            self.axe_runner.shutdown()
    
    def _combine_reports(self, axe_report: Dict[str, Any], extended_results: List[ExtendedAuditResult]) -> Dict[str, Any]:
        """Combine axe-core and extended audit results"""
        combined_report = axe_report.copy()
        
        # Add extended results to page results
        for i, page_result in enumerate(combined_report['page_results']):
            url = page_result['url']
            extended_result = next((er for er in extended_results if er.url == url), None)
            
            if extended_result:
                page_result['extended_audit'] = {
                    'total_defects': extended_result.total_defects,
                    'defects_by_category': {
                        'keyboard': len(extended_result.keyboard_defects),
                        'screen_reader': len(extended_result.screen_reader_defects),
                        'landmark': len(extended_result.landmark_defects),
                        'skip_links': len(extended_result.skip_link_defects)
                    },
                    'defects_by_severity': {
                        severity.value: count 
                        for severity, count in extended_result.defects_by_severity.items()
                    },
                    'keyboard_defects': [
                        {
                            'element_type': defect.element_type,
                            'element_description': defect.element_description,
                            'issue': defect.issue,
                            'severity': defect.severity.value,
                            'recommendation': defect.recommendation,
                            'selector': defect.selector
                        } for defect in extended_result.keyboard_defects
                    ],
                    'screen_reader_defects': [
                        {
                            'element_type': defect.element_type,
                            'element_description': defect.element_description,
                            'issue': defect.issue,
                            'severity': defect.severity.value,
                            'recommendation': defect.recommendation,
                            'selector': defect.selector
                        } for defect in extended_result.screen_reader_defects
                    ],
                    'landmark_defects': [
                        {
                            'landmark_type': defect.landmark_type.value,
                            'element_description': defect.element_description,
                            'issue': defect.issue,
                            'severity': defect.severity.value,
                            'recommendation': defect.recommendation,
                            'selector': defect.selector
                        } for defect in extended_result.landmark_defects
                    ],
                    'skip_link_defects': [
                        {
                            'issue': defect.issue,
                            'severity': defect.severity.value,
                            'recommendation': defect.recommendation,
                            'target_id': defect.target_id
                        } for defect in extended_result.skip_link_defects
                    ]
                }
        
        # Update summary with extended defects
        if extended_results:
            successful_extended = [er for er in extended_results if not er.error]
            if successful_extended:
                combined_report['summary']['total_extended_defects'] = sum(
                    er.total_defects for er in successful_extended
                )
                combined_report['summary']['extended_defects_by_category'] = {
                    'keyboard': sum(len(er.keyboard_defects) for er in successful_extended),
                    'screen_reader': sum(len(er.screen_reader_defects) for er in successful_extended),
                    'landmark': sum(len(er.landmark_defects) for er in successful_extended),
                    'skip_links': sum(len(er.skip_link_defects) for er in successful_extended)
                }
                
                # Calculate defects by severity across all extended audits
                severity_counts = {}
                for er in successful_extended:
                    for severity, count in er.defects_by_severity.items():
                        severity_counts[severity.value] = severity_counts.get(severity.value, 0) + count
                combined_report['summary']['extended_defects_by_severity'] = severity_counts
        
        combined_report['metadata']['audit_type'] = 'comprehensive'
        
        return combined_report

    def _log_comprehensive_summary(self, report: Dict[str, Any]):
        """Log comprehensive audit summary"""
        summary = report['summary']
        
        self.logger.info("=" * 70)
        self.logger.info("COMPREHENSIVE ACCESSIBILITY AUDIT SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total URLs: {summary['total_pages']}")
        self.logger.info(f"Successfully analyzed: {summary['pages_audited']}")
        self.logger.info(f"Axe-Core Score: {summary['average_score']:.1f}%")
        
        # Extended defects summary
        total_extended_defects = summary.get('total_extended_defects', 0)
        self.logger.info(f"Extended Audit Defects: {total_extended_defects}")
        
        if total_extended_defects > 0:
            # Log defects by category
            defects_by_category = summary.get('extended_defects_by_category', {})
            if defects_by_category:
                self.logger.info("Extended Defects by Category:")
                for category, count in defects_by_category.items():
                    if count > 0:
                        self.logger.info(f"  - {category.replace('_', ' ').title()}: {count}")
            
            # Log defects by severity
            defects_by_severity = summary.get('extended_defects_by_severity', {})
            if defects_by_severity:
                self.logger.info("Extended Defects by Severity:")
                for severity, count in defects_by_severity.items():
                    if count > 0:
                        self.logger.info(f"  - {severity.upper()}: {count}")
        
        # Axe-core violations summary
        total_violations = summary.get('total_violations', 0)
        self.logger.info(f"Axe-Core Violations: {total_violations}")
        
        if total_violations > 0:
            violations_by_level = summary.get('violations_by_level', {})
            if violations_by_level:
                self.logger.info("Axe Violations by Level:")
                for level, count in violations_by_level.items():
                    if count > 0:
                        self.logger.info(f"  - {level.upper()}: {count}")
        
        self.logger.info(f"Audit Duration: {summary['audit_duration']}s")
        self.logger.info("=" * 70)