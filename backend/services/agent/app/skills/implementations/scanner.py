from playwright.async_api import Page
from common.schemas.audit import Violation
import logging
import json

logger = logging.getLogger(__name__)

class ScannerSkill:
    """
    Skill for performing automated accessibility scans using axe-core.
    """
    
    def __init__(self):
        self.axe_script_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js"

    async def run_axe(self, page: Page):
        logger.info("Running Axe-core scan")
        # Inject Axe
        await page.add_script_tag(url=self.axe_script_url)
        
        # Run Audit
        results = await page.evaluate("async () => { return await axe.run(); }")
        
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
            
        return {
            "violations": violations,
            "summary": {
                "total": len(violations),
                "engine": results.get("testEngine", {}).get("name", "axe-core")
            }
        }

scanner_skill = ScannerSkill()
