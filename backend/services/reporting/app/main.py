from fastapi import FastAPI
from common.schemas.audit import AuditResult
from app.services.report_service import report_service
import logging
from common.config import setup_environment

# Initialize environment
setup_environment()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A11ySense Enterprise Reporting Service")

@app.post("/generate")
async def generate_report(result: AuditResult):
    """
    Industry-standard endpoint for generating accessibility audit reports.
    Delegates logic to the ReportService and AllureManager.
    """
    logger.info(f"Generating report for URL: {result.url}")
    return await report_service.create_audit_report(result)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reporting"}
