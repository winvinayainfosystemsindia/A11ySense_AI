from typing import Dict, List, Any
from .models.audit_models import Violation, ViolationLevel, AuditSummary, PageAuditResult
from ..utils.logger import setup_logger

class ViolationCategorizer:
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.rule_metadata = {
            'color-contrast': {
                'category': 'Visual Design',
                'priority': ViolationLevel.SERIOUS,
                'description': 'Ensure text has sufficient color contrast'
            },
            'image-alt': {
                'category': 'Images',
                'priority': ViolationLevel.CRITICAL,
                'description': 'Images must have alternate text'
            },
            'button-name': {
                'category': 'Forms',
                'priority': ViolationLevel.CRITICAL,
                'description': 'Buttons must have discernible text'
            },
            'link-name': {
                'category': 'Navigation',
                'priority': ViolationLevel.SERIOUS,
                'description': 'Links must have discernible text'
            },
            'html-has-lang': {
                'category': 'Structure',
                'priority': ViolationLevel.SERIOUS,
                'description': 'HTML element must have a lang attribute'
            },
            'label': {
                'category': 'Forms',
                'priority': ViolationLevel.CRITICAL,
                'description': 'Form elements must have labels'
            }
        }
    
    def categorize_violations(self, violations: List[Violation]) -> Dict[str, Any]:
        """Categorize violations by type, level, and WCAG version"""
        categorized = {
            'by_level': {},
            'by_rule': {},
            'by_wcag': {},
            'by_category': {}
        }
        
        # Initialize categories
        for level in ViolationLevel:
            categorized['by_level'][level.value] = 0
        
        for violation in violations:
            # Count by level
            categorized['by_level'][violation.level.value] += 1
            
            # Count by rule ID
            rule_id = violation.id
            categorized['by_rule'][rule_id] = categorized['by_rule'].get(rule_id, 0) + 1
            
            # Count by WCAG version
            if violation.wcag_version:
                wcag_key = violation.wcag_version.value
                categorized['by_wcag'][wcag_key] = categorized['by_wcag'].get(wcag_key, 0) + 1
            
            # Count by category
            category = self.rule_metadata.get(rule_id, {}).get('category', 'Other')
            categorized['by_category'][category] = categorized['by_category'].get(category, 0) + 1
        
        return categorized
    
    def get_rule_metadata(self, rule_id: str) -> Dict[str, Any]:
        """Get metadata for a specific rule"""
        return self.rule_metadata.get(rule_id, {
            'category': 'Other',
            'priority': ViolationLevel.MINOR,
            'description': 'No additional information available'
        })
    
    def generate_summary(self, audit_results: List[PageAuditResult]) -> AuditSummary:
        """Generate comprehensive audit summary - FIXED VERSION"""
        total_pages = len(audit_results)
        successful_results = [r for r in audit_results if not r.error]
        pages_audited = len(successful_results)
        
        total_violations = 0
        violations_by_level = {level: 0 for level in ViolationLevel}
        violations_by_rule = {}
        scores = []
        pages_with_errors = []
        
        for result in audit_results:
            if result.error:
                pages_with_errors.append(result.url)
            else:
                total_violations += len(result.violations)
                scores.append(result.score)
                
                # Count violations by level and rule
                for violation in result.violations:
                    violations_by_level[violation.level] = violations_by_level.get(violation.level, 0) + 1
                    rule_id = violation.id
                    violations_by_rule[rule_id] = violations_by_rule.get(rule_id, 0) + 1
        
        avg_score = sum(scores) / len(scores) if scores else 0
        worst_score = min(scores) if scores else 0
        best_score = max(scores) if scores else 100
        
        return AuditSummary(
            total_pages=total_pages,
            pages_audited=pages_audited,
            total_violations=total_violations,
            violations_by_level=violations_by_level,
            violations_by_rule=violations_by_rule,
            average_score=avg_score,
            worst_score=worst_score,
            best_score=best_score,
            pages_with_errors=pages_with_errors,
            audit_duration=0.0  # Will be set by the runner
        )