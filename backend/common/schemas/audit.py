from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AuditRequest(BaseModel):
    url: HttpUrl
    depth: int = Field(default=1, ge=1, le=5)
    audit_type: str = Field(default="standard", pattern="^(standard|comprehensive)$")

class Violation(BaseModel):
    id: str
    impact: Optional[str]
    description: str
    help: str
    helpUrl: HttpUrl
    nodes: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class AuditResult(BaseModel):
    url: HttpUrl
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    violations: List[Violation]
    passes: Optional[List[Any]] = None
    incomplete: Optional[List[Any]] = None
    inapplicable: Optional[List[Any]] = None
    metadata: Dict[str, Any] = {}

class AuditTask(BaseModel):
    task_id: str
    status: str
    report_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
