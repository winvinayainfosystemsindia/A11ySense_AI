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

        # Convert to Violation objects early
        violations = [Violation(**v) for v in raw_violations]

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
        
        CRITICAL RULES:
        1. Return ONLY a valid JSON object.
        2. Do NOT include markdown code blocks (like ```json).
        3. Escape all double quotes within strings.
        4. If you include HTML snippets, use backticks (`) instead of quotes.
        
        INPUT DATA:
        Violation ID: {violation.id}
        Description: {violation.description}
        Help Text: {violation.help}
        
        JSON SCHEMA:
        {{
            "friendly_name": "Professional title (e.g. Missing Alt Text on Logo)",
            "wcag_criteria": "The Success Criterion number",
            "wcag_level": "A, AA, or AAA",
            "severity": "Critical, High, Medium, or Low",
            "business_impact": "How this affects users with specific disabilities (e.g. screen reader users)",
            "expected_result": "Standard compliant behavior",
            "actual_result": "Description of the current failure",
            "steps_to_reproduce": "Numbered list of steps",
            "remediation_plan": "Recommended fix with code example if applicable"
        }}
        """
        try:
            ai_response = await self.call_llm(prompt, system_message=self.system_prompt)
            data = self.parse_json(ai_response)
            
            # If parse_json returned an error dict, use fallback
            if "error" in data:
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
