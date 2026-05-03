from app.services.allure_manager import AllureManager
from common.schemas.audit import AuditResult
import os

class ReportService:
    def __init__(self):
        results_dir = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")
        self.allure_manager = AllureManager(results_dir)

    async def create_audit_report(self, result: AuditResult):
        """
        Coordinates the transformation of an AuditResult into a professional Allure report.
        """
        task_id = self.allure_manager.generate_allure_json(result)
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Industry-standard Allure report generated successfully."
        }

report_service = ReportService()
