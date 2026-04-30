from fastapi import FastAPI
from common.schemas.audit import AuditResult
import os
import json
import uuid

app = FastAPI(title="Reporting Service")

ALLURE_RESULTS_DIR = "/app/storage/reports/allure-results"

@app.post("/generate")
async def generate_report(result: AuditResult):
    report_id = str(uuid.uuid4())
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    
    # Create an Allure result file
    # This is a simplified version; real Allure results are more complex
    result_filename = f"{report_id}-result.json"
    filepath = os.path.join(ALLURE_RESULTS_DIR, result_filename)
    
    # Transform AuditResult to Allure format
    allure_data = {
        "uuid": report_id,
        "historyId": str(uuid.uuid4()),
        "name": f"Accessibility Audit for {result.url}",
        "status": "passed" if not result.violations else "failed",
        "start": int(result.timestamp.timestamp() * 1000),
        "stop": int(result.timestamp.timestamp() * 1000) + 1000,
        "steps": [
            {
                "name": f"Violation: {v.id}",
                "status": "broken",
                "statusDetails": {"message": v.description, "trace": v.help}
            } for v in result.violations
        ]
    }
    
    with open(filepath, "w") as f:
        json.dump(allure_data, f)
    
    return {"status": "success", "report_url": f"/reports/{report_id}"}
