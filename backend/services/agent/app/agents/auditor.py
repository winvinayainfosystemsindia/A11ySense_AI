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
            "business_impact": data.get("business_impact", "Significant impact on assistive technology users."),
            "remediation": data.get("remediation_plan", "Update the element to meet WCAG standards."),
            "wcag_mapping": data.get("wcag_mapping", "N/A"),
            "refined_by": "AuditorAgent"
        }
        return violation
