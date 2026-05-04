from common.config import setup_environment
setup_environment()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from common.schemas.audit import AuditResult
from app.services.report_service import report_service
import os

app = FastAPI(title="A11ySense AI Reporting Service")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.post("/generate")
async def generate_report(result: AuditResult):
    """
    Industry-standard Allure report generation.
    """
    return await report_service.create_audit_report(result)
