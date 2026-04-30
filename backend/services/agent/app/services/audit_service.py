from app.utils.browser import browser_manager
from common.schemas.audit import AuditRequest, AuditResult, Violation
import json
import os

class AuditService:
    def __init__(self):
        # Path to axe.min.js - in a real app, this would be bundled or downloaded
        self.axe_script_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js"

    async def run_audit(self, request: AuditRequest) -> AuditResult:
        async with browser_manager.get_page() as page:
            # 1. Navigate
            await page.goto(str(request.url), wait_until="networkidle")
            
            # 2. Inject Axe-core
            await page.add_script_tag(url=self.axe_script_url)
            
            # 3. Run Audit
            results = await page.evaluate("async () => { return await axe.run(); }")
            
            # 4. Parse Results
            violations = []
            for v in results.get("violations", []):
                violations.append(Violation(
                    id=v["id"],
                    impact=v.get("impact"),
                    description=v["description"],
                    help=v["help"],
                    helpUrl=v["helpUrl"],
                    nodes=v["nodes"]
                ))
            
            return AuditResult(
                url=request.url,
                violations=violations,
                metadata={
                    "testEngine": results["testEngine"],
                    "testRunner": results["testRunner"],
                    "testEnvironment": results["testEnvironment"]
                }
            )

audit_service = AuditService()
