# src/analyzer/result_processor.py
import json
import time
from typing import List, Dict, Any
from pathlib import Path
from ..utils.logger import setup_logger
from ..reporting.report_writer import ReportWriter
from .models.audit_models import PageAuditResult, AuditSummary

class ResultProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
        self.report_writer = ReportWriter()
    
    def save_audit_results(self, audit_report: Dict[str, Any], output_path: str = None):
        """Save audit results to JSON and Excel formats"""
        try:
            # Generate comprehensive reports
            report_paths = self.report_writer.save_comprehensive_audit_report(
                audit_report, 
                "accessibility_audit"
            )
            
            self.logger.info(f"Audit results saved:")
            self.logger.info(f"  JSON: {report_paths['json']}")
            self.logger.info(f"  Excel: {report_paths['excel']}")
            
            return report_paths
            
        except Exception as e:
            self.logger.error(f"Failed to save audit results: {e}")
            raise
    
    def save_comprehensive_results(self, comprehensive_results: Dict[str, Any]) -> Dict[str, str]:
        """Save comprehensive audit results with extended details"""
        try:
            # Save main report
            report_paths = self.report_writer.save_comprehensive_audit_report(
                comprehensive_results,
                "comprehensive_accessibility_audit"
            )
            
            # Generate detailed Excel report
            excel_path = self.report_writer.generate_audit_excel_report(
                comprehensive_results,
                "detailed_audit_report"
            )
            
            self.logger.info(f"Comprehensive audit results saved:")
            self.logger.info(f"  JSON: {report_paths['json']}")
            self.logger.info(f"  Excel (Basic): {report_paths['excel']}")
            self.logger.info(f"  Excel (Detailed): {excel_path}")
            
            return {
                'json': report_paths['json'],
                'excel_basic': report_paths['excel'],
                'excel_detailed': excel_path
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save comprehensive results: {e}")
            raise
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable formats"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        elif hasattr(obj, '__dict__'):
            # Convert objects to dict
            return self._make_serializable(obj.__dict__)
        else:
            # Convert to string as fallback
            return str(obj)
    
    def generate_console_report(self, audit_report: Dict[str, Any]):
        """Generate console-friendly audit report"""
        summary = audit_report.get('summary', {})
        categorization = audit_report.get('categorization', {})
        
        report_lines = [
            "🚀 ACCESSIBILITY AUDIT REPORT",
            "=" * 50,
            f"Total Pages: {summary.get('total_pages', 0)}",
            f"Pages Audited: {summary.get('pages_audited', 0)}",
            f"Total Violations: {summary.get('total_violations', 0)}",
            f"Average Score: {summary.get('average_score', 0):.1f}%",
            f"Best Score: {summary.get('best_score', 0):.1f}%",
            f"Worst Score: {summary.get('worst_score', 0):.1f}%",
            f"Audit Duration: {summary.get('audit_duration', 0):.1f}s",
            "",
            "📊 VIOLATIONS BY LEVEL:"
        ]
        
        # Add violations by level
        violations_by_level = summary.get('violations_by_level', {})
        for level, count in violations_by_level.items():
            report_lines.append(f"  • {level.upper()}: {count}")
        
        # Add extended defects if available
        if 'total_extended_defects' in summary:
            report_lines.append(f"\n🔴 EXTENDED AUDIT DEFECTS: {summary['total_extended_defects']}")
            defects_by_category = summary.get('extended_defects_by_category', {})
            for category, count in defects_by_category.items():
                if count > 0:
                    report_lines.append(f"  • {category.replace('_', ' ').title()}: {count}")
        
        # Add top violating rules
        report_lines.append("\n🔴 TOP VIOLATING RULES:")
        violations_by_rule = summary.get('violations_by_rule', {})
        sorted_rules = sorted(
            violations_by_rule.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for rule_id, count in sorted_rules:
            report_lines.append(f"  • {rule_id}: {count} violations")
        
        # Add pages with errors if any
        pages_with_errors = summary.get('pages_with_errors', [])
        if pages_with_errors:
            report_lines.append(f"\n❌ PAGES WITH ERRORS ({len(pages_with_errors)}):")
            for url in pages_with_errors[:3]:
                report_lines.append(f"  • {url}")
            if len(pages_with_errors) > 3:
                report_lines.append(f"  • ... and {len(pages_with_errors) - 3} more")
        
        return "\n".join(report_lines)