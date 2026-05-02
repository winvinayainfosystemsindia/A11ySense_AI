from fastapi import FastAPI
from common.schemas.audit import AuditResult, Violation
import os
import json
import uuid
import time

app = FastAPI(title="Reporting Service")

# Use an environment variable for the results directory, fallback to a local relative path
ALLURE_RESULTS_DIR = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")

def map_severity(impact: str) -> str:
    mapping = {
        "critical": "blocker",
        "serious": "critical",
        "moderate": "normal",
        "minor": "minor"
    }
    return mapping.get(impact, "normal")

@app.post("/generate")
async def generate_report(result: AuditResult):
    task_id = str(uuid.uuid4())
    os.makedirs(ALLURE_RESULTS_DIR, exist_ok=True)
    
    # 1. Prepare Allure Result JSON
    start_time = int(result.timestamp.timestamp() * 1000)
    
    allure_result = {
        "uuid": task_id,
        "historyId": str(uuid.uuid4()),
        "name": f"A11y Audit: {result.url}",
        "status": "failed" if result.violations else "passed",
        "statusDetails": {
            "message": f"Found {len(result.violations)} accessibility violations." if result.violations else "No violations found."
        },
        "stage": "finished",
        "steps": [],
        "attachments": [],
        "parameters": [
            {"name": "Audited URL", "value": str(result.url)},
            {"name": "Scan Depth", "value": str(result.metadata.get("depth", 1))}
        ],
        "labels": [
            {"name": "feature", "value": "Accessibility Audit"},
            {"name": "epic", "value": "Compliance"},
            {"name": "framework", "value": "Axe-core + OpenClaw"},
            {"name": "host", "value": "A11ySense-AI-Agent"}
        ],
        "links": [],
        "start": start_time,
        "stop": start_time + 5000  # Simulated duration
    }

    # 2. Add violations as steps
    for v in result.violations:
        # Map severity label based on highest impact node
        allure_result["labels"].append({
            "name": "severity", 
            "value": map_severity(v.impact)
        })
        
        # Add WCAG Link
        allure_result["links"].append({
            "name": f"WCAG Help: {v.id}",
            "url": str(v.helpUrl),
            "type": "issue"
        })

        # Add Violation Step
        friendly_title = v.metadata.get("friendly_name", f"{v.id} - {v.help}")
        remediation = v.metadata.get("remediation", "No AI suggestion available.")
        impact_desc = v.metadata.get("business_impact", "")
        ai_severity = v.metadata.get("ai_severity", map_severity(v.impact))

        step = {
            "name": f"AI Finding: {friendly_title}",
            "status": "failed",
            "statusDetails": {
                "message": f"USER IMPACT:\n{impact_desc}\n\nREMEDIATION PLAN:\n{remediation}",
                "trace": f"Technical ID: {v.id}\nPriority: {ai_severity}\nNodes Found: {len(v.nodes)}"
            },
            "attachments": [],
            "start": start_time,
            "stop": start_time + 100
        }
        allure_result["steps"].append(step)

    # 3. Save Allure Result File
    result_path = os.path.join(ALLURE_RESULTS_DIR, f"{task_id}-result.json")
    with open(result_path, "w") as f:
        json.dump(allure_result, f, indent=4)

    # 4. Save Raw Audit Data as Attachment
    attachment_id = str(uuid.uuid4())
    attachment_path = os.path.join(ALLURE_RESULTS_DIR, f"{attachment_id}-attachment.json")
    with open(attachment_path, "w") as f:
        json.dump(result.dict(), f, indent=4, default=str)
    
    # Register attachment in result
    allure_result["attachments"].append({
        "name": "Raw Audit Data",
        "source": f"{attachment_id}-attachment.json",
        "type": "application/json"
    })
    
    # Re-save with attachment reference
    with open(result_path, "w") as f:
        json.dump(allure_result, f, indent=4)

    return {"status": "success", "task_id": task_id, "report_path": ALLURE_RESULTS_DIR}
