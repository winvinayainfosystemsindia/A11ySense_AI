from app.agents.base import BaseAgent
from app.skills.implementations.scanner import scanner_skill
from playwright.async_api import Page
from common.schemas.audit import AuditResult, Violation
import logging
from typing import List

logger = logging.getLogger(__name__)

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TechnicalAuditor", role="Accessibility Technical Auditor")
        self.system_prompt = self.load_prompt("auditor.xml")

    async def audit_page(self, page: Page, url: str) -> List[Violation]:
        """
        Runs an automated scan and then uses AI to refine the findings.
        """
        logger.info(f"AuditorAgent scanning {url}")
        
        # 1. Technical Scan
        scan_results = await scanner_skill.run_axe(page)
        raw_violations = scan_results["violations"]
        
        if not raw_violations:
            return []

        # 2. AI Refinement (Optional but powerful)
        # For simplicity in this first iteration, we refine them one by one or in batches
        refined_violations = []
        for violation in raw_violations[:10]: # Limit to 10 for performance in demo
            ai_refined = await self.refine_violation(violation)
            refined_violations.append(ai_refined)
            
        return refined_violations

    async def refine_violation(self, violation: Violation) -> Violation:
        prompt = f"""
        Refine the following accessibility violation:
        Violation ID: {violation.id}
        Description: {violation.description}
        Help: {violation.help}
        
        Provide:
        1. Business Impact (how it affects users)
        2. Remediation Plan (code fix)
        3. WCAG Mapping
        
        Return JSON.
        """
        ai_response = await self.call_llm(prompt, system_message=self.system_prompt)
        data = self.parse_json(ai_response)
        
        # Merge AI data into metadata
        violation.metadata = {
            "friendly_name": data.get("friendly_name", violation.help),
            "wcag_criteria": data.get("wcag_criteria", "N/A"),
            "wcag_level": data.get("wcag_level", "AA"),
            "severity": data.get("severity", violation.impact or "High"),
            "business_impact": data.get("business_impact", ""),
            "expected_result": data.get("expected_result", ""),
            "actual_result": data.get("actual_result", ""),
            "steps_to_reproduce": data.get("steps_to_reproduce", ""),
            "remediation": data.get("remediation_plan", ""),
            "refined_by": "AuditorAgent"
        }
        return violation
