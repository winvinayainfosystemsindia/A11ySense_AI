from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ViolationLevel(Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"

class WCAGVersion(Enum):
    WCAG2A = "wcag2a"
    WCAG2AA = "wcag2aa"
    WCAG21A = "wcag21a"
    WCAG21AA = "wcag21aa"

@dataclass
class Violation:
    id: str
    impact: str
    description: str
    help: str
    help_url: str
    tags: List[str]
    nodes: List[Dict[str, Any]]
    level: ViolationLevel = None
    wcag_version: Optional[WCAGVersion] = None
    
    def __post_init__(self):
        # Auto-calculate level based on impact
        impact_levels = {
            'critical': ViolationLevel.CRITICAL,
            'serious': ViolationLevel.SERIOUS,
            'moderate': ViolationLevel.MODERATE,
            'minor': ViolationLevel.MINOR
        }
        self.level = impact_levels.get(self.impact.lower(), ViolationLevel.MINOR)
        
        # Extract WCAG version from tags
        for tag in self.tags:
            if tag in [v.value for v in WCAGVersion]:
                self.wcag_version = WCAGVersion(tag)
                break

@dataclass
class PageAuditResult:
    url: str
    timestamp: str
    violations: List[Violation]
    passes: List[Dict[str, Any]]
    incomplete: List[Dict[str, Any]]
    inapplicable: List[Dict[str, Any]]
    score: float = 0.0
    error: Optional[str] = None
    load_time: float = 0.0
    
    def __post_init__(self):
        self.calculate_score()
    
    def calculate_score(self):
        """Calculate accessibility score (0-100)"""
        total_violations = len(self.violations)
        total_elements = total_violations + len(self.passes)
        
        if total_elements == 0:
            self.score = 100.0
        else:
            self.score = max(0, (len(self.passes) / total_elements) * 100)

@dataclass
class AuditSummary:
    total_pages: int
    pages_audited: int
    total_violations: int
    violations_by_level: Dict[ViolationLevel, int]
    violations_by_rule: Dict[str, int]
    average_score: float
    worst_score: float
    best_score: float
    pages_with_errors: List[str]
    audit_duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_pages': self.total_pages,
            'pages_audited': self.pages_audited,
            'total_violations': self.total_violations,
            'violations_by_level': {level.value: count for level, count in self.violations_by_level.items()},
            'violations_by_rule': self.violations_by_rule,
            'average_score': round(self.average_score, 2),
            'worst_score': round(self.worst_score, 2),
            'best_score': round(self.best_score, 2),
            'pages_with_errors': self.pages_with_errors,
            'audit_duration': round(self.audit_duration, 2)
        }