# src/analyzer/models/extended_audit_models.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class NavigationType(Enum):
    TAB = "tab"
    ARROW = "arrow"
    BOTH = "both"
    NONE = "none"

class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class LandmarkType(Enum):
    BANNER = "banner"
    MAIN = "main"
    NAVIGATION = "navigation"
    COMPLEMENTARY = "complementary"
    CONTENTINFO = "contentinfo"
    SEARCH = "search"
    FORM = "form"
    REGION = "region"

@dataclass
class KeyboardDefect:
    element_type: str
    element_description: str
    issue: str
    severity: SeverityLevel
    recommendation: str
    selector: Optional[str] = None

@dataclass
class ScreenReaderDefect:
    element_type: str
    element_description: str
    issue: str
    severity: SeverityLevel
    recommendation: str
    selector: Optional[str] = None

@dataclass
class LandmarkDefect:
    landmark_type: LandmarkType
    element_description: str
    issue: str
    severity: SeverityLevel
    recommendation: str
    selector: Optional[str] = None

@dataclass
class SkipLinkDefect:
    issue: str
    severity: SeverityLevel
    recommendation: str
    target_id: Optional[str] = None

@dataclass
class ExtendedAuditResult:
    url: str
    timestamp: str
    keyboard_defects: List[KeyboardDefect]
    screen_reader_defects: List[ScreenReaderDefect]
    landmark_defects: List[LandmarkDefect]
    skip_link_defects: List[SkipLinkDefect]
    error: Optional[str] = None
    
    @property
    def total_defects(self) -> int:
        return (len(self.keyboard_defects) + 
                len(self.screen_reader_defects) + 
                len(self.landmark_defects) + 
                len(self.skip_link_defects))
    
    @property
    def defects_by_severity(self) -> Dict[SeverityLevel, int]:
        severity_count = {level: 0 for level in SeverityLevel}
        
        for defect_list in [self.keyboard_defects, self.screen_reader_defects, 
                          self.landmark_defects, self.skip_link_defects]:
            for defect in defect_list:
                severity_count[defect.severity] += 1
        
        return severity_count