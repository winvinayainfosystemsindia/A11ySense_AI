import json
import time
from typing import List, Dict, Any
from pathlib import Path
from ..utils.logger import setup_logger
from .models.audit_models import PageAuditResult, AuditSummary

class ResultProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger(__name__)
    
    def save_audit_results(self, audit_report: Dict[str, Any], output_path: str):
        """Save audit results to JSON file"""
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Make sure the report is JSON serializable
            serializable_report = self._make_serializable(audit_report)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Audit results saved to: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save audit results: {e}")
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