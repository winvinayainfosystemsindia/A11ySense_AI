from app.agents.base import BaseAgent
from app.agents.auditor import AuditorAgent
from app.skills.implementations.browser import browser_skill
from app.skills.implementations.scanner import scanner_skill
from common.schemas.audit import AuditRequest, AuditResult
from app.utils.browser import browser_manager
import logging

logger = logging.getLogger(__name__)

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AuditManager", role="Audit Orchestrator")
        self.system_prompt = self.load_prompt("manager.xml")
        self.skills_docs = self.load_skills_docs()
        self.full_system_prompt = f"{self.system_prompt}\n\nAvailable Skills:\n{self.skills_docs}"
        self.auditor = AuditorAgent()

    async def run_audit(self, request: AuditRequest) -> AuditResult:
        """
        Orchestrates the multi-agent audit process.
        """
        logger.info(f"ManagerAgent starting audit for {request.url}")
        
        # 1. Thought Process
        thought_prompt = f"I need to audit {request.url}. What is the plan?"
        thought_response = await self.call_llm(thought_prompt, system_message=self.full_system_prompt)
        logger.info(f"Manager Thought: {thought_response}")

        # 2. Execution
        async with browser_manager.get_page() as page:
            # Navigate
            await browser_skill.navigate(page, str(request.url))
            page_title = await page.title()
            
            # Delegate to Technical Auditor
            violations = await self.auditor.audit_page(page, str(request.url))
            
            # Get other results from scanner (we might need to refactor auditor to return full results)
            scan_data = await scanner_skill.run_axe(page)

        # 3. Final Result
        return AuditResult(
            url=request.url,
            violations=violations,
            passes=scan_data.get("passes", []),
            incomplete=scan_data.get("incomplete", []),
            inapplicable=scan_data.get("inapplicable", []),
            metadata={
                "page_title": page_title,
                "manager_thought": thought_response,
                "summary": scan_data.get("summary", {}),
                "audit_type": "Multi-Agent / OpenClaw",
                "engine": "A11ySense-MAS-v1"
            }
        )
