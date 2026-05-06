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
        raw_violations = scan_results.get("violations", [])
        
        if not raw_violations:
            return []

        # Use Violation objects directly from scan results
        violations = raw_violations

        # 2. AI Refinement (Optional but powerful)
        refined_violations = []
        for v in violations[:10]: # Limit to 10 for performance in demo
            try:
                ai_refined = await self.refine_violation(v)
                refined_violations.append(ai_refined)
            except Exception as e:
                logger.error(f"Failed to refine violation {v.id}: {str(e)}")
                # Fallback to the unrefined violation so we don't lose data
                refined_violations.append(v)
            
        return refined_violations

    async def refine_violation(self, violation: Violation) -> Violation:
        prompt = f"""
        Refine the following accessibility violation into a professional audit report entry.
        
        STRICT OUTPUT RULES:
        1. Return ONLY a single raw JSON object.
        2. DO NOT use markdown code blocks (e.g., NO ```json).
        3. DO NOT include any conversational text before or after the JSON.
        4. Ensure all double quotes inside JSON values are escaped with a backslash (\").
        5. Use standard JSON double quotes (") for all string delimiters.
        
        INPUT DATA:
        Violation ID: {violation.id}
        Description: {violation.description}
        Help Text: {violation.help}
        
        EXPECTED JSON STRUCTURE:
        {{
            "friendly_name": "Title",
            "wcag_criteria": "Criterion",
            "wcag_level": "Level",
            "severity": "Severity",
            "business_impact": "Impact",
            "expected_result": "Expected",
            "actual_result": "Actual",
            "steps_to_reproduce": "Steps",
            "remediation_plan": "Fix"
        }}

        GOOD OUTPUT EXAMPLE:
        {{
            "friendly_name": "Images must have alternate text",
            "wcag_criteria": "1.1.1 Non-text Content",
            "wcag_level": "A",
            "severity": "Critical",
            "business_impact": "Users with visual impairments cannot understand the content of the image.",
            "expected_result": "All images should have a descriptive alt attribute.",
            "actual_result": "The main logo image is missing an alt attribute.",
            "steps_to_reproduce": "1. Open the page. 2. Inspect the logo image.",
            "remediation_plan": "Add alt='Company Logo' to the img tag."
        }}
        """
        try:
            ai_response = await self.call_llm(prompt, system_message=self.system_prompt)
            data = self.parse_json(ai_response)
            
            if "error" in data:
                logger.warning(f"JSON Parse error for {violation.id}, using fallback.")
                return violation
        except Exception as e:
            logger.error(f"LLM Call failed for {violation.id}: {str(e)}")
            return violation
        
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
